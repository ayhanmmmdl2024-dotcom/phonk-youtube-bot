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
    # Uzantıları təmizləyirik
    track_name = filename.replace('.mp4', '').replace('.MP4', '').replace('.mov', '')
    
    # .upper() əlavə edirik ki, hər yerdə BÖYÜK hərflə görünsün
    clean_name = track_name.replace('_', ' ').replace('- shorts', '').strip().upper()
    
    # ... qalan if/else bloku eyni qalır ...
    
    # Əgər fayl adında 'shorts' varsa (məs: Kabus_shorts.mp4)
    if "shorts" in filename.lower():
        # 1. Shorts üçün adı təmizləyib BÖYÜK hərflə edirik
        clean_name = track_name.replace('_shorts', '').replace('_', ' ').strip().upper()
        
        # 2. Shorts Başlığı (Title)
        title = f"{clean_name} - Na.Camara/ #darkphonk #music #bass #shorts #phonk"
        
        # 3. Shorts Təsviri (Description)
        sep = "─── ⋆⋅☆⋅⋆ ───"
        description = f"🔥 Na.Camara - Phonk/Brazilian Funk\n"
        description += f"{sep}\n\n"
        description += f"🎵 Track: {clean_name}\n"
        description += f"🎧 Style: Brazilian Funk / Dark Phonk\n\n"
        description += f"{sep}\n\n"
        description += "📌 Tags:\n#phonk #shorts #darkphonk #music #bass #funk"
        
        tags = ["phonk", "darkphonk", "music", "shorts", "bass"]

⚠️ Copyright:
Music produced by Na.Camara
All rights reserved ©2026"""
        tags = ["phonk", "darkphonk", "music", "shorts", "bass"]
   else:
        # 1. Adı təmizləyib hamısını BÖYÜK hərflə edirik
        display_name = track_name.replace('_', ' ').strip().upper()
        
        # 2. Başlıq nizamlanır
        title = f"Na.Camara - {display_name} (Original Track)"
        
        # 3. Təsvir (Description) nizamlanır
        sep = "─── ⋆⋅☆⋅⋆ ───"
        description = f"🔥 Na.Camara - Phonk/Brazilian Funk\n"
        description += f"{sep}\n\n"
        description += f"🎵 Track: {display_name}\n"
        description += f"🎧 Genre: Brazilian Funk / Dark Phonk\n"
        description += f"🎼 Style: Slowed + Reverb\n\n"
        description += f"{sep}\n\n"
        description += "📢 Best experienced with headphones\n"
        description += "🔊 Turn up the volume\n\n"
        description += "📌 Tags:\n#phonk #darkphonk #brazilianphonk #music #funk #bass"
        
        tags = ["phonk", "darkphonk", "music", "bass"]
____________________________________________________
# 56-cı sətirdən sonranı belə tənzimləyə bilərsən:
        description += f"\n🎵 Track: {display_name}\n🎧 Genre: Brazilian Funk / Dark Phonk\n🎬 Style: Slowed + Reverb"
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
           _, res = dbx.files_download(path)
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
            def check_for_thumbnail(dbx, video_filename):
    # Videonun təmiz adını alırıq
    base_name = video_filename.replace('.mp4', '').replace('.MP4', '').replace('.mov', '').strip().lower()
    
    try:
        # Dropbox qovluğundakı hər şeyə baxırıq
        files = dbx.files_list_folder(DROPBOX_FOLDER).entries
        
        for file in files:
            # Faylın adını və uzantısını ayırırıq
            f_name, f_ext = os.path.splitext(file.name)
            
            # Əgər adlar (kiçik hərflə müqayisədə) eynidirsə və fayl şəkildirsə
            if f_name.lower() == base_name and f_ext.lower() in ['.jpg', '.jpeg', '.png']:
                print(f"Uyğun şəkil tapıldı: {file.name}")
                # Şəkli yükləmək üçün path_lower istifadə edirik
                _, res = dbx.files_download(file.path_lower)
                return res.content, file.name
    except Exception as e:
        print(f"Thumbnail axtarışında xəta: {e}")
        
    return None, None
        thumb_data, thumb_name = check_for_thumbnail(dbx, entry.name)
        if thumb_data:
            print(f"Üz qabığı yüklənir: {thumb_name}")
            upload_thumbnail(youtube, v_id, thumb_data, thumb_name)
            # Yüklənmiş şəkli Dropbox-dan silirik
            dbx.files_delete_v2(f"{DROPBOX_FOLDER}/{thumb_name}")
                
                # 4. Dropbox-dan sil
                dbx.files_delete_v2(entry.path_lower)
                print(f"Dropbox-dan silindi: {entry.name}")

    except Exception as e:
        print(f"Sistem xətası: {e}")

if __name__ == "__main__":
    main()
