import html
from api import search_videos, YouTubeAPIError


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

    for number, item in enumerate(videos, start=1):
        title = html.unescape(item["snippet"]["title"])
        channel = item["snippet"]["channelTitle"]
        video_id = item["id"]["videoId"]
        print(f"{number}. {title}")
        print(f"   Канал: {channel}")
        print(f"   https://www.youtube.com/watch?v={video_id}")


if __name__ == "__main__":
    main()