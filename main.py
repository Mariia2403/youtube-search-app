import html
import sqlite3
from api import search_videos, get_video_stats, YouTubeAPIError
from db import get_connection, init_db, save_videos, get_saved_videos


def format_number(n):
    """8188531 → '8 188 531'; None → '—'."""
    if n is None:
        return "—"
    return f"{n:,}".replace(",", " ")   # :, ставить коми між тисячами, а ми міняємо їх на пробіли


def print_videos(videos, stats):
    """Друкує список відео з API разом зі статистикою."""
    for number, item in enumerate(videos, start=1):
        title = html.unescape(item["snippet"]["title"])
        channel = item["snippet"]["channelTitle"]
        video_id = item["id"]["videoId"]
        video_stats = stats.get(video_id, {})
        print(f"{number}. {title}")
        print(f"   Канал: {channel}")
        print(f"   Переглядів: {format_number(video_stats.get('views'))} · Лайків: {format_number(video_stats.get('likes'))}")
        print(f"   https://www.youtube.com/watch?v={video_id}")


def search_and_save():
    """Пункт меню 1: два запити до API (пошук + статистика) і збереження."""
    query = input("Що шукаємо на YouTube? ").strip()
    if not query:
        print("Запит порожній. Введи хоча б одне слово.")
        return

    try:
        videos = search_videos(query)                               # запит 1
        if not videos:
            print("За цим запитом нічого не знайдено.")
            return
        video_ids = [item["id"]["videoId"] for item in videos]      # результат запиту 1...
        stats = get_video_stats(video_ids)                          # ...стає параметром запиту 2
    except YouTubeAPIError as error:
        print(error)
        return

    print_videos(videos, stats)

    conn = get_connection()
    try:
        init_db(conn)
        new_count = save_videos(conn, videos, stats)
        print(f"\nНових відео збережено: {new_count}. Уже були в базі: {len(videos) - new_count}.")
    except sqlite3.Error as error:
        print(f"Помилка бази даних: {error}")
    finally:
        conn.close()


def show_saved():
    """Пункт меню 2: вивід усього, що збережено в базі."""
    conn = get_connection()
    try:
        init_db(conn)
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
    for channel, title, published_at, video_id, views, likes in rows:
        if channel != current_channel:
            print(f"\n📺 {channel}")
            current_channel = channel
        print(f"   {published_at[:10]}  {title}  ({format_number(views)} переглядів)")

    channels_count = len({row[0] for row in rows})
    print(f"\nУсього: {len(rows)} відео з {channels_count} каналів.")


def main():
    """Головне меню: працює, доки користувач не обере 0."""
    while True:
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
            break
        else:
            print("Немає такого пункту. Введи 1, 2 або 0.")


if __name__ == "__main__":
    main()