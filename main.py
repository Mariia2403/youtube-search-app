import html                      
from api import search_videos    

query = input("Що шукаємо на YouTube? ")
videos = search_videos(query)

for number, item in enumerate(videos, start=1):   
    title = html.unescape(item["snippet"]["title"])
    channel = item["snippet"]["channelTitle"]
    video_id = item["id"]["videoId"]

    print(f"{number}. {title}")
    print(f"   Канал: {channel}")
    print(f"   https://www.youtube.com/watch?v={video_id}")   