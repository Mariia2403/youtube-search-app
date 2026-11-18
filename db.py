import html
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "youtube.db")



def get_connection():
    """Відкриває з'єднання з базою і вмикає перевірку FK."""
    conn = sqlite3.connect(DB_PATH)          
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn):
    """Створює таблиці, якщо їх ще немає."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS channels (
            id    TEXT PRIMARY KEY,          -- id каналу від YouTube (natural key)
            title TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS videos (
            id           TEXT PRIMARY KEY,   -- videoId від YouTube
            title        TEXT NOT NULL,
            published_at TEXT,               -- дата публікації (може бути відсутня)
            channel_id   TEXT NOT NULL REFERENCES channels(id)   -- FK → channels.id
        );
    """)

def save_videos(conn, items):
    """Зберігає відео та канали. Повертає кількість НОВИХ відео."""
    before = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]   

    with conn:
        for item in items:
            snippet = item["snippet"]
            conn.execute(
                """
                INSERT INTO channels (id, title) VALUES (?, ?)
                ON CONFLICT (id) DO UPDATE SET title = excluded.title
                """,
                (snippet["channelId"], snippet["channelTitle"]),
            )
            conn.execute(
                """
                INSERT INTO videos (id, title, published_at, channel_id) VALUES (?, ?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET title = excluded.title
                """,
                (
                    item["id"]["videoId"],
                    html.unescape(snippet["title"]),
                    snippet["publishedAt"],
                    snippet["channelId"],
                ),
            )

    after = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]   
    return after - before                                                

if __name__ == "__main__":
    conn = get_connection()
    init_db(conn)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()
    print("Таблиці в базі:", tables)
    conn.close()