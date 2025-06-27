import requests, json, os
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
        json={ "contents": [{"parts": [{"text": prompt}]}] },
    )
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]

def generate_image_url(title):
    prompt = f"Create a LinkedIn header image for: {title}"
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent?key={GOOGLE_API_KEY}",
        json={ "contents": [{"parts": [{"text": prompt}]}] },
    )
    return "https://your-image-url.com/generated.jpg"

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
    print(response.status_code, response.text)

for url in urls:
    title = f"Insights from: {url.split('/')[-1].replace('-', ' ').title()}"
    article_text = generate_article_content(url)
    image_url = generate_image_url(title)
    post_to_linkedin(title, article_text, image_url)
    sleep(10)
