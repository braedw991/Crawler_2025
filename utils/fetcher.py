# utils/fetcher.py
import requests
from bs4 import BeautifulSoup

def fetch_html(url: str) -> str:
    """
    Tải nội dung HTML của bài viết từ URL
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[Fetch Error] {e}")
        return ""

def fetch_soup(url: str) -> BeautifulSoup:
    """
    Trả về BeautifulSoup đã parse HTML
    """
    html = fetch_html(url)
    return BeautifulSoup(html, "html.parser") if html else None
