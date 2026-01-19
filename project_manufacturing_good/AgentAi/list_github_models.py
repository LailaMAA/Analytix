from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('DEEPSEEK_API_KEY')

if not api_key:
    print("No API Key found")
    exit()

client = OpenAI(
    api_key=api_key,
    base_url="https://models.inference.ai.azure.com"
)

print("Listing GitHub Models...")
try:
    # Most OpenAI-compatible endpoints support model listing
    models = client.models.list()
    for model in models:
        print(f"ID: {model.id}")
except Exception as e:
    print(f"Error listing models: {e}")
