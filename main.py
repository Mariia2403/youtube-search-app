import html
import sqlite3
from api import search_videos, YouTubeAPIError
from db import get_connection, init_db, save_videos, get_saved_videos


def print_videos(videos):
    """Друкує список відео з API."""
    for number, item in enumerate(videos, start=1):
        title = html.unescape(item["snippet"]["title"])
        channel = item["snippet"]["channelTitle"]
        video_id = item["id"]["videoId"]
        print(f"{number}. {title}")
        print(f"   Канал: {channel}")
        print(f"   https://www.youtube.com/watch?v={video_id}")


def search_and_save():
    """Пункт меню 1: пошук на YouTube і збереження в базу."""
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
        new_count = save_videos(conn, videos)
        print(f"\nНових відео збережено: {new_count}. Уже були в базі: {len(videos) - new_count}.")
    except sqlite3.Error as error:
        print(f"Помилка бази даних: {error}")
    finally:
        conn.close()


def show_saved():
    """Пункт меню 2: вивід усього, що збережено в базі."""
    conn = get_connection()
    try:
        init_db(conn)                     # якщо бази ще немає, створимо порожні таблиці
        rows = get_saved_videos(conn)
    except sqlite3.Error as error:
        print(f"Помилка бази даних: {error}")
        return
    finally:
        conn.close()

    if not rows:
        print("У базі ще немає відео. Спершу виконай пошук (пункт 1).")
        return

    current_channel = None
    for channel, title, published_at, video_id in rows:   # розпаковуємо кортеж на 4 змінні
        if channel != current_channel:     # почався новий канал, тож друкуємо його назву
            print(f"\n📺 {channel}")
            current_channel = channel
        date = published_at[:10]           # "2025-02-12T12:30:31Z" → "2025-02-12"
        print(f"   {date}  {title}")

    channels_count = len({row[0] for row in rows})   # множина унікальних назв каналів
    print(f"\nУсього: {len(rows)} відео з {channels_count} каналів.")


def main():
    """Головне меню: працює, доки користувач не обере 0."""
    while True:                            # нескінченний цикл, вихід лише через break
        print("\n1 — Шукати відео на YouTube")
        print("2 — Показати збережені відео")
        print("0 — Вихід")
        choice = input("Обери дію: ").strip()

        if choice == "1":
            search_and_save()
        elif choice == "2":
            show_saved()
        elif choice == "0":
            print("До зустрічі!")
            break                          # вийти з циклу, і програма завершиться
        else:
            print("Немає такого пункту. Введи 1, 2 або 0.")


if __name__ == "__main__":
    main()