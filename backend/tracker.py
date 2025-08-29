from __future__ import annotations
import argparse, json, os, requests, threading, time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

RAW_PATH = Path("data/session_raw.jsonl")
LAST30_PATH = Path("data/session_last30.json")
DATA_DIR = RAW_PATH.parent; DATA_DIR.mkdir(parents=True, exist_ok=True)

WINDOW_MINUTES = 30
API = "https://oauth.reddit.com"
OAUTH = "https://www.reddit.com/api/v1/access_token"

# ---------- utils ----------
def now_utc() -> datetime: return datetime.now(timezone.utc)
def iso(dt: datetime) -> str: return dt.astimezone(timezone.utc).isoformat()
def parse_iso(s: str) -> datetime: return datetime.fromisoformat(s.replace("Z", "+00:00"))
def _iso_unix(ts_utc: int) -> str:  # fix: used by RedditProvider
    return datetime.fromtimestamp(ts_utc, tz=timezone.utc).isoformat()

# ---------- data model ----------
@dataclass
class PostEvent:
    id: str
    ts: str
    platform: str
    author_id: str | None = None
    is_friend: bool | None = None
    text: str = ""
    topic_hint: str | None = None
    media_meta: Dict[str, Any] | None = None

# ---------- 30-min window ----------
class Last30Window:
    def __init__(self, minutes: int = WINDOW_MINUTES):
        self.minutes = minutes
        self._lock = threading.Lock()
        self.events: List[PostEvent] = []
    def add(self, ev: PostEvent):
        with self._lock:
            self.events.append(ev); self._prune_locked()
    def _prune_locked(self):
        cutoff = now_utc() - timedelta(minutes=self.minutes)
        self.events = [e for e in self.events if parse_iso(e.ts) >= cutoff]
    def prune(self):
        with self._lock: self._prune_locked()
    def snapshot(self) -> List[Dict[str, Any]]:
        with self._lock:
            self._prune_locked()
            return [asdict(e) for e in self.events]

WINDOW = Last30Window()

# ---------- persistence ----------
def append_raw(ev: PostEvent):
    with RAW_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(ev), ensure_ascii=False) + "\n")
def export_last30() -> List[Dict[str, Any]]:
    data = WINDOW.snapshot()
    with LAST30_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data
def rebuild_window_from_raw():
    WINDOW.events.clear()
    if not RAW_PATH.exists(): return
    cutoff = now_utc() - timedelta(minutes=WINDOW_MINUTES)
    with RAW_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            obj = json.loads(line)
            try: ts = parse_iso(obj.get("ts"))
            except Exception: continue
            if ts >= cutoff:
                WINDOW.add(PostEvent(**obj))

# ---------- providers ----------
class RedditProvider:
    name = "reddit"
    def __init__(self):
        self.client_id = os.environ["REDDIT_CLIENT_ID"]
        self.secret = os.environ["REDDIT_CLIENT_SECRET"]
        self.username = os.environ["REDDIT_USERNAME"]
        self.password = os.environ["REDDIT_PASSWORD"]
        self.user_agent = "bublenz-tracker/0.1"
        auth = requests.auth.HTTPBasicAuth(self.client_id, self.secret)
        data = {"grant_type": "password", "username": self.username, "password": self.password}
        headers = {"User-Agent": self.user_agent}
        r = requests.post(OAUTH, auth=auth, data=data, headers=headers, timeout=20)
        r.raise_for_status()
        self.token = r.json()["access_token"]
        self.headers = {"Authorization": f"bearer {self.token}", "User-Agent": self.user_agent}
    def fetch_recent(self, since_ts: str) -> List[Dict]:
        out: List[Dict] = []
        for path in ["/best", "/r/all/new"]:
            r = requests.get(API + path, headers=self.headers, params={"limit": 50}, timeout=20)
            r.raise_for_status()
            for it in r.json()["data"]["children"]:
                d = it["data"]
                out.append({
                    "id": d["id"],
                    "ts": _iso_unix(int(d["created_utc"])),
                    "platform": "reddit",
                    "author_id": d.get("author"),
                    "is_friend": None,
                    "text": (d.get("title","") + "\n" + d.get("selftext","")).strip(),
                    "topic_hint": None,
                    "media_meta": {"subreddit": d.get("subreddit")}
                })
            time.sleep(0.8)
        return out

PROVIDERS = {"reddit": RedditProvider}

# ---------- demo loader (kept) ----------
def run_demo_pull(demo_path: str, platform: str = "demo"):
    with open(demo_path, "r", encoding="utf-8") as f:
        posts = json.load(f)
    for obj in posts:
        ev = PostEvent(
            id=str(obj.get("id")),
            ts=obj.get("ts") or iso(now_utc()),
            platform=platform,
            author_id=obj.get("author_id"),
            is_friend=bool(obj.get("is_friend")) if obj.get("is_friend") is not None else None,
            text=obj.get("text",""),
            topic_hint=obj.get("topic_hint"),
            media_meta=obj.get("media_meta"),
        )
        append_raw(ev); WINDOW.add(ev)
    exported = export_last30()
    print(f"[demo] loaded {len(posts)} → exported {len(exported)} to {LAST30_PATH}")

# ---------- ingest server (unchanged) ----------
def run_ingest_server(host: str = "127.0.0.1", port: int = 7070):
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    app = Flask(__name__); CORS(app, resources={r"/*": {"origins": ["*", "null"]}})
    @app.route("/health", methods=["GET"])
    def health(): return jsonify({"ok": True, "window_count": len(WINDOW.snapshot())})
    @app.route("/ingest", methods=["POST"])
    def ingest():
        obj = (request.get_json(silent=True) or {})
        ev = PostEvent(
            id=str(obj.get("id") or f"loc_{int(time.time()*1000)}"),
            ts=iso(now_utc()),
            platform=str(obj.get("platform") or "local"),
            author_id=obj.get("author_id"),
            is_friend=bool(obj.get("is_friend")) if obj.get("is_friend") is not None else None,
            text=obj.get("text") or "",
            topic_hint=obj.get("topic_hint"),
            media_meta=obj.get("media_meta"),
        )
        append_raw(ev); WINDOW.add(ev); export_last30()
        return jsonify({"ok": True, "stored": asdict(ev)})
    @app.route("/last30", methods=["GET"])
    def last30():
        return app.response_class(
            response=json.dumps(WINDOW.snapshot(), ensure_ascii=False, indent=2),
            mimetype="application/json")
    def pruner():
        while True:
            WINDOW.prune(); export_last30(); time.sleep(20)
    threading.Thread(target=pruner, daemon=True).start()
    print(f"* Ingest server on http://{host}:{port}")
    app.run(host=host, port=port, debug=False)

# ---------- CLI ----------
def main():
    p = argparse.ArgumentParser(description="Bublenz tracker")
    sub = p.add_subparsers(dest="cmd", required=True)

    demo = sub.add_parser("demo", help="Load posts from demo JSON file")
    demo.add_argument("--file", required=True)
    demo.add_argument("--platform", default="demo")

    api = sub.add_parser("api", help="Fetch from real provider (e.g., reddit)")
    api.add_argument("--provider", required=True, choices=PROVIDERS.keys())
    api.add_argument("--since", help="ISO start time; default = now-30m")

    ing = sub.add_parser("ingest", help="Start local server to receive POST /ingest")
    ing.add_argument("--host", default="127.0.0.1")
    ing.add_argument("--port", type=int, default=7070)

    exp = sub.add_parser("export", help="Rebuild last30 from existing raw file")

    args = p.parse_args()

    if args.cmd == "demo":
        run_demo_pull(args.file, platform=args.platform)

    elif args.cmd == "api":
        since = args.since or (now_utc() - timedelta(minutes=30)).isoformat()
        provider = PROVIDERS[args.provider]()
        posts = provider.fetch_recent(since_ts=since)
        for obj in posts:
            ev = PostEvent(
                id=str(obj["id"]),
                ts=obj["ts"],
                platform=obj.get("platform", args.provider),
                author_id=obj.get("author_id"),
                is_friend=obj.get("is_friend"),
                text=obj.get("text",""),
                topic_hint=obj.get("topic_hint"),
                media_meta=obj.get("media_meta"),
            )
            append_raw(ev); WINDOW.add(ev)
        export_last30()
        print(f"[api-{args.provider}] got {len(posts)} → exported last30.json")

    elif args.cmd == "ingest":
        rebuild_window_from_raw()
        run_ingest_server(args.host, args.port)

    elif args.cmd == "export":
        rebuild_window_from_raw()
        exported = export_last30()
        print(f"[export] last30 → {LAST30_PATH} ({len(exported)} posts)")

if __name__ == "__main__":
    main()
