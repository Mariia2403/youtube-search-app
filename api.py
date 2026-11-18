import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


class YouTubeAPIError(Exception):
    """Наш власний тип помилки: все, що пішло не так при роботі з YouTube."""
   


def search_videos(query, max_results=5):
    """Шукає відео на YouTube. Повертає список items або кидає YouTubeAPIError."""

    
    if not API_KEY:
        raise YouTubeAPIError("Не задано YOUTUBE_API_KEY. Створи файл .env за зразком .env.example")
       

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": API_KEY,
    }


    try:
        response = requests.get(SEARCH_URL, params=params, timeout=10)
    except requests.exceptions.Timeout:          # Timeout ПЕРШИМ: він конкретніший (пам'ятаєш блок 2?)
        raise YouTubeAPIError("YouTube не відповідає. Спробуй пізніше.")
    except requests.exceptions.ConnectionError:  # немає інтернету або сервер недоступний
        raise YouTubeAPIError("Немає з'єднання з інтернетом.")

    
    if response.status_code != 200:
        raise YouTubeAPIError(_error_message(response))

    
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        raise YouTubeAPIError("YouTube повернув відповідь не у форматі JSON.")

    return data.get("items", [])


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