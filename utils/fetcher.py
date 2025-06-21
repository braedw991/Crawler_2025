# utils/fetcher.py
import time
import random
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import requests

# Không cần User-Agent hay Session nữa, Playwright sẽ quản lý tất cả

def fetch_soup_playwright(url: str) -> BeautifulSoup:
    """
    Tải và parse HTML từ một URL sử dụng trình duyệt không đầu Playwright.
    Hàm này sẽ thực thi JavaScript và trả về HTML cuối cùng.
    """
    try:
        with sync_playwright() as p:
            # Sử dụng trình duyệt Chromium (giống Chrome)
            browser = p.chromium.launch(headless=True) 
            page = browser.new_page()
            
            print(f"🚀 Playwright đang mở trang: {url}")
            # Đi đến trang, chờ cho đến khi mạng không còn hoạt động (tức là đã tải xong)
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Chờ thêm một chút để đảm bảo các script cuối cùng đã chạy
            time.sleep(random.uniform(1, 2))
            
            # Lấy nội dung HTML sau khi đã thực thi JavaScript
            content = page.content()
            
            browser.close()
            
            return BeautifulSoup(content, "html.parser")

    except Exception as e:
        print(f"❌ Lỗi khi fetch bằng Playwright tại URL {url}: {e}")
        return None

def get_full_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        # Header Client Hints, rất quan trọng để trông giống Chrome thật
        'Sec-CH-UA': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        'Sec-CH-UA-Mobile': '?0',
        'Sec-CH-UA-Platform': '"Windows"',
    }

# Bạn có thể giữ lại hàm fetch_soup cũ dùng requests để dùng cho các trang đơn giản
# và chỉ gọi fetch_soup_playwright cho các trang phức tạp.

def fetch_soup(url: str) -> BeautifulSoup:
    """
    Tải và parse HTML từ một URL sử dụng requests.
    Hàm này chỉ nên được sử dụng cho các trang web đơn giản, không yêu cầu JavaScript.
    """
    try:
        session = requests.Session()
        response = session.get(url, headers=get_full_headers(), timeout=10)
        response.raise_for_status()  # Kiểm tra mã trạng thái HTTP
        
        return BeautifulSoup(response.text, "html.parser")

    except Exception as e:
        print(f"❌ Lỗi khi fetch bằng requests tại URL {url}: {e}")
        return None
