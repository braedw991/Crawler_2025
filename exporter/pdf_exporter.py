from fpdf import FPDF
from database.db_manager import load_articles
from datetime import datetime
import os
import requests
from io import BytesIO
from PIL import Image
import shutil  # Dùng để xoá thư mục tạm sau khi tạo PDF

FONT_PATH_REGULAR = "assets/fonts/DejaVuSans.ttf"
FONT_PATH_BOLD = "assets/fonts/DejaVuSans-Bold.ttf"
TEMP_DIR = "temp"

def is_valid_image_url(url: str) -> bool:
    """Loại bỏ ảnh base64 hoặc URL không hợp lệ"""
    return bool(url and url.startswith("http"))

class PDFNews(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(15, 15, 15)
        self.add_font("DejaVu", "", FONT_PATH_REGULAR, uni=True)
        self.add_font("DejaVu", "B", FONT_PATH_BOLD, uni=True)

    def header(self):
        self.set_font("DejaVu", "B", 14)
        self.cell(0, 10, "TIN NÓNG VNEXPRESS", border=0, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "", 8)
        self.cell(0, 10, f"Trang {self.page_no()}", 0, 0, "C")

def export_pdf(file_path="data/tin_nong.pdf", limit=None):
    articles = load_articles()
    articles = sorted(articles, key=lambda x: x["created_at"], reverse=True)
    if limit:
        articles = articles[:limit]

    os.makedirs(TEMP_DIR, exist_ok=True)
    pdf = PDFNews()
    pdf.add_page()

    for i, art in enumerate(articles, start=1):
        created = datetime.fromisoformat(art["created_at"]).strftime("%d/%m/%Y %H:%M")
        image_url = art.get("image_url", "")
        has_image = is_valid_image_url(image_url)

        # Tính chiều cao ảnh dự kiến (nếu có)
        img_path = None
        display_height = 0
        if has_image:
            try:
                response = requests.get(image_url, timeout=5)
                img = Image.open(BytesIO(response.content)).convert("RGB")
                page_width = pdf.w - pdf.l_margin - pdf.r_margin
                aspect_ratio = img.height / img.width
                display_height = page_width * aspect_ratio
                img_path = os.path.join(TEMP_DIR, f"img_{i}.jpg")
                img.save(img_path, format="JPEG")
            except Exception as e:
                print(f"[Ảnh lỗi] {e}")
                has_image = False

        # Ước lượng tổng chiều cao cần thiết cho toàn block
        estimated_block = 40 + (display_height if has_image else 0)
        if pdf.get_y() + estimated_block > pdf.h - pdf.b_margin:
            pdf.add_page()

        # Tiêu đề
        pdf.set_font("DejaVu", "B", 12)
        pdf.multi_cell(0, 8, f"{i}. {art['title']}")
        pdf.ln(1)

        # Ảnh minh họa
        if has_image and img_path:
            try:
                pdf.image(img_path, x=pdf.l_margin, w=page_width)
                os.remove(img_path)
                pdf.ln(2)
            except Exception as e:
                print(f"[Chèn ảnh lỗi] {e}")

        # Tóm tắt
        pdf.set_font("DejaVu", "", 11)
        pdf.multi_cell(0, 7, f"Tóm tắt: {art['summary']}")
        pdf.ln(1)

        # Link
        pdf.set_text_color(0, 0, 255)
        pdf.set_font("DejaVu", "", 11)
        pdf.multi_cell(0, 6, art["url"], link=art["url"])
        pdf.ln(1)

        # Thời gian
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("DejaVu", "", 10)
        pdf.cell(0, 5, f"Thời gian: {created}")
        pdf.ln(10)

    pdf.output(file_path)
    print(f"📄 Đã tạo file PDF: {file_path}")

    # Xoá temp/ sau khi chèn ảnh xong
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    print(f"🧹 Đã xoá thư mục tạm: {TEMP_DIR}")
