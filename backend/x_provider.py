import os, requests
from datetime import datetime, timezone
from typing import List, Dict

API = "https://api.twitter.com/2"

def _iso(s):  # ensure ISO format
    return datetime.fromisoformat(s.replace("Z","+00:00")).astimezone(timezone.utc).isoformat()

class XProvider:
    name = "x"
    def __init__(self):
        self.bearer = os.environ["X_BEARER_TOKEN"]
        self.headers = {"Authorization": f"Bearer {self.bearer}"}

    def fetch_recent(self, since_ts: str) -> List[Dict]:
        # Example: search recent tweets (needs Elevated/Academic/paid access)
        q = "lang:en -is:retweet"
        params = {
            "query": q,
            "max_results": 50,
            "tweet.fields": "created_at,author_id,lang",
            "start_time": since_ts  # ISO timestamp
        }
        r = requests.get(API + "/tweets/search/recent", headers=self.headers, params=params, timeout=20)
        r.raise_for_status()
        out: List[Dict] = []
        for tw in r.json().get("data", []):
            out.append({
                "id": tw["id"],
                "ts": _iso(tw["created_at"]),
                "platform": "x",
                "author_id": tw["author_id"],
                "is_friend": None,
                "text": tw.get("text",""),
                "topic_hint": None,
                "media_meta": {"lang": tw.get("lang")}
            })
        return out
