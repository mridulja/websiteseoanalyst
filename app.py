import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup
import requests
import time

# Load environment variables and setup
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI()

# Page configuration
st.set_page_config(
    page_title="Website SEO Analyzer",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Headers for web requests
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

class Website:
    def __init__(self, url):
        self.url = url
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            self.title = soup.title.string if soup.title else "No title found"
            
            # Clean up the HTML
            for irrelevant in soup.body(["script", "style", "img", "input"]) if soup.body else []:
                irrelevant.decompose()
            
            self.text = soup.body.get_text(separator="\n", strip=True) if soup.body else ""
        except Exception as e:
            raise Exception(f"Error fetching website: {str(e)}")

def analyze_website(url: str) -> str:
    # System prompt for SEO analysis
    system_prompt = """You are an SEO Expert and Web Development Engineer that analyzes the contents of a website 
    and provides a detailed analysis on the status of SEO and how to improve the SEO vitals, ignoring text that might be navigation related. 
    Structure your response in the following sections:
    1. Overall SEO Score (0-100)
    2. Key Findings
    3. Critical Issues
    4. Recommendations
    5. Technical Details
    6. Check if the website is mobile-friendly and if it is, provide a list of the mobile-friendly features that are being tracked.
    7. Check if the website is fast and if it is, provide a list of the fast features that are being tracked.
    8. Check any other factors that might affect the SEO of the website.
    Respond in markdown format."""

    try:
        website = Website(url)
        
        user_prompt = f"""You are analyzing a website titled: {website.title}
        URL: {url}
        
        Please analyze the following content and provide a comprehensive SEO analysis:
        
        {website.text}"""

        response = client.chat.completions.create(
            model="gpt-4",  # Updated to use correct model name
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Analysis failed: {str(e)}")

# Main app interface
def main():
    st.title("🔍 Website SEO Analyzer")
    st.markdown("### Analyze your website's SEO performance with AI-powered insights")
    
    # Input section
    with st.container():
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
        try:
            with st.spinner("🔄 Analyzing website... This may take a minute..."):
                analysis_result = analyze_website(url)
                
            st.success("✅ Analysis completed successfully!")
            
            # Display results in an expander
            with st.expander("📊 View Detailed Analysis", expanded=True):
                st.markdown(analysis_result)
                
            # Add download button for the analysis
            st.download_button(
                label="📥 Download Analysis Report",
                data=analysis_result,
                file_name=f"seo_analysis_{url.replace('https://', '').replace('http://', '').replace('/', '_')}.md",
                mime="text/markdown"
            )
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("💡 Please make sure the URL is correct and the website is accessible.")
    
    # Footer
    st.markdown("---")
    st.markdown("### How it works")
    st.markdown("""
    1. Enter your website URL
    2. Click 'Analyze Website'
    3. Get detailed SEO analysis powered by AI
    4. Download the report for future reference
    """)

if __name__ == "__main__":
    main() 