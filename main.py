from crawler.vnexpress_crawler import crawl_latest_articles
from exporter.pdf_exporter import export_pdf

DEBUG_MODE = True        # 👉 Bật True khi test, False khi chạy thật

if __name__ == "__main__":
    if DEBUG_MODE:
        crawl_latest_articles(limit=5)     # chỉ crawl 5 bài khi test
        export_pdf(limit=5)                # chỉ xuất 5 bài ra PDF
    else:
        crawl_latest_articles()             # crawl đầy đủ
        export_pdf()                        # xuất toàn bộ bài
