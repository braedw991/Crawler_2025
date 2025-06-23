from fpdf import FPDF
from database.db_manager import get_all_articles # <-- THAY ĐỔI QUAN TRỌNG
from datetime import datetime
import pytz
import os
import requests
from PIL import Image
import io
import shutil
import unicodedata

FONT_PATH_REGULAR = "assets/fonts/DejaVuSans.ttf"
FONT_PATH_BOLD = "assets/fonts/DejaVuSans-Bold.ttf"
TEMP_DIR = "temp"

# Màu sắc
COLOR_HEADER = (25, 118, 210)       # Xanh đậm
COLOR_HEADER_BAND = (25, 118, 210)  # Màu nền band header
COLOR_TITLE = (33, 150, 243)        # Xanh nhạt hơn (dùng cho tiêu đề bài)
COLOR_LINK = (48, 63, 159)          # Xanh tím than
COLOR_BG_SUMMARY = (240, 247, 255)  # Xanh rất nhạt
COLOR_TEXT = (33, 33, 33)           # Gần đen
COLOR_FOOTER = (117, 117, 117)      # Xám

def is_valid_image_url(url: str) -> bool:
    return bool(url and url.startswith("http"))

def strip_accents(s: str) -> str:
    if not s:
        return s
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))

class PDF(FPDF):
    def header(self):
        self.set_font('DejaVu', 'B', 15)
        title = f"TIN NÓNG VNEXPRESS - NGÀY {datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%d/%m/%Y')}"
        self.cell(0, 10, title, 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('DejaVu', '', 8)
        self.cell(0, 10, f'Trang {self.page_no()}/{{nb}}', 0, 0, 'C')

def add_image_from_url(pdf, url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content))
        
        page_width = pdf.w - 2 * pdf.l_margin
        
        # Giữ tỷ lệ ảnh
        w, h = img.size
        aspect_ratio = h / w
        img_width = page_width
        img_height = page_width * aspect_ratio
        
        # Lưu ảnh tạm thời để FPDF đọc
        temp_img_path = os.path.join("data", "temp_thumb.jpg")
        img.save(temp_img_path)
        
        pdf.image(temp_img_path, x=pdf.get_x(), w=img_width, h=img_height)
        pdf.ln(img_height + 5) # Thêm khoảng trống sau ảnh
        os.remove(temp_img_path) # Xóa ảnh tạm
    except Exception as e:
        print(f"🖼️ Lỗi khi tải ảnh thumbnail: {e}")

def export_pdf(file_path: str, limit: int = None):
    """
    Xuất các bài viết từ database ra file PDF.
    """
    # --- THAY ĐỔI: LẤY DỮ LIỆU TRỰC TIẾP TỪ DATABASE ---
    print("📄 Đang lấy dữ liệu từ database để xuất PDF...")
    articles = get_all_articles(limit=limit)
    
    if not articles:
        print("⚠️ Không có bài viết nào trong database để xuất PDF.")
        return None

    pdf = PDF('P', 'mm', 'A4')
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font('DejaVu', '', 'assets/fonts/DejaVuSans.ttf', uni=True)
    pdf.add_font('DejaVu', 'B', 'assets/fonts/DejaVuSans-Bold.ttf', uni=True)

    for article in articles:
        pdf.add_page()
        
        if article.get('image_url'):
            add_image_from_url(pdf, article['image_url'])

        pdf.set_font('DejaVu', 'B', 16)
        pdf.multi_cell(0, 10, article['title'])
        pdf.ln(5)

        pdf.set_font('DejaVu', '', 12)
        pdf.multi_cell(0, 8, article['summary'])
        pdf.ln(5)

        pdf.set_font('DejaVu', '', 10)
        pdf.set_text_color(0, 0, 255)
        pdf.cell(0, 10, f"Nguồn: {article['url']}", link=article['url'])
        pdf.ln(5)
        pdf.set_text_color(0, 0, 0)

    pdf.output(file_path)
    print(f"✅ Đã tạo file PDF thành công tại: {file_path}")
    return file_path

# Nếu chạy trực tiếp
if __name__ == "__main__":
    # Tạo tên file động khi chạy trực tiếp file này
    today_str = datetime.now().strftime("%d%m%Y")
    default_filename = f"data/tin_nong_{today_str}.pdf"
    export_pdf(default_filename, limit=5)
