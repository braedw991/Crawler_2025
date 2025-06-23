# database/db_manager.py
import json
import os
import sqlite3
from typing import List, Dict

# Thay đổi đường dẫn sang file database SQLite
DB_PATH = "data/database.db"

def create_connection():
    """Tạo kết nối đến file database SQLite"""
    conn = None
    try:
        # Đảm bảo thư mục 'data' tồn tại
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        # Giúp trả về kết quả dạng dictionary thay vì tuple
        conn.row_factory = sqlite3.Row 
    except sqlite3.Error as e:
        print(f"❌ Lỗi khi kết nối tới database: {e}")
    return conn

def create_table():
    """Tạo bảng 'articles' nếu nó chưa tồn tại"""
    conn = create_connection()
    if conn is not None:
        try:
            sql_create_articles_table = """ CREATE TABLE IF NOT EXISTS articles (
                                                url TEXT PRIMARY KEY,
                                                title TEXT NOT NULL,
                                                summary TEXT,
                                                created_at TEXT NOT NULL,
                                                image_url TEXT
                                            ); """
            cur = conn.cursor()
            cur.execute(sql_create_articles_table)
            conn.commit()
        except sqlite3.Error as e:
            print(f"❌ Lỗi khi tạo bảng: {e}")
        finally:
            conn.close()

def add_article(article: Dict) -> bool:
    """Thêm một bài viết mới vào database. Trả về True nếu thêm thành công."""
    conn = create_connection()
    if conn is not None:
        # Dùng INSERT OR IGNORE, nếu URL đã tồn tại, nó sẽ bỏ qua và không báo lỗi
        sql = ''' INSERT OR IGNORE INTO articles(url,title,summary,created_at,image_url)
                  VALUES(?,?,?,?,?) '''
        try:
            cur = conn.cursor()
            cur.execute(sql, (
                article['url'],
                article['title'],
                article['summary'],
                article['created_at'],
                article.get('image_url', '') # Dùng .get để an toàn nếu không có key
            ))
            conn.commit()
            # cur.rowcount sẽ trả về 1 nếu insert thành công, 0 nếu bỏ qua
            return cur.rowcount > 0
        except sqlite3.Error as e:
            print(f"❌ Lỗi khi thêm bài viết: {e}")
            return False
        finally:
            conn.close()
    return False

def get_all_articles(limit: int = None) -> List[Dict]:
    """Lấy tất cả bài viết từ database, có thể giới hạn số lượng."""
    conn = create_connection()
    articles = []
    if conn is not None:
        try:
            sql = "SELECT * FROM articles ORDER BY created_at DESC"
            if limit:
                sql += f" LIMIT {limit}"
            
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            # Chuyển đổi các đối tượng Row thành dictionary
            articles = [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"❌ Lỗi khi lấy bài viết: {e}")
        finally:
            conn.close()
    return articles

def delete_old_articles(days_to_keep: int):
    """Xóa các bài viết cũ hơn số ngày chỉ định."""
    conn = create_connection()
    if conn is not None:
        try:
            # SQLite có thể so sánh trực tiếp chuỗi ISO 8601
            # date('now', '-X days') sẽ tạo ra ngày giới hạn
            sql = "DELETE FROM articles WHERE created_at < date('now', ?)"
            param = f'-{days_to_keep} days'
            
            cur = conn.cursor()
            cur.execute(sql, (param,))
            conn.commit()
            
            deleted_rows = cur.rowcount
            if deleted_rows > 0:
                print(f"🧹 Đã dọn dẹp và xóa {deleted_rows} bài viết cũ.")
            else:
                print("🧹 Không có bài viết cũ nào cần dọn dẹp.")
                
        except sqlite3.Error as e:
            print(f"❌ Lỗi khi dọn dẹp database: {e}")
        finally:
            conn.close()

# --- KHỞI TẠO DATABASE KHI MODULE ĐƯỢC IMPORT ---
# Đảm bảo bảng luôn tồn tại khi chương trình chạy
create_table()
