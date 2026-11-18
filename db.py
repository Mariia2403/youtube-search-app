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


if __name__ == "__main__":
    conn = get_connection()
    init_db(conn)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()
    print("Таблиці в базі:", tables)
    conn.close()