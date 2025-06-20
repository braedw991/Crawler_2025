# filepath: d:\Python\Crawler_2025final\Crawler_2025\integrations\google_drive_uploader.py
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Đường dẫn tới file credentials và các quyền cần thiết
SERVICE_ACCOUNT_FILE = 'config/gold-cocoa-460316-p9-b467244cdbc8.json'
SCOPES = ['https://www.googleapis.com/auth/drive']

def upload_to_drive(file_path: str, folder_id: str):
    """
    Tải một file lên thư mục cụ thể trên Google Drive.
    """
    try:
        # Xác thực
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        
        # Tạo service client
        service = build('drive', 'v3', credentials=creds)
        
        file_name = os.path.basename(file_path)
        print(f"🚀 Đang tải file '{file_name}' lên Google Drive...")

        # Định nghĩa metadata cho file
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        # Tải file
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(body=file_metadata,
                                      media_body=media,
                                      fields='id').execute()
        
        print(f"✅ Tải lên thành công! File ID: {file.get('id')}")
        return file.get('id')

    except FileNotFoundError:
        print(f"❌ Lỗi: Không tìm thấy file credentials tại '{SERVICE_ACCOUNT_FILE}'")
    except Exception as e:
        print(f"❌ Đã xảy ra lỗi khi tải file lên Google Drive: {e}")
    
    return None