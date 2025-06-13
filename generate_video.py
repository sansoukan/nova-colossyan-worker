
import os
import time
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
COLOSSYAN_API_KEY = os.getenv("COLOSSYAN_API_KEY")
QUESTION_UUID = os.getenv("QUESTION_UUID")

print(f"🧪 QUESTION_UUID = {QUESTION_UUID}")
if not QUESTION_UUID:
    raise Exception("❌ QUESTION_UUID is not defined.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
bucket = "nova-videos"
filename = f"{QUESTION_UUID}_fr_question.mp4"
local_path = f"/tmp/{filename}"

# Récupération de la question
print(f"🔍 Fetching question {QUESTION_UUID}...")
data = supabase.table("nova_questions").select("*").eq("id", QUESTION_UUID).single().execute()
question = data.data or {}
text_fr = question.get("question_fr") or ""
print(f"🎤 Question: {text_fr}")

# Appel Colossyan avec videoSize objet
print("🎬 Sending to Colossyan (final structure)...")
url = "https://app.colossyan.com/api/v1/video-generation-jobs"
headers = {
    "Authorization": f"Bearer {COLOSSYAN_API_KEY}",
    "Content-Type": "application/json"
}
payload = {
    "title": f"Nova - {QUESTION_UUID}",
    "script": {
        "type": "text",
        "input": text_fr
    },
    "videoCreative": {
        "avatar": {
            "name": "nova_avatar"
        },
        "voice": {
            "id": "0e051caf8e0947a18870ee24bbbfce36"
        },
        "background": {
            "color": "#ffffff"
        },
        "settings": {
            "resolution": "720p",
            "subtitles": False,
            "videoLayout": "face",
            "padding": "none",
            "videoSize": {
                "type": "square"
            }
        }
    }
}

response = requests.post(url, headers=headers, json=payload)
print("📦 Status Code:", response.status_code)
print("📦 Full Response Text:")
print(response.text)
response.raise_for_status()

res_json = response.json()
video_id = res_json.get("id")
if not video_id:
    raise Exception("❌ No video ID returned from Colossyan.")
print(f"✅ Video Job ID: {video_id}")

# Suivi du job
print("⏳ Waiting for video...")
status_url = f"https://app.colossyan.com/api/v1/video-generation-jobs/{video_id}"
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

# Téléchargement
print("⬇️ Downloading video...")
video_data = requests.get(video_url)
with open(local_path, "wb") as f:
    f.write(video_data.content)

# Upload Supabase
print("☁️ Uploading to Supabase...")
with open(local_path, "rb") as f:
    supabase.storage.from_(bucket).upload(path=filename, file=f, file_options={"upsert": True})

# Mise à jour dans la base
public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{filename}"
supabase.table("nova_questions").update({ "video_question_fr": public_url }).eq("id", QUESTION_UUID).execute()
print(f"✅ Video uploaded and linked in Supabase for {QUESTION_UUID}")
