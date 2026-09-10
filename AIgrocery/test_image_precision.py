import agents
import os
from dotenv import load_dotenv

load_dotenv()

def test_precision():
    items = ["Upma Mix", "Poha", "Pav Bread", "Tomato"]
    print("--- Precision Image Test ---")
    for item in items:
        url = agents.get_image_url(item)
        print(f"Item: {item}")
        print(f"URL: {url}")
        print("-" * 20)

if __name__ == "__main__":
    test_precision()
