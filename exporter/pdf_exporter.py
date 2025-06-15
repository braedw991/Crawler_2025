from fpdf import FPDF
from database.db_manager import load_articles
from datetime import datetime
import os
import requests
from io import BytesIO
from PIL import Image
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

class PDFNews(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(15, 15, 15)
        # Thêm font Unicode
        self.add_font("DejaVu", "", FONT_PATH_REGULAR, uni=True)
        self.add_font("DejaVu", "B", FONT_PATH_BOLD, uni=True)
        
        # Metadata PDF
        self.set_title("Tổng hợp tin nóng VnExpress")
        self.set_author("Crawler_2025")
        self.set_creator("Python FPDF")

    def header(self):
        # Vẽ band header
        band_height = 20
        self.set_fill_color(*COLOR_HEADER_BAND)
        # Vẽ full-width band từ y=0 đến band_height
        self.rect(0, 0, self.w, band_height, style='F')

        # In tiêu đề lên band
        self.set_y(3)
        self.set_font("DejaVu", "B", 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "TIN NÓNG VNEXPRESS", border=0, ln=1, align="C")

        # In ngày báo cáo
        today = datetime.now().strftime("%d/%m/%Y")
        self.set_font("DejaVu", "", 9)
        self.set_text_color(245, 245, 245)
        self.cell(0, 5, f"Báo cáo ngày: {today}", border=0, ln=1, align="C")

        # Khoảng cách và đường phân tách
        self.ln(3)
        self.set_draw_color(*COLOR_HEADER)
        self.set_line_width(0.5)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(5)
        # Reset màu text cho nội dung
        self.set_text_color(*COLOR_TEXT)

        # Vẽ border nhẹ quanh trang, bắt đầu dưới header band
        offset_top = 5  # khoảng cách từ đáy band đến viền
        y_border = band_height + offset_top
        total_h = self.h
        bottom_margin = 5
        height_border = total_h - y_border - bottom_margin
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.1)
        self.rect(5, y_border, self.w - 10, height_border)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(*COLOR_FOOTER)
        self.cell(0, 10, f"Trang {self.page_no()} | Dữ liệu từ VnExpress.net", 0, 0, "C")
    
    def add_link_button(self, url, text="Xem chi tiết"):
        x, y = self.get_x(), self.get_y()
        width, height = 40, 10
        self.set_fill_color(*COLOR_LINK)
        self.set_draw_color(*COLOR_LINK)
        self.rect(x, y, width, height, style="F")
        self.set_text_color(255, 255, 255)
        self.set_font("DejaVu", "B", 9)
        self.cell(width, height, text, 0, 0, "C", link=url)
        self.set_text_color(*COLOR_TEXT)

def export_pdf(file_path="data/tin_nong.pdf", limit=None):
    articles = load_articles()
    articles = sorted(articles, key=lambda x: x.get("created_at", ""), reverse=True)
    if limit:
        articles = articles[:limit]

    os.makedirs(TEMP_DIR, exist_ok=True)
    dir_pdf = os.path.dirname(file_path)
    if dir_pdf:
        os.makedirs(dir_pdf, exist_ok=True)

    def build_pdf(strip_unicode=False):
        pdf = PDFNews()
        for i, art in enumerate(articles, start=1):
            pdf.add_page()
            # Thông tin bài viết
            created_raw = art.get("created_at", "")
            try:
                created = datetime.fromisoformat(created_raw).strftime("%d/%m/%Y %H:%M")
            except Exception:
                created = created_raw
            title = art.get("title", "")
            summary_text = art.get("summary", "").strip()
            url = art.get("url", "")
            image_url = art.get("image_url", "")
            has_image = is_valid_image_url(image_url)

            if strip_unicode:
                title = strip_accents(title)
                summary_text = strip_accents(summary_text)
            # Tiêu đề bài
            pdf.set_font("DejaVu", "B", 14)
            pdf.set_text_color(*COLOR_TITLE)
            pdf.multi_cell(0, 8, f"{i}. {title}")
            # Đường kẻ nhỏ dưới tiêu đề
            pdf.ln(2)
            pdf.set_draw_color(*COLOR_TITLE)
            pdf.set_line_width(0.3)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(5)
            # Thời gian
            pdf.set_text_color(*COLOR_TEXT)
            pdf.set_font("DejaVu", "", 11)
            pdf.cell(0, 5, f"Thời gian: {created}")
            pdf.ln(8)
            # Ảnh minh họa
            if has_image:
                try:
                    response = requests.get(image_url, timeout=5)
                    img = Image.open(BytesIO(response.content)).convert("RGB")
                    page_width = pdf.w - pdf.l_margin - pdf.r_margin - 20
                    aspect_ratio = img.height / img.width
                    display_height = page_width * aspect_ratio
                    img_path = os.path.join(TEMP_DIR, f"img_{i}.jpg")
                    img.save(img_path, format="JPEG")
                    x = pdf.l_margin + 10
                    pdf.set_draw_color(200, 200, 200)
                    pdf.set_line_width(0.3)
                    pdf.rect(x, pdf.get_y(), page_width, display_height)
                    pdf.image(img_path, x=x, y=pdf.get_y(), w=page_width)
                    pdf.ln(display_height + 10)
                    os.remove(img_path)
                except Exception as e:
                    print(f"[Ảnh lỗi] {e}")
                    has_image = False
            # Tóm tắt với nền
            pdf.set_font("DejaVu", "B", 11)
            pdf.set_text_color(*COLOR_TEXT)
            pdf.cell(0, 7, "Tóm tắt:", 0, 1)
            pdf.set_font("DejaVu", "", 11)
            if summary_text:
                start_y = pdf.get_y()
                tmp_lines = pdf.multi_cell(0, 7, summary_text, align="L", split_only=True)
                text_height = len(tmp_lines) * 7
                pdf.set_y(start_y)
                pdf.set_fill_color(*COLOR_BG_SUMMARY)
                pdf.rect(pdf.l_margin, start_y, pdf.w - pdf.l_margin - pdf.r_margin, text_height, style="F")
                pdf.multi_cell(0, 7, summary_text)
                pdf.ln(5)
            # Link
            pdf.add_link_button(url)
            pdf.ln(15)
        return pdf

    # Thử build & xuất bình thường
    pdf = build_pdf(strip_unicode=False)
    try:
        pdf.output(file_path)
        print(f"📄 Đã tạo file PDF: {file_path}")
    except UnicodeEncodeError as ue:
        print(f"⚠️ UnicodeEncodeError: {ue}. Thử strip dấu tiếng Việt rồi xuất ASCII.")
        pdf = build_pdf(strip_unicode=True)
        base, ext = os.path.splitext(file_path)
        fallback_path = f"{base}_ascii{ext}"
        try:
            pdf.output(fallback_path)
            print(f"📄 Đã tạo file PDF fallback (ASCII): {fallback_path}")
        except Exception as e2:
            print(f"❌ Lỗi khi xuất PDF fallback: {e2}")
    except PermissionError:
        timestamp = datetime.now().strftime("%H%M%S")
        base_dir = os.path.dirname(file_path)
        base_name = os.path.basename(file_path)
        name, ext = os.path.splitext(base_name)
        new_file_path = os.path.join(base_dir, f"{name}_{timestamp}{ext}")
        try:
            pdf.output(new_file_path)
            print(f"📄 Đã tạo file PDF: {new_file_path}")
        except Exception as e3:
            print(f"❌ Lỗi khi xuất file PDF mới: {e3}")

    # Xóa thư mục tạm
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    print(f"🧹 Đã xoá thư mục tạm: {TEMP_DIR}")

# Nếu chạy trực tiếp
if __name__ == "__main__":
    export_pdf("data/tin_nong.pdf", limit=5)
