import os

import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("OPENAI_API_KEY")

if not api_key:
    raise SystemExit("OPENAI_API_KEY not set")

url = "https://api.openai.com/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}
payload = {
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Say hello in one sentence."}],
    "temperature": 0.7,
    "max_tokens": 50
}

try:
    response = requests.post(url, json=payload, headers=headers, timeout=20)
    print(f"Status: {response.status_code}")
except Exception as exc:
    print(f"Failed to connect: {exc}")
