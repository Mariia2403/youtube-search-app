import os                        
import requests                  
from dotenv import load_dotenv  

load_dotenv()                                 
API_KEY = os.getenv("YOUTUBE_API_KEY")         
SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"   


def search_videos(query, max_results=5):
    """Шукає відео на YouTube і повертає список результатів (items)."""
    params = {                  
        "part": "snippet",      
        "q": query,             
        "type": "video",         
        "maxResults": max_results,
        "key": API_KEY,         
    }
    response = requests.get(SEARCH_URL, params=params, timeout=10)  
    data = response.json()      
    return data["items"]        