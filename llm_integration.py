import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_initial_prompt():
    with open("prompt.md", "r") as f:
        return f.read()

def create_session():
    model = genai.GenerativeModel('gemini-2.5-pro')
    chat = model.start_chat(history=[])
    return chat

def send_message(chat, message):
    initial_prompt = get_initial_prompt()
    full_message = initial_prompt + "\n\n" + message
    
    response = chat.send_message(full_message)
    return response.text
