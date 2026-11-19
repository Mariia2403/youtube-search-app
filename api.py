import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"


class YouTubeAPIError(Exception):
    """Наш власний тип помилки: все, що пішло не так при роботі з YouTube."""


def _get(url, params):
    """Спільний GET-запит до YouTube API з обробкою всіх помилок.
    Повертає розібраний JSON або кидає YouTubeAPIError."""
    if not API_KEY:
        raise YouTubeAPIError("Не задано YOUTUBE_API_KEY. Створи файл .env за зразком .env.example")

    params = {**params, "key": API_KEY}
    # {**params, ...} створює НОВИЙ словник: копія params + ключ.
    # Оригінальний словник того, хто викликав, ми не змінюємо.

    try:
        response = requests.get(url, params=params, timeout=10)
    except requests.exceptions.Timeout:
        raise YouTubeAPIError("YouTube не відповідає. Спробуй пізніше.")
    except requests.exceptions.ConnectionError:
        raise YouTubeAPIError("Немає з'єднання з інтернетом.")

    if response.status_code != 200:
        raise YouTubeAPIError(_error_message(response))

    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        raise YouTubeAPIError("YouTube повернув відповідь не у форматі JSON.")


def search_videos(query, max_results=5):
    """Запит 1: шукає відео. Повертає список items."""
    data = _get(SEARCH_URL, {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
    })
    return data.get("items", [])


def get_video_stats(video_ids):
    """Запит 2: статистика для списку id.
    Повертає словник {videoId: {"views": int, "likes": int або None}}."""
    if not video_ids:                      # немає id, тож немає чого запитувати
        return {}

    data = _get(VIDEOS_URL, {
        "part": "statistics",
        "id": ",".join(video_ids),         # ["a", "b", "c"] → "a,b,c"
    })

    stats = {}
    for item in data.get("items", []):
        s = item.get("statistics", {})
        stats[item["id"]] = {
            "views": int(s.get("viewCount", 0)),                        # рядок → число
            "likes": int(s["likeCount"]) if "likeCount" in s else None, # лайки можуть бути приховані
        }
    return stats


def _error_message(response):
    """Складає зрозуміле повідомлення за статусом відповіді."""
    code = response.status_code
    try:
        details = response.json()["error"]["message"]
    except (ValueError, KeyError):
        details = response.text[:200]

    if code == 400:
        hint = "Некоректний запит або неправильний ключ API."
    elif code == 403:
        hint = "Доступ заборонено: вичерпано денну квоту або API не увімкнено."
    elif code >= 500:
        hint = "Проблема на боці YouTube. Спробуй пізніше."
    else:
        hint = "Неочікувана помилка."

    return f"Помилка {code}: {hint}\nДеталі від YouTube: {details}"