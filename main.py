import os
import io
import time
import mimetypes
import dropbox
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials

# --- AYARLAR ---
DROPBOX_APP_KEY = os.environ.get("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.environ.get("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.environ.get("DROPBOX_REFRESH_TOKEN")

YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
YOUTUBE_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN")

DROPBOX_FOLDER = "/Phonk Videos"

def get_formatted_metadata(filename):
    """Fayl adından YouTube üçün başlıq, təsvir və teqlər yaradır."""
    # .mp4 silirik
    track_name = filename.replace('.mp4', '').replace('.MP4', '').replace('.mov', '')
    
    # Başlıqları təmizləyirik (Böyük hərflə)
    display_name = track_name.replace('_', ' ').replace('- shorts', '').replace('shorts', '').strip().upper()
    
    sep = "———— ★·☆·★ ————"
    
    # Shorts yoxlanışı və Başlıq nizamlanması
    if "shorts" in filename.lower():
        title = f"{display_name} - Na.Camara"
        description = f"🔥 Na.Camara - Phonk/Brazilian Funk\n{sep}\n\n🎵 Track: {display_name}\n\n{sep}\n#shorts #phonk #bass #darkphonk #music"
    else:
        title = f"Na.Camara - {display_name} (Original Track)"
        description = f"🔥 Na.Camara - Phonk/Brazilian Funk\n{sep}\n\n🎵 Track: {display_name}\n🎬 Style: Slowed + Reverb\n\n{sep}\n#phonk #darkphonk #music #bass"

    tags = ["phonk", "darkphonk", "brazilian funk", "slowed", "reverb"]
    return title, description, tags

def get_youtube_service():
    """YouTube API-yə qoşulma."""
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
    """Dropbox-da uyğun şəkli axtarır."""
    base_name = os.path.splitext(video_filename)[0]
    # Fayl adındakı sonluğu təmizləyirik (məs: "MAHNI_shorts" -> "MAHNI")
    clean_base = base_name.replace('_shorts', '').replace('- shorts', '')
    
    for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.PNG']:
        path = f"{DROPBOX_FOLDER}/{clean_base}{ext}"
        try:
            _, res = dbx.files_download(path)
            return res.content, f"{clean_base}{ext}"
        except:
            continue
    return None, None

def main():
    if not all([DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN]):
        print("Xəta: Dropbox açarları tapılmadı!")
        return

    try:
        dbx = dropbox.Dropbox(
            app_key=DROPBOX_APP_KEY,
            app_secret=DROPBOX_APP_SECRET,
            oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
        )
        print("Dropbox bağlantısı uğurla quruldu!")
    except Exception as e:
        print(f"Dropbox xətası: {e}")
        return

    youtube = get_youtube_service()

    try:
        result = dbx.files_list_folder(DROPBOX_FOLDER)
        for entry in result.entries:
            if isinstance(entry, dropbox.files.FileMetadata) and entry.name.lower().endswith(('.mp4', '.mov')):
                print(f"\nVideo emal edilir: {entry.name}")
                
                # 1. Videonu Dropbox-dan yüklə
                _, res = dbx.files_download(entry.path_lower)
                video_data = res.content
                
                # 2. Metadata hazırla
                title, desc, tags = get_formatted_metadata(entry.name)
                
                body = {
                    "snippet": {"title": title, "description": desc, "tags": tags, "categoryId": "10"},
                    "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
                }
                
                # 3. YouTube-a video yüklə
                media = MediaIoBaseUpload(io.BytesIO(video_data), mimetype="video/mp4", resumable=True)
                request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
                
                video_response = request.execute()
                v_id = video_response['id']
                print(f"Video yükləndi! ID: {v_id}")
                
                time.sleep(5) # Gözləmə
                
                # 4. Thumbnail yoxla və yüklə
                thumb_data, thumb_name = check_for_thumbnail(dbx, entry.name)
                if thumb_data:
                    upload_thumbnail(youtube, v_id, thumb_data, thumb_name)
                    try:
                        dbx.files_delete_v2(f"{DROPBOX_FOLDER}/{thumb_name}")
                    except: pass
                
                # 5. Videonu sil
                dbx.files_delete_v2(entry.path_lower)
                print(f"Dropbox-dan silindi: {entry.name}")
                
    except Exception as e:
        print(f"Sistem xətası: {e}")

if __name__ == "__main__":
    main()
