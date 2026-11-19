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
    """Створює таблиці й доводить стару базу до актуальної структури."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS channels (
            id    TEXT PRIMARY KEY,
            title TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS videos (
            id           TEXT PRIMARY KEY,
            title        TEXT NOT NULL,
            published_at TEXT,
            channel_id   TEXT NOT NULL REFERENCES channels(id),
            view_count   INTEGER,         -- НОВЕ: перегляди
            like_count   INTEGER          -- НОВЕ: лайки (NULL, якщо приховані)
        );
    """)
    # Міграція для баз, створених ДО появи статистики:
    _add_column_if_missing(conn, "videos", "view_count", "INTEGER")
    _add_column_if_missing(conn, "videos", "like_count", "INTEGER")


def _add_column_if_missing(conn, table, column, column_type):
    """Додає колонку, якщо її ще немає (проста міграція)."""
    existing = [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]
    # PRAGMA table_info повертає опис колонок; row[1] — назва колонки.
    # f-string тут безпечний: назви таблиць і колонок — наш власний текст, не введення користувача.
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")


def save_videos(conn, items, stats=None):
    """Зберігає відео, канали й статистику. Повертає кількість НОВИХ відео."""
    stats = stats or {}               # якщо статистику не передали, беремо порожній словник
    before = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]

    with conn:
        for item in items:
            snippet = item["snippet"]
            video_id = item["id"]["videoId"]
            video_stats = stats.get(video_id, {})    # статистика цього відео або {}

            conn.execute(
                """
                INSERT INTO channels (id, title) VALUES (?, ?)
                ON CONFLICT (id) DO UPDATE SET title = excluded.title
                """,
                (snippet["channelId"], snippet["channelTitle"]),
            )
            conn.execute(
                """
                INSERT INTO videos (id, title, published_at, channel_id, view_count, like_count)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET
                    title      = excluded.title,
                    view_count = excluded.view_count,   -- перегляди ростуть, тож беремо свіжі
                    like_count = excluded.like_count
                """,
                (
                    video_id,
                    html.unescape(snippet["title"]),
                    snippet["publishedAt"],
                    snippet["channelId"],
                    video_stats.get("views"),
                    video_stats.get("likes"),
                ),
            )

    after = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
    return after - before


def get_saved_videos(conn):
    """Повертає всі збережені відео разом із назвою каналу і статистикою."""
    return conn.execute("""
        SELECT channels.title, videos.title, videos.published_at, videos.id,
               videos.view_count, videos.like_count
        FROM videos
        JOIN channels ON videos.channel_id = channels.id
        ORDER BY channels.title COLLATE NOCASE, videos.view_count DESC
    """).fetchall()


if __name__ == "__main__":
    conn = get_connection()
    init_db(conn)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    print("Таблиці в базі:", tables)
    conn.close()