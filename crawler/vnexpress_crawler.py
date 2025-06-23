import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils.fetcher import fetch_soup
from parsers.vnexpress_parser import parse_article
from database.db_manager import add_article
import time
import random
from datetime import datetime
import pytz

BASE_URL = "https://vnexpress.net"
TIN_NONG_URL = "https://vnexpress.net/tin-nong"

def get_article_links(limit: int = None) -> list:
    """
    Lấy link bài viết mới nhất với chiến lược linh hoạt.
    """
    print(f"Đang tải danh sách bài viết từ: {TIN_NONG_URL}")
    soup = fetch_soup(TIN_NONG_URL)
    if not soup:
        print("❌ Không thể tải trang danh sách bài viết. Dừng crawl.")
        return []
        
    links = []
    target_section = None
    
    # --- CHIẾN LƯỢC ƯU TIÊN #1: TÌM KHỐI CÓ NGÀY HÔM NAY ---
    tz_vietnam = pytz.timezone("Asia/Ho_Chi_Minh")
    today = datetime.now(tz_vietnam)
    today_href_str = f"{today.day}-{today.month}-{today.year}"
    print(f"🔎 [Ưu tiên 1] Đang tìm khối bài viết có href chứa: '{today_href_str}'")

    all_sections = soup.select("div.list-news-subfolder")
    for section in all_sections:
        date_tag = section.select_one("h2.title-sub-folder a")
        if date_tag and date_tag.get('href') and today_href_str in date_tag.get('href'):
            print(f"✅ [Ưu tiên 1] Tìm thấy khối bài viết cho ngày hôm nay.")
            target_section = section
            break
    
    # --- CHIẾN LƯỢC ƯU TIÊN #2: NẾU KHÔNG CÓ, LẤY KHỐI ĐẦU TIÊN ---
    if not target_section and all_sections:
        print(f"⚠️ [Ưu tiên 2] Không tìm thấy khối của ngày hôm nay. Lấy khối bài viết đầu tiên trên trang.")
        target_section = all_sections[0]

    # --- TRÍCH XUẤT LINK TỪ KHỐI ĐÃ CHỌN ---
    if target_section:
        for tag in target_section.select("h3.title-news a[href]"):
            href = tag.get("href")
            if href and (href.startswith("https://vnexpress.net") or href.startswith("/")):
                links.append(urljoin(BASE_URL, href))
    else:
        # --- CHIẾN LƯỢC ƯU TIÊN #3: NẾU VẪN KHÔNG CÓ, LẤY TẤT CẢ LINK ---
        print(f"⚠️ [Ưu tiên 3] Không tìm thấy bất kỳ khối 'list-news-subfolder' nào. Lấy tất cả các link trên trang.")
        for tag in soup.select("h3.title-news a[href]"):
             href = tag.get("href")
             if href and (href.startswith("https://vnexpress.net") or href.startswith("/")):
                links.append(urljoin(BASE_URL, href))

    if not links:
        print("❌ Không thể tìm thấy bất kỳ link bài viết nào bằng mọi chiến lược.")
        return []

    # Loại trùng lặp và giữ nguyên thứ tự
    seen = set()
    unique_links = [x for x in links if not (x in seen or seen.add(x))]

    if limit is not None:
        return unique_links[:limit]

    return unique_links

def crawl_latest_articles(limit: int = None) -> int:
    print("🚀 Bắt đầu quá trình crawl...")
    urls = get_article_links(limit=limit)
    print(f"🔗 Tìm thấy tổng cộng {len(urls)} bài viết để xử lý.")

    if not urls:
        print("--- Không có bài viết nào để xử lý. Dừng lại. ---")
        return 0

    new_count = 0
    for idx, url in enumerate(urls, start=1):
        print(f"\n👉 Đang xử lý bài viết ({idx}/{len(urls)}): {url}")
        article = parse_article(url)
        
        if not article:
            print("❌ Lỗi parse, bỏ qua bài viết này.")
            time.sleep(1)
            continue

        thumb = article.get('image_url') or 'Không có'
        print(f"🏞️ Ảnh thumbnail: {thumb}")

        if add_article(article):
            print(f"✅ Đã lưu bài viết mới: {article['title']}")
            new_count += 1
        else:
            print(f"⏩ Bài viết đã tồn tại, bỏ qua.")

        sleep_time = random.uniform(1, 3)
        print(f"--- Tạm nghỉ {sleep_time:.2f} giây để tránh bị phát hiện ---")
        time.sleep(sleep_time)

    print(f"\n🎉 Hoàn tất! Tổng số bài viết mới được lưu: {new_count}")
    return new_count
