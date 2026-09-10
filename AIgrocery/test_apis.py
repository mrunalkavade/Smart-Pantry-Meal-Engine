import os
import requests
from dotenv import load_dotenv

load_dotenv()

UNSPLASH_KEY = os.environ.get("API_KEY_UNSPLASH")
PEXELS_KEY = os.environ.get("API_KEY_PEXELS")

print(f"Unsplash Key: {UNSPLASH_KEY[:5]}...")
print(f"Pexels Key: {PEXELS_KEY[:5]}...")

query = "tomato fresh organic produce white background"

print("\nTesting Unsplash...")
try:
    url = f"https://api.unsplash.com/search/photos?query={query}&per_page=1&client_id={UNSPLASH_KEY}"
    res = requests.get(url, timeout=5)
    print(f"Unsplash Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        if data.get("results"):
            print(f"Unsplash Result: {data['results'][0]['urls']['small']}")
        else:
            print("Unsplash: No results found")
    else:
        print(f"Unsplash Error Body: {res.text}")
except Exception as e:
    print(f"Unsplash Exception: {e}")

print("\nTesting Pexels...")
try:
    headers = {"Authorization": PEXELS_KEY}
    params = {"query": query, "per_page": 1}
    res = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params, timeout=5)
    print(f"Pexels Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        if data.get("photos"):
            print(f"Pexels Result: {data['photos'][0]['src']['medium']}")
        else:
            print("Pexels: No results found")
    else:
        print(f"Pexels Error Body: {res.text}")
except Exception as e:
    print(f"Pexels Exception: {e}")
