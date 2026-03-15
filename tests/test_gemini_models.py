import os

import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise SystemExit("GEMINI_API_KEY not set")

res = requests.get(
    f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}", timeout=15
)
if res.status_code == 200:
    for model in res.json().get("models", []):
        print(model["name"])
else:
    print(res.status_code)
