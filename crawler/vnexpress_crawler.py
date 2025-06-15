import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.vnexpress_parser import parse_article
from database.db_manager import add_article

BASE_URL = "https://vnexpress.net"
TIN_NONG_URL = "https://vnexpress.net/tin-nong"

def get_article_links(limit: int = None) -> list:
    response = requests.get(TIN_NONG_URL, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    links = []

    for tag in soup.select("h3.title-news a[href]"):
        href = tag.get("href")
        if href.startswith("https://vnexpress.net") or href.startswith("/"):
            full_url = urljoin(BASE_URL, href)
            links.append(full_url)

    # Loại trùng + giữ thứ tự
    seen = set()
    unique_links = []
    for link in links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)

    if limit is not None:
        return unique_links[:limit]

    return unique_links

def crawl_latest_articles(limit: int = None):
    print("🚀 Đang crawl danh sách bài viết từ mục Tin Nóng...")
    urls = get_article_links(limit=limit)
    print(f"🔗 Tìm được {len(urls)} bài viết")

    new_count = 0
    for idx, url in enumerate(urls, start=1):
        print(f"👉 ({idx}/{len(urls)}) {url}")
        article = parse_article(url)
        if not article:
            print("❌ Lỗi parse, bỏ qua\n")
            continue

        # In ra URL ảnh thumbnail (nếu có)
        thumb = article.get('thumbnail') or 'Không có'
        print(f"🏞️ Ảnh thumbnail: {thumb}")

        if article:
            if add_article(article):
                print(f"✅ Lưu bài mới: {article['title']}")
                new_count += 1
            else:
                print(f"⏩ Đã tồn tại: {article['title']}")

    print(f"\n🎉 Tổng số bài mới được lưu: {new_count}")
