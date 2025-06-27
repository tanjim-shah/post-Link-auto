import requests
import json
import os
from time import sleep

LINKEDIN_ORG_ID = os.environ["LINKEDIN_ORG_ID"]
LINKEDIN_ACCESS_TOKEN = os.environ["LINKEDIN_ACCESS_TOKEN"]
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]

with open("urls.json") as f:
    urls = json.load(f)

def generate_article_content(url):
    prompt = f"Write a professional LinkedIn article for this blog post: {url}"
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GOOGLE_API_KEY}",
        json={"contents": [{"parts": [{"text": prompt}]}]},
    )
    data = response.json()

    if response.status_code != 200:
        print(f"[ERROR] Article API returned status {response.status_code}")
        print(data)
        return None

    if "candidates" in data and len(data["candidates"]) > 0:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    else:
        print("[ERROR] 'candidates' missing or empty in article API response")
        print(data)
        return None

def generate_image_url(title):
    prompt = f"Create a LinkedIn header image for: {title}"
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent?key={GOOGLE_API_KEY}",
        json={"contents": [{"parts": [{"text": prompt}]}]},
    )
    data = response.json()

    if response.status_code != 200:
        print(f"[ERROR] Image API returned status {response.status_code}")
        print(data)
        return None

    # Example: parse image URL from response (adjust according to real API)
    # Here I assume the response has a key 'candidates' with 'imageUrl' somewhere
    if "candidates" in data and len(data["candidates"]) > 0:
        candidate = data["candidates"][0]
        # This is just an example - adjust depending on real response structure
        if "content" in candidate and "imageUrl" in candidate["content"]:
            return candidate["content"]["imageUrl"]

    print("[ERROR] Could not find image URL in response")
    print(data)
    return None

def post_to_linkedin(title, body, image_url):
    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }
    post_data = {
        "author": f"urn:li:organization:{LINKEDIN_ORG_ID}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": title},
                "shareMediaCategory": "ARTICLE",
                "media": [{
                    "status": "READY",
                    "description": {"text": body[:150]},
                    "originalUrl": image_url,
                    "title": {"text": title}
                }]
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    response = requests.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=post_data)
    print(f"LinkedIn post response: {response.status_code} - {response.text}")
    if response.status_code != 201:
        print("[ERROR] Failed to post on LinkedIn")

def main():
    for url in urls:
        title = f"Insights from: {url.split('/')[-1].replace('-', ' ').title()}"
        print(f"Processing URL: {url}")

        article_text = generate_article_content(url)
        if not article_text:
            print(f"[SKIP] Article generation failed for {url}")
            continue

        image_url = generate_image_url(title)
        if not image_url:
            print(f"[SKIP] Image generation failed for {url}")
            continue

        post_to_linkedin(title, article_text, image_url)
        sleep(10)  # avoid rate limits or abuse

if __name__ == "__main__":
    main()
