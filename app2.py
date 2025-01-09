import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup
import requests
import time
import json

# Load environment variables
load_dotenv()

# Constants
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_HEADERS = {"Content-Type": "application/json"}
OLLAMA_MODEL = "llama3.2:latest"  # Changed from llama2:latest
WEB_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

def check_ollama_availability():
    """Check if Ollama server is available and the model is loaded"""
    try:
        # First check if the server is running
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code != 200:
            return False
            
        # Then test with a simple prompt to ensure the model works
        test_payload = {
            "model": OLLAMA_MODEL,
            "prompt": "hi",
            "stream": False
        }
        
        response = requests.post(OLLAMA_API, json=test_payload, headers=OLLAMA_HEADERS)
        return response.status_code == 200
        
    except requests.exceptions.RequestException:
        return False

def init_session_state():
    """Initialize session state variables"""
    if 'api_key' not in st.session_state:
        st.session_state.api_key = None
    if 'api_source' not in st.session_state:
        st.session_state.api_source = None

class Website:
    def __init__(self, url):
        self.url = url
        try:
            response = requests.get(url, headers=WEB_HEADERS, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            self.title = soup.title.string if soup.title else "No title found"
            
            # Clean up the HTML
            for irrelevant in soup.body(["script", "style", "img", "input"]) if soup.body else []:
                irrelevant.decompose()
            
            self.text = soup.body.get_text(separator="\n", strip=True) if soup.body else ""
        except Exception as e:
            raise Exception(f"Error fetching website: {str(e)}")

def analyze_with_ollama(website: Website) -> str:
    """Analyze website using Ollama"""
    system_prompt = """You are an SEO Expert and Web Development Engineer. Analyze the website content and provide a detailed SEO analysis with these sections:
    1. Overall SEO Score (0-100)
    2. Key Findings
    3. Critical Issues
    4. Recommendations
    5. Technical Details
    6. Mobile-friendly Analysis
    7. Performance Analysis
    8. Additional SEO Factors
    Respond in markdown format."""

    full_prompt = f"{system_prompt}\n\nAnalyzing website: {website.title}\nURL: {website.url}\n\nContent:\n{website.text}"
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_API, json=payload, headers=OLLAMA_HEADERS)
        
        # Add detailed error logging
        st.sidebar.write(f"Status Code: {response.status_code}")
        st.sidebar.write(f"Response Headers: {dict(response.headers)}")
        st.sidebar.write(f"Response Text: {response.text[:500]}...")  # First 500 chars
        
        response.raise_for_status()
        return response.json()['response']
    except Exception as e:
        st.sidebar.error(f"Full error details: {str(e)}")
        raise Exception(f"Ollama analysis failed: {str(e)}")

def analyze_with_openai(website: Website, api_key: str) -> str:
    """Analyze website using OpenAI"""
    client = OpenAI(api_key=api_key)
    
    system_prompt = """You are an SEO Expert and Web Development Engineer. Analyze the website content and provide a detailed SEO analysis with these sections:
    1. Overall SEO Score (0-100)
    2. Key Findings
    3. Critical Issues
    4. Recommendations
    5. Technical Details
    6. Mobile-friendly Analysis
    7. Performance Analysis
    8. Additional SEO Factors
    Respond in markdown format."""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyzing website: {website.title}\nURL: {website.url}\n\nContent:\n{website.text}"}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"OpenAI analysis failed: {str(e)}")

def render_api_selection():
    """Render API selection interface"""
    st.sidebar.title("API Configuration")
    
    # API source selection
    api_source = st.sidebar.radio(
        "Select AI Provider",
        ["OpenAI", "Ollama"],
        help="Choose between OpenAI (requires API key) or Ollama (must be running locally)"
    )
    
    if api_source == "OpenAI":
        env_api_key = os.getenv("OPENAI_API_KEY")
        if env_api_key:
            use_env_key = st.sidebar.checkbox("Use API key from .env file", value=True)
            if use_env_key:
                st.session_state.api_key = env_api_key
            else:
                api_key = st.sidebar.text_input("Enter OpenAI API Key", type="password")
                st.session_state.api_key = api_key
        else:
            api_key = st.sidebar.text_input("Enter OpenAI API Key", type="password")
            st.session_state.api_key = api_key
    else:  # Ollama
        if not check_ollama_availability():
            st.sidebar.error("⚠️ Ollama server not detected. Please ensure Ollama is running locally.")
        else:
            st.sidebar.success("✅ Ollama server detected")
    
    st.session_state.api_source = api_source

def main():
    # Page configuration
    st.set_page_config(
        page_title="Website SEO Analyzer",
        page_icon="🔍",
        layout="wide"
    )

    # Initialize session state
    init_session_state()
    
    # Render API selection sidebar
    render_api_selection()

    # Main content
    st.title("🔍 Website SEO Analyzer")
    st.markdown("### AI-powered SEO analysis using OpenAI or Ollama")
    
    # Input section
    url = st.text_input(
        "Enter website URL",
        placeholder="https://example.com",
        help="Enter the full URL including https:// or http://"
    )
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        analyze_button = st.button("🚀 Analyze Website", use_container_width=True)

    # Analysis section
    if analyze_button and url:
        # Validate API configuration
        if st.session_state.api_source == "OpenAI" and not st.session_state.api_key:
            st.error("❌ Please provide an OpenAI API key")
            return
        elif st.session_state.api_source == "Ollama" and not check_ollama_availability():
            st.error("❌ Ollama server is not available")
            return

        try:
            with st.spinner("🔄 Analyzing website... This may take a minute..."):
                website = Website(url)
                if st.session_state.api_source == "OpenAI":
                    analysis_result = analyze_with_openai(website, st.session_state.api_key)
                else:
                    analysis_result = analyze_with_ollama(website)
                
            st.success("✅ Analysis completed successfully!")
            
            # Display results
            with st.expander("📊 View Detailed Analysis", expanded=True):
                st.markdown(analysis_result)
            
            # Download button
            st.download_button(
                label="📥 Download Analysis Report",
                data=analysis_result,
                file_name=f"seo_analysis_{url.replace('https://', '').replace('http://', '').replace('/', '_')}.md",
                mime="text/markdown"
            )
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("💡 Please check the URL and try again.")
    
    # Footer
    st.markdown("---")
    st.markdown("### How it works")
    st.markdown("""
    1. Select your preferred AI provider (OpenAI or Ollama)
    2. Configure API access
    3. Enter your website URL
    4. Click 'Analyze Website'
    5. Get detailed SEO analysis
    6. Download the report
    """)

if __name__ == "__main__":
    main() 