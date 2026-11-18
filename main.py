import html
import sqlite3
from api import search_videos, YouTubeAPIError
from db import get_connection, init_db, save_videos


def print_videos(videos):
    """Друкує список відео з API."""
    for number, item in enumerate(videos, start=1):
        title = html.unescape(item["snippet"]["title"])
        channel = item["snippet"]["channelTitle"]
        video_id = item["id"]["videoId"]
        print(f"{number}. {title}")
        print(f"   Канал: {channel}")
        print(f"   https://www.youtube.com/watch?v={video_id}")


def main():
    query = input("Що шукаємо на YouTube? ").strip()
    if not query:
        print("Запит порожній. Введи хоча б одне слово.")
        return

    try:
        videos = search_videos(query)
    except YouTubeAPIError as error:
        print(error)
        return

    if not videos:
        print("За цим запитом нічого не знайдено.")
        return

    print_videos(videos)

    conn = get_connection()
    try:
        init_db(conn)                          
        saved = save_videos(conn, videos)
        print(f"\nЗбережено в базу: {saved} відео.")
    except sqlite3.Error as error:             
        print(f"Помилка бази даних: {error}")
    finally:
        conn.close()                           


if __name__ == "__main__":
    main()