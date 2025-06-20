from crawler.vnexpress_crawler import crawl_latest_articles
from exporter.pdf_exporter import export_pdf
from integrations.google_drive_uploader import upload_to_drive
import os
from datetime import datetime

# Lấy ID thư mục Drive từ biến môi trường
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")

if __name__ == "__main__":
    # Tạo tên file PDF động theo ngày
    today_str = datetime.now().strftime("%d%m%Y")
    PDF_FILE_PATH = f"data/tin_nong_{today_str}.pdf"

    # Trên server, chúng ta không cần limit
    crawl_latest_articles(limit=None)
    
    actual_pdf_path = export_pdf(file_path=PDF_FILE_PATH, limit=None)

    if actual_pdf_path and os.path.exists(actual_pdf_path):
        if DRIVE_FOLDER_ID:
            print("\n--- Bắt đầu tải lên Google Drive ---")
            upload_to_drive(actual_pdf_path, DRIVE_FOLDER_ID)
        else:
            print("\n⚠️ Bỏ qua tải lên Drive: Biến môi trường DRIVE_FOLDER_ID chưa được cấu hình.")
    else:
        print(f"\n⚠️ Bỏ qua tải lên Drive: File PDF '{actual_pdf_path}' không được tạo.")
