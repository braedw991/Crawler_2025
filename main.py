import os
from dotenv import load_dotenv
from crawler.vnexpress_crawler import crawl_latest_articles
from exporter.pdf_exporter import export_pdf
from integrations.google_drive_uploader import upload_to_drive
from database.db_manager import delete_old_articles # <-- THÊM IMPORT NÀY
from datetime import datetime
import pytz

# Tải các biến môi trường từ file .env
load_dotenv()

# --- CẤU HÌNH ---
# Lấy múi giờ Việt Nam
tz_vietnam = pytz.timezone("Asia/Ho_Chi_Minh") 
# Tạo tên file PDF dựa trên ngày hiện tại
PDF_FILE_PATH = f"data/tin_nong_{datetime.now(tz_vietnam).strftime('%d%m%Y')}.pdf"
# Lấy ID thư mục Drive từ biến môi trường
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")

if __name__ == "__main__":
    
    # BƯỚC 1: DỌN DẸP DATABASE CŨ
    print("--- Bắt đầu dọn dẹp dữ liệu cũ ---")
    delete_old_articles(days_to_keep=30) # Giữ lại dữ liệu trong 30 ngày gần nhất

    # BƯỚC 2: CRAWL DỮ LIỆU MỚI
    new_articles_count = crawl_latest_articles(limit=None)
    
    # BƯỚC 3: XUẤT PDF VÀ UPLOAD NẾU CÓ BÀI MỚI
    if new_articles_count > 0:
        print(f"\n--- Có {new_articles_count} bài viết mới, bắt đầu xuất PDF ---")
        actual_pdf_path = export_pdf(file_path=PDF_FILE_PATH, limit=new_articles_count) # Chỉ xuất các bài vừa crawl

        if actual_pdf_path and os.path.exists(actual_pdf_path):
            if DRIVE_FOLDER_ID:
                print("\n--- Bắt đầu tải lên Google Drive ---")
                upload_to_drive(actual_pdf_path, DRIVE_FOLDER_ID)
            else:
                print("\n⚠️ Bỏ qua tải lên Drive: Biến môi trường DRIVE_FOLDER_ID chưa được cấu hình.")
        else:
            print(f"\n⚠️ Bỏ qua tải lên Drive: File PDF '{actual_pdf_path}' không được tạo.")
    else:
        print("\n--- Không có bài viết mới nào được tìm thấy. Dừng chương trình. ---")
