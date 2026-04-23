import os
import time
import dropbox
import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
import io

DROPBOX_TOKEN = os.environ.get("DROPBOX_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
YOUTUBE_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN")
DROPBOX_FOLDER = "/Phonk Videos"
CHECK_INTERVAL = 60

def get_groq_metadata(filename):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a YouTube SEO expert for phonk music. Generate metadata in this EXACT format:\nTITLE: [title max 80 chars]\nDESCRIPTION: [4-5 sentences about brazilian phonk vibe, heavy 808, cowbell, dark energy, subscribe CTA]\nTAGS: phonk, brazilian phonk, phonk music, drift phonk, phonk 2025, dark phonk, phonk beats, cowbell phonk\nHASHTAGS: #phonk #brazilianphonk #phonkmusic #driftphonk #phonk2025"},
            {"role": "user", "content": f"Generate YouTube metadata for this phonk video: {filename}"}
        ]
    }
    r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
    result = r.json()["choices"][0]["message"]["content"]
    
    title = ""
    description = ""
    tags = []
    
    for line in result.split("\n"):
        if line.startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip()[:100]
        elif line.startswith("DESCRIPTION:"):
            description = line.replace("DESCRIPTION:", "").strip()
        elif line.startswith("TAGS:"):
            tags = [t.strip() for t in line.replace("TAGS:", "").split(",")]
        elif line.startswith("HASHTAGS:"):
            description += "\n\n" + line.replace("HASHTAGS:", "").strip()
    
    return title, description, tags

def get_youtube_service():
    creds = Credentials(
        token=None,
        refresh_token=YOUTUBE_REFRESH_TOKEN,
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token"
    )
    return build("youtube", "v3", credentials=creds)

def upload_to_youtube(video_data, filename):
    title, description, tags = get_groq_metadata(filename)
    youtube = get_youtube_service()
    
    body = {
        "snippet": {
            "title": title or filename,
            "description": description,
            "tags": tags,
            "categoryId": "10"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True
        }
    }
    
    media = MediaIoBaseUpload(io.BytesIO(video_data), mimetype="video/mp4", resumable=True, chunksize=10*1024*1024)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploading: {int(status.progress() * 100)}%")
    
    print(f"Uploaded: https://youtube.com/watch?v={response['id']}")
    return response['id']

def main():
    dbx = dropbox.Dropbox(DROPBOX_TOKEN)
    processed = set()
    
    print("Bot started, watching Dropbox folder...")
    
    while True:
        try:
            result = dbx.files_list_folder(DROPBOX_FOLDER)
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    if entry.id not in processed and entry.name.endswith(('.mp4', '.mov', '.avi')):
                        print(f"New video found: {entry.name}")
                        _, response = dbx.files_download(entry.path_lower)
                        video_data = response.content
                        upload_to_youtube(video_data, entry.name)
                        processed.add(entry.id)
                        print(f"Done: {entry.name}")
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
