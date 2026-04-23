import os
import dropbox
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
import io

# Secrets
DROPBOX_TOKEN = os.environ.get("DROPBOX_TOKEN")
YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
YOUTUBE_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN")

DROPBOX_FOLDER = "/Phonk Videos" 

def get_formatted_metadata(filename):
    # Fayl adından (.mp4) hissəsini silirik. 
    # Əgər fayl adı "Kabus.mp4"-dirsə, track_name "Kabus" olacaq.
    track_name = os.path.splitext(filename)[0]
    
    # Başlıq formatı (Na.Camara ilə)
    title = f"Na.Camara - {track_name} (Original Track)"
    
    # Description formatı
    description = f"""🔥 Na.Camara - Phonk/Brazilian Funk
____________________________________________________

🎵 Track: {track_name}
🎧 Genre: Brazilian Funk / Dark Phonk
🎚️ Style: Slowed + Reverb
____________________________________________________

🎧 Best experienced with headphones
🔊 Turn up the volume
____________________________________________________

📌 Tags:
#phonk #darkphonk #brazilianphonkmusic #slowed #slowedreverb #phonkmusic #funk #inferno #music
____________________________________________________

⚠️ Copyright:
Music produced by Na.Camara
All rights reserved ©2026"""

    tags = ["phonk", "darkphonk", "brazilian funk", "slowed", "reverb", "phonk music", "funk", "inferno"]
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
    title, description, tags = get_formatted_metadata(filename)
    youtube = get_youtube_service()
    
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "10" 
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }
    
    media = MediaIoBaseUpload(io.BytesIO(video_data), mimetype="video/mp4", resumable=True, chunksize=10*1024*1024)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploading: {int(status.progress() * 100)}%")
    
    print(f"Uploaded successfully! Video ID: {response['id']}")
    return response['id']

def main():
    if not DROPBOX_TOKEN:
        print("Error: DROPBOX_TOKEN not found!")
        return

    dbx = dropbox.Dropbox(DROPBOX_TOKEN)
    
    try:
        result = dbx.files_list_folder(DROPBOX_FOLDER)
        files_found = False

        for entry in result.entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                if entry.name.lower().endswith(('.mp4', '.mov', '.avi')):
                    files_found = True
                    print(f"Processing: {entry.name}")
                    
                    _, response = dbx.files_download(entry.path_lower)
                    video_data = response.content
                    
                    try:
                        upload_to_youtube(video_data, entry.name)
                        dbx.files_delete_v2(entry.path_lower)
                        print(f"Deleted from Dropbox: {entry.name}")
                    except Exception as yt_err:
                        print(f"YouTube upload failed: {yt_err}")

        if not files_found:
            print("No videos found in folder.")

    except Exception as e:
        print(f"Main Error: {e}")

if __name__ == "__main__":
    main()
