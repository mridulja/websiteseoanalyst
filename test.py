from openai import OpenAI
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup
import requests

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    print("No API key was found - please head over to the troubleshooting notebook in this folder to identify & fix!")
elif not openai_api_key.startswith("sk-proj-"):
    print("An API key was found, but it doesn't start sk-proj-; please check you're using the right key - see troubleshooting notebook")
elif openai_api_key.strip() != openai_api_key:
    print("An API key was found, but it looks like it might have space or tab characters at the start or end - please remove them - see troubleshooting notebook")
else:
    print("API key found and looks good so far!")

client = OpenAI()

message = """Hello, GPT! This is my first ever message to you! Hi!"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": message}],
    temperature=0.5,
    max_tokens=1000,
)

print(response.choices[0].message.content)

# A class to represent a Webpage
# If you're not familiar with Classes, check out the "Intermediate Python" notebook

# Some websites need you to use proper headers when fetching them:
headers = {
 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

class Website:

    def __init__(self, url):
        """
        Create this Website object from the given url using the BeautifulSoup library
        """
        self.url = url
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        self.text = soup.body.get_text(separator="\n", strip=True)

myWebsite = Website("https://fitnessfuelhub.com")

# Define  our system prompt - you can experiment with this later, changing the last sentence to 'Respond in markdown in Spanish."

system_prompt = "You are an SEO Expert and Web Development Engineer that analyzes the contents of a website \
and provides a short summary on the status of SEO and how to improve the SEO vitals, ignoring text that might be navigation related. \
Respond in markdown."

def user_prompt_for(website):
    user_prompt = f"You are looking at a website titled {website.title}"
    user_prompt += "\n The contents of this website is as follows; \
please provide a short summary and vitals related to the SEO of this website in markdown. \
Include practical and relevant recommendations or errors if you find them, and also summarize these too.\n\n"
    user_prompt += website.text
    return user_prompt

user_prompt = user_prompt_for(myWebsite)

# print(user_prompt)

def messages_for(website):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_for(website)}
    ]

def summarize(url):
    website = Website(url)
    response = client.chat.completions.create(
        model = "gpt-4o-mini",
        messages = messages_for(website)
    )
    return response.choices[0].message.content

from IPython.display import Markdown

def display_summary(url):
    summary = summarize(url)
    return Markdown(summary)

summary = summarize(myWebsite.url)
print(summary)