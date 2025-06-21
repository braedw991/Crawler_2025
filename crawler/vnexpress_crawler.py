import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils.fetcher import fetch_soup # <-- Sử dụng fetcher tập trung
from parsers.vnexpress_parser import parse_article
from database.db_manager import add_article
import time
import random

BASE_URL = "https://vnexpress.net"
TIN_NONG_URL = "https://vnexpress.net/tin-nong"

def get_article_links(limit: int = None) -> list:
    # Sử dụng fetch_soup để có User-Agent ngẫu nhiên
    print(f"Đang tải danh sách bài viết từ: {TIN_NONG_URL}")
    soup = fetch_soup(TIN_NONG_URL)
    if not soup:
        print("❌ Không thể tải trang danh sách bài viết. Dừng crawl.")
        return []
        
    links = []
    for tag in soup.select("h3.title-news a[href]"):
        href = tag.get("href")
        if href and (href.startswith("https://vnexpress.net") or href.startswith("/")):
            full_url = urljoin(BASE_URL, href)
            links.append(full_url)

    # Loại trùng lặp và giữ nguyên thứ tự
    seen = set()
    unique_links = [x for x in links if not (x in seen or seen.add(x))]

    if limit is not None:
        return unique_links[:limit]

    return unique_links

def crawl_latest_articles(limit: int = None):
    print("🚀 Bắt đầu quá trình crawl...")
    urls = get_article_links(limit=limit)
    print(f"🔗 Tìm thấy tổng cộng {len(urls)} bài viết để xử lý.")

    new_count = 0
    for idx, url in enumerate(urls, start=1):
        print(f"\n👉 Đang xử lý bài viết ({idx}/{len(urls)}): {url}")
        article = parse_article(url)
        
        if not article:
            print("❌ Lỗi parse, bỏ qua bài viết này.")
            # Thêm độ trễ ngắn ngay cả khi lỗi để tránh dồn dập request
            time.sleep(1)
            continue

        # Sửa lại key cho đúng với dữ liệu trả về từ parser
        thumb = article.get('image_url') or 'Không có'
        print(f"🏞️ Ảnh thumbnail: {thumb}")

        if add_article(article):
            print(f"✅ Đã lưu bài viết mới: {article['title']}")
            new_count += 1
        else:
            print(f"⏩ Bài viết đã tồn tại, bỏ qua.")

        # --- THÊM ĐỘ TRỄ NGẪU NHIÊN ĐỂ TRÁNH BỊ BLOCK ---
        # Chờ từ 1 đến 3 giây trước khi crawl bài tiếp theo
        sleep_time = random.uniform(1, 3)
        print(f"--- Tạm nghỉ {sleep_time:.2f} giây để tránh bị phát hiện ---")
        time.sleep(sleep_time)

    print(f"\n🎉 Hoàn tất! Tổng số bài viết mới được lưu: {new_count}")
