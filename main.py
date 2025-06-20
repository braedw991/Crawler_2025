from crawler.vnexpress_crawler import crawl_latest_articles
from exporter.pdf_exporter import export_pdf
from integrations.google_drive_uploader import upload_to_drive
import os
from datetime import datetime

# --- CẤU HÌNH ---
DEBUG_MODE = True        # 👉 Bật True khi test, False khi chạy thật

# Tạo tên file PDF động theo ngày hiện tại (ví dụ: tin_nong_20062025.pdf)
today_str = datetime.now().strftime("%d%m%Y")
PDF_FILE_PATH = f"data/tin_nong_{today_str}.pdf"

# 👉 ID thư mục Google Drive của bạn
DRIVE_FOLDER_ID = "1KzQX1QZUoGdfmkvoqlDHg2pRyJAPDVNO" 

if __name__ == "__main__":
    # Xác định số lượng bài viết cần xử lý dựa trên DEBUG_MODE
    limit = 5 if DEBUG_MODE else None

    # --- BƯỚC 1: CRAWL DỮ LIỆU ---
    crawl_latest_articles(limit=limit)
    
    # --- BƯỚC 2: XUẤT FILE PDF ---
    # Hàm export_pdf sẽ trả về đường dẫn file thực tế đã được tạo
    actual_pdf_path = export_pdf(file_path=PDF_FILE_PATH, limit=limit)

    # --- BƯỚC 3: TẢI FILE PDF LÊN GOOGLE DRIVE ---
    if actual_pdf_path and os.path.exists(actual_pdf_path):
        if DRIVE_FOLDER_ID and DRIVE_FOLDER_ID != "YOUR_GOOGLE_DRIVE_FOLDER_ID_HERE":
            print("\n--- Bắt đầu tải lên Google Drive ---")
            upload_to_drive(actual_pdf_path, DRIVE_FOLDER_ID)
        else:
            print("\n⚠️ Bỏ qua tải lên Drive: Chưa cấu hình DRIVE_FOLDER_ID.")
    else:
        print(f"\n⚠️ Bỏ qua tải lên Drive: File PDF '{actual_pdf_path}' không được tạo hoặc không tồn tại.")
