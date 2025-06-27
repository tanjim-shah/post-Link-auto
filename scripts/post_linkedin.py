import os
import json
import base64
import mimetypes
from time import sleep
import requests
from google import genai
from google.genai import types

# Load environment variables
LINKEDIN_ORG_ID = os.environ["LINKEDIN_ORG_ID"]
LINKEDIN_ACCESS_TOKEN = os.environ["LINKEDIN_ACCESS_TOKEN"]
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

with open("urls.json") as f:
    urls = json.load(f)

genai.configure(api_key=GEMINI_API_KEY)

def generate_article_content(url):
    prompt = f"Write a professional LinkedIn article for this blog post: {url}"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={GOOGLE_API_KEY}"

    response = requests.post(
        api_url,
        json={"contents": [{"parts": [{"text": prompt}]}]},
    )
    data = response.json()

    if response.status_code != 200 or "candidates" not in data:
        print("Article generation failed:", data)
        return "Error generating article."

    return data["candidates"][0]["content"]["parts"][0]["text"]

def generate_image(title, output_path):
    client = genai.Client(api_key=GEMINI_API_KEY)
    model = "gemini-2.0-flash-preview-image-generation"
    prompt = f"Create a LinkedIn header image for: {title}"

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(prompt)],
        )
    ]
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
        response_mime_type="text/plain",
    )

    for chunk in client.models.generate_content_stream(
        model=model, contents=contents, config=config
    ):
        if (
            chunk.candidates
            and chunk.candidates[0].content
            and chunk.candidates[0].content.parts
            and chunk.candidates[0].content.parts[0].inline_data
        ):
            inline_data = chunk.candidates[0].content.parts[0].inline_data
            data_buffer = inline_data.data
            file_extension = mimetypes.guess_extension(inline_data.mime_type) or ".png"
            full_path = f"{output_path}{file_extension}"
            with open(full_path, "wb") as f:
                f.write(data_buffer)
            print(f"Image saved: {full_path}")
            return full_path
    return None

def upload_image_to_imgbb(image_path):
    # Optional: Replace with your preferred image host or CDN
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    res = requests.post(
        "https://api.imgbb.com/1/upload",
        params={"key": "YOUR_IMGBB_API_KEY"},
        data={"image": b64},
    )
    data = res.json()
    return data["data"]["url"] if "data" in data else None

def post_to_linkedin(title, body, image_url):
    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }
    post_data = {
        "author": f"urn:li:organization:{LINKEDIN_ORG_ID}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": title},
                "shareMediaCategory": "ARTICLE",
                "media": [
                    {
                        "status": "READY",
                        "description": {"text": body[:150]},
                        "originalUrl": image_url,
                        "title": {"text": title},
                    }
                ],
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    res = requests.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=post_data)
    print(f"LinkedIn post response: {res.status_code} - {res.text}")

def main():
    for url in urls:
        title = f"Insights from: {url.split('/')[-1].replace('-', ' ').title()}"
        print(f"Processing: {url}")

        article_text = generate_article_content(url)
        if article_text.startswith("Error"):
            print("Skipping due to article error.")
            continue

        local_image_path = generate_image(title, "linkedin_image")
        if not local_image_path:
            print("Skipping due to image error.")
            continue

        image_url = upload_image_to_imgbb(local_image_path)
        if not image_url:
            print("Skipping due to image upload error.")
            continue

        post_to_linkedin(title, article_text, image_url)
        sleep(10)

if __name__ == "__main__":
    main()
