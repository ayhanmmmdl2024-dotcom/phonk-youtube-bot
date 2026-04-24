import os
import dropbox
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
import io
import mimetypes

# Secrets (GitHub Settings -> Secrets hissəsindən götürülür)
# Köhnə DROPBOX_TOKEN yerinə bunları yaz:
DROPBOX_APP_KEY = os.environ.get("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.environ.get("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.environ.get("DROPBOX_REFRESH_TOKEN")
YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
YOUTUBE_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN")

DROPBOX_FOLDER = "/Phonk Videos" 

def get_formatted_metadata(filename):
    """Videonun adına görə başlıq və təsviri təyin edir."""
    track_name = os.path.splitext(filename)[0]
    
    # Əgər fayl adında 'shorts' varsa (məs: Kabus_shorts.mp4)
    if "shorts" in filename.lower():
        clean_name = track_name.lower().replace('_shorts', '').capitalize()
        # Sənin istədiyin Shorts formatı
        title = f"/{clean_name} - Na.Camara/ #darkphonk #music #bass #driftphonk #phonk #phonkmusic #funk"
        description = f"""🔥 Na.Camara - Phonk/Brazilian Funk
____________________________________________________

🎵 Track: {clean_name}
🎧 Genre: Brazilian Funk / Dark Phonk
🎚️ Style: Slowed + Reverb
____________________________________________________

🎧 Best experienced with headphones
🔊 Turn up the volume
____________________________________________________

📌 Tags:
#phonk #darkphonk #brazilianphonkmusic #slowed #slowedreverbmusicmashup #phonkmusic #funk #inferno #music
____________________________________________________

⚠️ Copyright:
Music produced by Na.Camara
All rights reserved ©2026"""
        tags = ["phonk", "darkphonk", "music", "shorts", "bass"]
    else:
        # Normal uzun video formatı
        title = f"Na.Camara - {track_name} (Original Track)"
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
        tags = ["phonk", "darkphonk", "brazilian funk", "slowed", "reverb"]

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
    """YouTube-a qapaq şəklini yükləyir."""
    mimetype = mimetypes.guess_type(thumbnail_filename)[0] or 'image/jpeg'
    media = MediaIoBaseUpload(io.BytesIO(thumbnail_data), mimetype=mimetype, resumable=True)
    try:
        youtube.thumbnails().set(videoId=video_id, media_body=media).execute()
        print(f"Thumbnail yükləndi: {thumbnail_filename}")
    except Exception as e:
        print(f"Thumbnail xətası: {e}")

def check_for_thumbnail(dbx, video_filename):
    """Videoya uyğun şəkli Dropbox-da axtarır."""
    base_name = os.path.splitext(video_filename)[0]
    for ext in ['.jpg', '.jpeg', '.png']:
        path = f"{DROPBOX_FOLDER}/{base_name}{ext}"
        try:
            _, res = dbx.files_download(path.lower())
            return res.content, f"{base_name}{ext}"
        except:
            continue
    return None, None

def main():
    # Yeni Refresh Token sistemi üçün yoxlama
    if not all([DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN]):
        print("Xəta: Dropbox üçün lazımi açarlar (Key, Secret və ya Refresh Token) tapılmadı!")
        return

    # Dropbox-a Refresh Token ilə qoşulma (DOĞRU VARIANT)
    try:
        dbx = dropbox.Dropbox(
            app_key=DROPBOX_APP_KEY,
            app_secret=DROPBOX_APP_SECRET,
            oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
        )
        print("Dropbox bağlantısı Refresh Token ilə uğurla quruldu!")
    except Exception as e:
        print(f"Dropbox-a bağlanarkən xəta baş verdi: {e}")
        return

    youtube = get_youtube_service()
    
    # ... kodun ardı eyni qalır
    youtube = get_youtube_service()
    
    try:
        result = dbx.files_list_folder(DROPBOX_FOLDER)
        for entry in result.entries:
            if isinstance(entry, dropbox.files.FileMetadata) and entry.name.lower().endswith(('.mp4', '.mov')):
                print(f"\nVideo emal edilir: {entry.name}")
                
                # 1. Videonu yüklə
                _, res = dbx.files_download(entry.path_lower)
                video_data = res.content
                
                title, desc, tags = get_formatted_metadata(entry.name)
                
                body = {
                    "snippet": {"title": title, "description": desc, "tags": tags, "categoryId": "10"},
                    "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
                }
                
                # 2. YouTube-a göndər
                media = MediaIoBaseUpload(io.BytesIO(video_data), mimetype="video/mp4", resumable=True)
                request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
                
                video_response = request.execute()
                v_id = video_response['id']
                print(f"Video yükləndi! ID: {v_id}")
                
                # 3. Thumbnail yoxla və yüklə
                thumb_data, thumb_name = check_for_thumbnail(dbx, entry.name)
                if thumb_data:
                    upload_thumbnail(youtube, v_id, thumb_data, thumb_name)
                    dbx.files_delete_v2(f"{DROPBOX_FOLDER}/{thumb_name}".lower())
                
                # 4. Dropbox-dan sil
                dbx.files_delete_v2(entry.path_lower)
                print(f"Dropbox-dan silindi: {entry.name}")

    except Exception as e:
        print(f"Sistem xətası: {e}")

if __name__ == "__main__":
    main()
