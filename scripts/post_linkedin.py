import requests
import json
import os
from time import sleep

LINKEDIN_ORG_ID = os.environ["LINKEDIN_ORG_ID"]
LINKEDIN_ACCESS_TOKEN = os.environ["LINKEDIN_ACCESS_TOKEN"]
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]

with open("urls.json") as f:
    urls = json.load(f)

max_retries = 3
retry_delay = 5  # seconds

def generate_article_content(url):
    prompt = f"Write a professional LinkedIn article for this blog post: {url}"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={GOOGLE_API_KEY}"

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(
                api_url,
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
            data = response.json()

            if response.status_code != 200:
                print(f"[Attempt {attempt}] Article API error {response.status_code}: {data}")
                sleep(retry_delay)
                continue

            if "candidates" in data and len(data["candidates"]) > 0:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                print(f"[Attempt {attempt}] 'candidates' missing or empty in article response: {data}")
                sleep(retry_delay)
        except Exception as e:
            print(f"[Attempt {attempt}] Exception during article API call: {e}")
            sleep(retry_delay)

    return f"Error generating article after {max_retries} attempts."

def generate_image_url(title):
    prompt = f"Create a LinkedIn header image for: {title}"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-preview-image-generation:generateContent?key={GOOGLE_API_KEY}"

    try:
        response = requests.post(
            api_url,
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "responseModality": ["IMAGE", "TEXT"]  # Specify modalities here
            },
        )
        data = response.json()

        if response.status_code != 200:
            print(f"Image API error {response.status_code}: {data}")
            return None

        # Print full response for debugging (remove/comment out after)
        # print(json.dumps(data, indent=2))

        if "candidates" in data and len(data["candidates"]) > 0:
            candidate = data["candidates"][0]
            content = candidate.get("content", {})

            # Adjust this based on your actual API response
            # Sometimes the image is base64, or sometimes there's a URL field
            if "image" in content:
                image_info = content["image"]
                if isinstance(image_info, str):
                    # Could be a base64 string or URL
                    return image_info
                if isinstance(image_info, dict) and "url" in image_info:
                    return image_info["url"]

        print("Image URL not found in response:", data)
        return None
    except Exception as e:
        print("Exception generating image:", e)
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
        print("Error posting to LinkedIn")

def main():
    for url in urls:
        title = f"Insights from: {url.split('/')[-1].replace('-', ' ').title()}"
        print(f"Processing: {url}")

        article_text = generate_article_content(url)
        if article_text.startswith("Error generating article"):
            print(f"Skipping URL due to article generation error: {url}")
            continue

        image_url = generate_image_url(title)
        if not image_url:
            print(f"Skipping URL due to image generation error: {url}")
            continue

        post_to_linkedin(title, article_text, image_url)
        sleep(10)  # To avoid rate limits

if __name__ == "__main__":
    main()
