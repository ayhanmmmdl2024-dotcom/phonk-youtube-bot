import os
import dropbox
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
import io
import mimetypes # Şəkil növünü müəyyən etmək üçün

# Secrets
DROPBOX_TOKEN = os.environ.get("DROPBOX_TOKEN")
YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
YOUTUBE_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN")

DROPBOX_FOLDER = "/Phonk Videos" 

def get_formatted_metadata(filename):
    # Fayl adından (.mp4) hissəsini silirik.
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

def upload_thumbnail(youtube, video_id, thumbnail_data, thumbnail_filename):
    """YouTube-a videonun qapaq şəklini yükləyir."""
    # Şəkil növünü (jpeg, png) müəyyən edək
    mimetype = mimetypes.guess_type(thumbnail_filename)[0] or 'application/octet-stream'
    
    media = MediaIoBaseUpload(io.BytesIO(thumbnail_data), mimetype=mimetype, resumable=True)
    
    try:
        print(f"Thumbnail yüklənir: {thumbnail_filename}...")
        request = youtube.thumbnails().set(
            videoId=video_id,
            media_body=media
        )
        response = request.execute()
        print("Thumbnail uğurla yükləndi!")
        return response
    except Exception as e:
        print(f"Thumbnail yükləmə xətası: {e}")
        return None

def upload_to_youtube(video_data, filename, youtube_service):
    """Videonu yükləyir və video_id-ni qaytarır."""
    title, description, tags = get_formatted_metadata(filename)
    
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "10" # Music kateqoriyası
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }
    
    media = MediaIoBaseUpload(io.BytesIO(video_data), mimetype="video/mp4", resumable=True, chunksize=10*1024*1024)
    request = youtube_service.videos().insert(part="snippet,status", body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploading: {int(status.progress() * 100)}%")
    
    print(f"Uploaded successfully! Video ID: {response['id']}")
    return response['id']

def check_for_thumbnail(dbx, video_filename):
    """Video faylının adına uyğun thumbnail (jpeg, png) şəklini Dropbox-da axtarır."""
    base_name = os.path.splitext(video_filename)[0]
    
    # Şəkil uzantılarını yoxlayırıq
    for ext in ['.jpg', '.jpeg', '.png']:
        thumbnail_path = f"{DROPBOX_FOLDER}/{base_name}{ext}"
        try:
            _, response = dbx.files_download(thumbnail_path.lower())
            print(f"Thumbnail tapıldı: {thumbnail_path}")
            return response.content, f"{base_name}{ext}" # Şəkil datasını və tam adını qaytarırıq
        except dropbox.exceptions.ApiError:
            continue # Bu şəkil yoxdursa, digərini yoxla
            
    return None, None # Thumbnail yoxdursa

def main():
    if not DROPBOX_TOKEN:
        print("Error: DROPBOX_TOKEN not found!")
        return

    dbx = dropbox.Dropbox(DROPBOX_TOKEN)
    youtube_service = get_youtube_service() # YouTube servisini bir dəfə yaradaq
    
    try:
        result = dbx.files_list_folder(DROPBOX_FOLDER)
        files_found = False

        # Öncə bütün faylları siyahıya alaq ki, videoları və şəkilləri ayıra bilək
        entries = result.entries
        
        for entry in entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                # Sadəcə video faylları emal et
                if entry.name.lower().endswith(('.mp4', '.mov', '.avi')):
                    files_found = True
                    print(f"\nProcessing Video: {entry.name}")
                    
                    # 1. Videonu Dropbox-dan yüklə
                    _, video_response = dbx.files_download(entry.path_lower)
                    video_data = video_response.content
                    
                    try:
                        # 2. Videonu YouTube-a yüklə
                        video_id = upload_to_youtube(video_data, entry.name, youtube_service)
                        
                        # 3. Thumbnail yoxla
                        thumbnail_data, thumbnail_filename = check_for_thumbnail(dbx, entry.name)
                        
                        # 4. Varsa, thumbnail yüklə
                        if thumbnail_data and video_id:
                            upload_thumbnail(youtube_service, video_id, thumbnail_data, thumbnail_filename)
                        
                        # 5. Təmizlik: Videonu Dropbox-dan sil
                        dbx.files_delete_v2(entry.path_lower)
                        print(f"Deleted Video from Dropbox: {entry.name}")
                        
                        # 6. Təmizlik: Varsa, Thumbnail-i də sil
                        if thumbnail_data:
                            thumbnail_path = f"{DROPBOX_FOLDER}/{thumbnail_filename}"
                            dbx.files_delete_v2(thumbnail_path.lower())
                            print(f"Deleted Thumbnail from Dropbox: {thumbnail_filename}")
                            
                    except Exception as yt_err:
                        print(f"YouTube upload failed: {yt_err}")

        if not files_found:
            print("No videos found in folder.")

    except Exception as e:
        print(f"Main Error: {e}")

if __name__ == "__main__":
    main()
