# utils/fetcher.py
import time
import random
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def fetch_soup(url: str, referer: str = None) -> BeautifulSoup:
    """
    Tải và parse HTML từ một URL sử dụng trình duyệt không đầu Playwright.
    Hàm này sẽ thực thi JavaScript và trả về HTML cuối cùng.
    Nó cũng hỗ trợ giả mạo header 'Referer'.
    """
    try:
        with sync_playwright() as p:
            # Sử dụng trình duyệt Chromium (giống Chrome)
            # headless=True có nghĩa là chạy ngầm, không hiện cửa sổ trình duyệt
            browser = p.chromium.launch(headless=True) 
            page = browser.new_page()
            
            print(f"🚀 Playwright đang mở trang: {url}")
            
            # Đi đến trang, chờ cho đến khi nội dung HTML được tải (thay vì chờ mạng yên tĩnh)
            # Tăng timeout lên 60 giây để an toàn hơn
            page.goto(url, wait_until="domcontentloaded", timeout=60000, referer=referer)
            
            # Chờ thêm một chút để đảm bảo các script cuối cùng đã chạy
            time.sleep(random.uniform(1, 2))
            
            # Lấy nội dung HTML sau khi đã thực thi JavaScript
            content = page.content()
            
            browser.close()
            
            return BeautifulSoup(content, "html.parser")

    except Exception as e:
        print(f"❌ Lỗi khi fetch bằng Playwright tại URL {url}: {e}")
        return None
