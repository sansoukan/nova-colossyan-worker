
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

COLOSSYAN_API_KEY = os.getenv("COLOSSYAN_API_KEY")
if not COLOSSYAN_API_KEY:
    raise Exception("❌ COLOSSYAN_API_KEY is missing.")

text_fr = "Bonjour, je suis Nova. Ceci est un test avec la structure scenes + settings global."

print("🎬 Sending to Colossyan with dual settings structure...")
url = "https://app.colossyan.com/api/v1/video-generation-jobs"
headers = {
    "Authorization": f"Bearer {COLOSSYAN_API_KEY}",
    "Content-Type": "application/json"
}

settings_block = {
    "name": "nova-default",
    "resolution": "720p",
    "subtitles": False,
    "videoLayout": "face",
    "padding": "none",
    "videoSize": {
        "type": "square",
        "width": 1080,
        "height": 1080
    }
}

payload = {
    "title": "Nova - Test Dual Settings",
    "script": {
        "type": "text",
        "input": text_fr
    },
    "videoCreative": {
        "settings": settings_block,  # GLOBAL
        "scenes": [
            {
                "avatar": {
                    "name": "nova_avatar"
                },
                "voice": {
                    "id": "0e051caf8e0947a18870ee24bbbfce36"
                },
                "background": {
                    "color": "#ffffff"
                },
                "settings": settings_block  # PER SCENE
            }
        ]
    }
}

response = requests.post(url, headers=headers, json=payload)
print("📦 Status Code:", response.status_code)
print("📦 Response:", response.text)
response.raise_for_status()

res_json = response.json()
video_id = res_json.get("id")
if not video_id:
    raise Exception("❌ No video ID returned.")
print(f"✅ Video Job ID: {video_id}")

# Attente
status_url = f"https://app.colossyan.com/api/v1/video-generation-jobs/{video_id}"
print("⏳ Waiting for video to be ready...")
while True:
    status_res = requests.get(status_url, headers=headers).json()
    print("📡 Status:", status_res)
    if status_res.get("status") == "done":
        video_url = status_res.get("download_url")
        print(f"🎉 Video ready: {video_url}")
        break
    elif status_res.get("status") == "failed":
        raise Exception("❌ Video generation failed.")
    time.sleep(5)
