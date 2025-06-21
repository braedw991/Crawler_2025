from utils.fetcher import fetch_soup
from utils.summarizer import summarize_with_gemini
from datetime import datetime
import pytz
import time

def parse_created_at(raw: str):
    """
    Xử lý định dạng ngày VnExpress:
    - 'Thứ sáu, 14/6/2025, 13:06 (GMT+7)'
    - 'Thứ sáu, 14/6/2025 (GMT+7)'
    - '14/6/2025'
    """
    try:
        tz = pytz.timezone("Asia/Ho_Chi_Minh")
        parts = raw.strip().split(",")
        if len(parts) >= 3:
            date_part = parts[1].strip()
            time_part = parts[2].strip().split(" ")[0]
            dt = datetime.strptime(f"{date_part}, {time_part}", "%d/%m/%Y, %H:%M")
        elif len(parts) >= 2:
            date_part = parts[1].strip()
            dt = datetime.strptime(date_part, "%d/%m/%Y")
        else:
            dt = datetime.strptime(parts[0].strip(), "%d/%m/%Y")
        return tz.localize(dt)
    except Exception as e:
        print(f"[Lỗi định dạng thời gian] {e}")
        return datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))

def is_valid_image_url(url: str) -> bool:
    """Loại bỏ ảnh base64 hoặc placeholder không dùng được"""
    return bool(url and url.startswith("http") and not url.startswith("data:image/"))

def extract_image_url(img_tag) -> str:
    """Trích xuất URL hợp lệ từ thẻ ảnh, ưu tiên các thuộc tính lazy-load."""
    if not img_tag:
        return None
        
    # Ưu tiên các thuộc tính lazy-loading
    for attr in ["data-src", "data-original", "data-srcset", "src"]:
        candidate = img_tag.get(attr)
        # data-srcset có thể chứa nhiều URL, lấy cái đầu tiên
        if candidate:
            first_url = candidate.strip().split(',')[0].split(' ')[0]
            if is_valid_image_url(first_url):
                return first_url
    return None

def parse_article(url: str) -> dict:
    # --- THÊM REFERER ĐỂ GIẢ LẬP HÀNH VI NGƯỜI DÙNG ---
    # Giả vờ rằng chúng ta đến từ trang tin nóng
    referer_url = "https://vnexpress.net/tin-nong"
    soup = fetch_soup(url, referer=referer_url)
    
    if soup is None:
        print(f"[❌ Lỗi fetch bài] {url}")
        return None

    # 1. Tiêu đề
    title_tag = soup.find("h1", class_="title-detail")
    title = title_tag.get_text(strip=True) if title_tag else "Không có tiêu đề"

    # 2. Nội dung bài viết
    content_tag = soup.find("article", class_="fck_detail")
    if not content_tag:
        print(f"[❌ Không tìm thấy nội dung] {url}")
        return None
    paragraphs = content_tag.find_all("p")
    content = "\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

    # 3. Tóm tắt bằng Gemini
    summary = summarize_with_gemini(content)
    # Thêm độ trễ sau mỗi lần gọi API để tránh bị giới hạn
    time.sleep(2)

    # 4. Thời gian xuất bản
    created_at = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
    time_tag = soup.find("span", class_="date")
    if time_tag:
        raw_time = time_tag.get_text(strip=True)
        created_at = parse_created_at(raw_time)

    # 5. Thumbnail image (Cải tiến logic)
    image_url = ""
    # 5a. Ưu tiên thẻ meta og:image vì nó là chuẩn nhất
    og_image_tag = soup.select_one('meta[property="og:image"]')
    if og_image_tag and is_valid_image_url(og_image_tag.get('content')):
        image_url = og_image_tag['content']
    
    # 5b. Nếu không có, tìm ảnh thumbnail chính của bài viết
    if not image_url:
        thumb_tag = soup.select_one('div.thumb-art picture img, figure.fig-picture picture img')
        image_url = extract_image_url(thumb_tag)

    # 5c. Nếu vẫn không có, lấy ảnh đầu tiên trong nội dung
    if not image_url:
        first_content_img_tag = content_tag.select_one('img')
        image_url = extract_image_url(first_content_img_tag)

    return {
        "url": url,
        "title": title,
        "summary": summary,
        "created_at": created_at.isoformat(),
        "image_url": image_url if image_url else ""
    }
