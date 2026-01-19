from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("No API Key found")
    exit()

client = genai.Client(api_key=api_key)
print("Listing models...")
try:
    # Attempt to list models directly if supported, or iterate
    # The SDK documentation might vary, let's try standard iteration
    pager = client.models.list()
    for model in pager:
        print(f"Name: {model.name}, Display Name: {model.display_name}")
except Exception as e:
    print(f"Error listing models: {e}")
