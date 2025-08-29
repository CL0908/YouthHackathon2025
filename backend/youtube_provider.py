import os, requests
from datetime import datetime, timezone, timedelta
from typing import List, Dict

API = "https://www.googleapis.com/youtube/v3/search"

def _iso(dt): return dt.astimezone(timezone.utc).isoformat()

class YouTubeProvider:
    name = "youtube"
    def __init__(self):
        self.key = os.environ["YOUTUBE_API_KEY"]

    def fetch_recent(self, since_ts: str) -> List[Dict]:
        # Example: pull from a few topics/channels; adjust q or channelId as needed
        published_after = since_ts
        out: List[Dict] = []
        for q in ["education", "technology", "music", "news"]:
            params = {
                "part": "snippet",
                "type": "video",
                "order": "date",
                "q": q,
                "maxResults": 20,
                "publishedAfter": published_after,
                "key": self.key
            }
            r = requests.get(API, params=params, timeout=20)
            r.raise_for_status()
            for item in r.json().get("items", []):
                sn = item["snippet"]
                out.append({
                    "id": item["id"]["videoId"],
                    "ts": sn["publishedAt"],  # already ISO
                    "platform": "youtube",
                    "author_id": sn.get("channelId"),
                    "is_friend": None,
                    "text": sn.get("title","") + "\n" + sn.get("description",""),
                    "topic_hint": q,  # optional seed
                    "media_meta": {"channelTitle": sn.get("channelTitle")}
                })
        return out
