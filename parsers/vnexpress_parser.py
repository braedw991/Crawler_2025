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
    """Trích xuất URL hợp lệ từ thẻ ảnh"""
    for attr in ["src", "data-src", "data-original", "data-srcset"]:
        candidate = img_tag.get(attr)
        if is_valid_image_url(candidate):
            return candidate
    return None

def parse_article(url: str) -> dict:
    soup = fetch_soup(url)
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
    time.sleep(2)  # tránh rate limit

    # 4. Thời gian xuất bản
    created_at = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
    time_tag = soup.find("span", class_="date")
    if time_tag:
        raw_time = time_tag.get_text(strip=True)
        created_at = parse_created_at(raw_time)

    # 5. Thumbnail image
    image_url = None
    # 5a. Ưu tiên og:image
    og = soup.select_one('meta[property="og:image"]')
    if og and og.get('content'):
        image_url = og['content']
    else:
        # 5b. fallback thumbnail (nếu parse chung với listing)
        thumb = soup.select_one('div.thumb-art picture img')
        if thumb and thumb.get('src'):
            image_url = thumb['src']
        else:
            # 5c. fallback lấy ảnh đầu tiên trong nội dung bài
            content_img = soup.select_one('article.fck_detail img')
            if content_img and content_img.get('src'):
                image_url = content_img['src']

    return {
        "url": url,
        "title": title,
        "summary": summary,
        "created_at": created_at.isoformat(),
        "image_url": image_url
    }
