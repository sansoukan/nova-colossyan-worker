
import os
import time
import requests
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
COLOSSYAN_API_KEY = os.getenv("COLOSSYAN_API_KEY")
QUESTION_UUID = os.getenv("QUESTION_UUID")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
bucket = "nova-videos"
filename = f"{QUESTION_UUID}_fr_question.mp4"
local_path = f"/tmp/{filename}"

# Étape 1 : récupérer la question
print(f"🔎 Recherche de la question UUID {QUESTION_UUID}...")
data = supabase.table("nova_questions").select("*").eq("id", QUESTION_UUID).single().execute()
question = data.data
if not question:
    raise Exception(f"❌ Question UUID {QUESTION_UUID} introuvable.")

text_fr = question["question_fr"]

# Étape 2 : envoyer à Colossyan
print("🎬 Envoi à Colossyan...")
create_url = "https://api.colossyan.com/v2/videos"
headers = {
    "Authorization": f"Bearer {COLOSSYAN_API_KEY}",
    "Content-Type": "application/json"
}
payload = {
    "title": f"Nova - {QUESTION_UUID}",
    "input_text": text_fr,
    "avatar": { "name": "nova_avatar" },
    "voice": { "language": "fr", "voice_id": "0e051caf8e0947a18870ee24bbbfce36" },
    "config": { "resolution": "720p", "subtitles": False }
}
response = requests.post(create_url, headers=headers, json=payload)
video_id = response.json().get("video_id")
if not video_id:
    raise Exception("❌ Échec Colossyan.")

print(f"✅ Vidéo créée : {video_id}")

# Étape 3 : attendre la génération
status_url = f"https://api.colossyan.com/v2/videos/{video_id}"
while True:
    status_res = requests.get(status_url, headers=headers).json()
    status = status_res.get("status")
    if status == "done":
        video_url = status_res["video_url"]
        print(f"🎉 Vidéo prête : {video_url}")
        break
    elif status == "failed":
        raise Exception("❌ Échec génération.")
    time.sleep(5)

# Étape 4 : téléchargement local
print("⬇️ Téléchargement...")
video_data = requests.get(video_url)
with open(local_path, "wb") as f:
    f.write(video_data.content)

# Étape 5 : upload Supabase
print("☁️ Upload dans Supabase...")
with open(local_path, "rb") as f:
    supabase.storage.from_(bucket).upload(path=filename, file=f, file_options={"upsert": True})

# Étape 6 : mise à jour
public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{filename}"
supabase.table("nova_questions").update({ "video_question_fr": public_url }).eq("id", QUESTION_UUID).execute()

print(f"✅ Vidéo prête pour {QUESTION_UUID}")
