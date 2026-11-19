import html
import sqlite3
import tkinter as tk                    # вбудована бібліотека для вікон
import webbrowser                       # відкрити посилання в браузері
from tkinter import ttk, messagebox     # ttk — сучасні віджети, messagebox — спливаючі вікна

from api import search_videos, get_video_stats, YouTubeAPIError
from db import get_connection, init_db, save_videos, get_saved_videos
from main import format_number          # безпечно: main() у main.py не запуститься при імпорті


class App(tk.Tk):
    """Головне вікно застосунку."""

    def __init__(self):
        super().__init__()
        self.title("YouTube Search App")
        self.geometry("900x500")

        # --- Верхній рядок: поле запиту і кнопки ---
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Запит:").pack(side="left")
        self.query_var = tk.StringVar()                      # змінна, пов'язана з полем вводу
        entry = ttk.Entry(top, textvariable=self.query_var, width=40)
        entry.pack(side="left", padx=5)
        entry.bind("<Return>", lambda event: self.search())  # Enter теж запускає пошук

        ttk.Button(top, text="Шукати", command=self.search).pack(side="left")
        ttk.Button(top, text="Показати збережене", command=self.show_saved).pack(side="left", padx=5)

        # --- Таблиця результатів ---
        columns = ("channel", "title", "views", "likes", "date")
        self.table = ttk.Treeview(self, columns=columns, show="headings")
        headings = {"channel": "Канал", "title": "Назва", "views": "Перегляди", "likes": "Лайки", "date": "Дата"}
        widths = {"channel": 160, "title": 400, "views": 100, "likes": 80, "date": 90}
        for col in columns:
            self.table.heading(col, text=headings[col])
            self.table.column(col, width=widths[col], anchor="w")
        self.table.pack(fill="both", expand=True, padx=10)
        self.table.bind("<Double-1>", self.open_video)       # подвійний клік відкриває відео

        # --- Рядок стану внизу ---
        self.status = ttk.Label(self, text="Введи запит і натисни «Шукати»", padding=10)
        self.status.pack(fill="x")

    def fill_table(self, rows):
        """Очищає таблицю і заповнює новими рядками."""
        self.table.delete(*self.table.get_children())
        for video_id, channel, title, views, likes, date in rows:
            self.table.insert(
                "", "end",
                iid=video_id,       # id рядка = videoId, щоб знати, яке відео відкривати
                values=(channel, title, format_number(views), format_number(likes), date[:10]),
            )

    def search(self):
        """Кнопка «Шукати»: два запити до API, таблиця і збереження в базу."""
        query = self.query_var.get().strip()
        if not query:
            messagebox.showwarning("Порожній запит", "Введи хоча б одне слово.")
            return

        self.status.config(text="Шукаю...")
        self.update_idletasks()            # одразу перемалювати вікно, щоб було видно «Шукаю...»

        try:
            videos = search_videos(query)
            if not videos:
                self.fill_table([])
                self.status.config(text="За цим запитом нічого не знайдено.")
                return
            stats = get_video_stats([item["id"]["videoId"] for item in videos])
        except YouTubeAPIError as error:
            messagebox.showerror("Помилка API", str(error))     # ті самі повідомлення, що й у консолі
            self.status.config(text="Помилка запиту.")
            return

        rows = []
        for item in videos:
            snippet = item["snippet"]
            video_id = item["id"]["videoId"]
            video_stats = stats.get(video_id, {})
            rows.append((
                video_id, snippet["channelTitle"], html.unescape(snippet["title"]),
                video_stats.get("views"), video_stats.get("likes"), snippet["publishedAt"],
            ))
        self.fill_table(rows)

        conn = get_connection()
        try:
            init_db(conn)
            new_count = save_videos(conn, videos, stats)
            self.status.config(text=f"Знайдено: {len(videos)}. Нових у базі: {new_count}. Подвійний клік відкриває відео.")
        except sqlite3.Error as error:
            messagebox.showerror("Помилка бази даних", str(error))
        finally:
            conn.close()

    def show_saved(self):
        """Кнопка «Показати збережене»: усе з бази через JOIN."""
        conn = get_connection()
        try:
            init_db(conn)
            saved = get_saved_videos(conn)
        except sqlite3.Error as error:
            messagebox.showerror("Помилка бази даних", str(error))
            return
        finally:
            conn.close()

        # get_saved_videos повертає (канал, назва, дата, id, перегляди, лайки),
        # тож переставляємо поля в порядок, який чекає fill_table
        rows = [(video_id, channel, title, views, likes, date)
                for channel, title, date, video_id, views, likes in saved]
        self.fill_table(rows)
        self.status.config(text=f"У базі: {len(rows)} відео.")

    def open_video(self, event):
        """Подвійний клік по рядку: відкрити відео в браузері."""
        video_id = self.table.focus()       # id виділеного рядка = videoId
        if video_id:
            webbrowser.open(f"https://www.youtube.com/watch?v={video_id}")


if __name__ == "__main__":
    App().mainloop()     # mainloop — нескінченний цикл, що чекає на кліки й натискання