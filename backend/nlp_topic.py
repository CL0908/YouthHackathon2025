from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Attempt to import NLTK and VADER; fall back gracefully if unavailable.
try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer  # type: ignore
    _VADER_AVAILABLE = True
except Exception:
    nltk = None  # type: ignore
    SentimentIntensityAnalyzer = None  # type: ignore
    _VADER_AVAILABLE = False

TOPIC_KEYWORDS: Dict[str, List[str]] = {
    "education": ["education", "learn", "study", "school", "university", "college", "class", "course", "teacher", "students", "exam", "teach"],
    "technology": ["tech", "technology", "ai", "artificial intelligence", "machine learning", "software", "app", "computer", "robot", "electronics", "gadget"],
    "entertainment": ["music", "movie", "film", "song", "concert", "concert", "tv", "series", "game", "gaming", "show", "celebrity"],
    "news": ["news", "breaking", "headline", "journalist", "report", "article", "press", "media", "update"],
    "sports": ["sport", "football", "soccer", "basketball", "tennis", "match", "team", "goal", "score", "tournament"],
    "science": ["science", "research", "experiment", "laboratory", "scientist", "physics", "chemistry", "biology", "space", "nasa"],
    "health": ["health", "medicine", "medical", "doctor", "patient", "hospital", "wellness", "fitness", "diet"],
    "politics": ["politics", "election", "government", "policy", "senate", "president", "parliament", "vote", "law", "minister"],
    "business": ["business", "startup", "entrepreneur", "economy", "finance", "market", "investment", "stock", "company"],
}

DEFAULT_TOPIC = "other"

@dataclass
class ProcessedPost:
    """Structure for a post after NLP processing."""
    id: str
    ts: str
    platform: str
    author_id: Optional[str]
    is_friend: bool
    text: str
    topic: str
    novelty: float
    negative_score: float
    positive_score: float
    compound_score: float
    # Additional features can be added here if needed.


def load_last30(input_path: Path) -> List[Dict[str, any]]:
    """Load the list of posts from the last30 JSON file.

    Returns an empty list if the file doesn't exist or is unreadable.
    """
    if not input_path.exists():
        return []
    try:
        with input_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def normalize_text(text: str) -> str:
    """Lowercase and strip whitespace from text for easier matching."""
    return text.lower().strip()


def classify_topic(text: str) -> str:
   
    norm = normalize_text(text)
    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw in norm:
                return topic
    return DEFAULT_TOPIC


def compute_novelty(ts_str: str, now: datetime) -> float:
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except Exception:
        # If timestamp parsing fails, treat as old (low novelty)
        return 0.0
    delta = now - ts
    minutes = max(delta.total_seconds() / 60.0, 0.0)
    return 1.0 / (1.0 + minutes)


def get_sentiment_scores(text: str) -> Dict[str, float]:
    
    if not _VADER_AVAILABLE:
        return {"neg": 0.0, "pos": 0.0, "compound": 0.0}
    global _sentiment_analyser  # lazily initialised
    try:
        _sentiment_analyser
    except NameError:
        try:
            nltk.download("vader_lexicon", quiet=True)
        except Exception:
            pass
        _sentiment_analyser = SentimentIntensityAnalyzer()
    try:
        scores = _sentiment_analyser.polarity_scores(text)
        return {"neg": scores.get("neg", 0.0), "pos": scores.get("pos", 0.0), "compound": scores.get("compound", 0.0)}
    except Exception:
        return {"neg": 0.0, "pos": 0.0, "compound": 0.0}


def process_posts(raw_posts: List[Dict[str, any]]) -> List[ProcessedPost]:
    """Apply topic classification and feature extraction to raw posts."""
    results: List[ProcessedPost] = []
    now = datetime.now(timezone.utc)
    for obj in raw_posts:
        # Skip malformed objects
        if not isinstance(obj, dict):
            continue
        text = obj.get("text", "") or ""
        topic = classify_topic(text)
        novelty = compute_novelty(str(obj.get("ts", "")), now)
        is_friend = bool(obj.get("is_friend", False))
        # Sentiment scores are optional; compute for completeness
        sentiments = get_sentiment_scores(text)
        results.append(
            ProcessedPost(
                id=str(obj.get("id", "")),
                ts=str(obj.get("ts", "")),
                platform=str(obj.get("platform", "")),
                author_id=obj.get("author_id"),
                is_friend=is_friend,
                text=text,
                topic=topic,
                novelty=novelty,
                negative_score=sentiments["neg"],
                positive_score=sentiments["pos"],
                compound_score=sentiments["compound"],
            )
        )
    return results


def aggregate_topics(posts: List[ProcessedPost]) -> Dict[str, Dict[str, float]]:
    """Produce a summary of topic counts and percentages."""
    counts: Dict[str, int] = {}
    for p in posts:
        counts[p.topic] = counts.get(p.topic, 0) + 1
    total = float(sum(counts.values()))
    summary: Dict[str, Dict[str, float]] = {}
    for topic, cnt in counts.items():
        summary[topic] = {
            "count": cnt,
            "percent": (cnt / total) * 100.0 if total > 0 else 0.0,
        }
    return summary


def write_outputs(posts: List[ProcessedPost], out_dir: Path) -> None:
    """Write processed posts and summary pie chart data to JSON files."""
    out_dir.mkdir(parents=True, exist_ok=True)
    topics_file = out_dir / "session_topics.json"
    pie_file = out_dir / "piechart.json"
    # Convert dataclass objects to serialisable dicts
    posts_data = [asdict(p) for p in posts]
    with topics_file.open("w", encoding="utf-8") as f:
        json.dump(posts_data, f, ensure_ascii=False, indent=2)
    # Aggregation
    summary = aggregate_topics(posts)
    with pie_file.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Process last30 posts for topics and features.")
    parser.add_argument(
        "--input",
        type=str,
        default=str(Path("data") / "session_last30.json"),
        help="Path to input last30 JSON file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(Path("data")),
        help="Directory to write output JSON files",
    )
    args = parser.parse_args(argv)
    input_path = Path(args.input)
    out_dir = Path(args.output_dir)
    raw_posts = load_last30(input_path)
    if not raw_posts:
        # Create empty outputs if no data
        write_outputs([], out_dir)
        print(f"No input data found at {input_path}. Wrote empty outputs to {out_dir}.")
        return
    processed = process_posts(raw_posts)
    write_outputs(processed, out_dir)
    print(f"Processed {len(processed)} posts. Outputs written to {out_dir}.")


if __name__ == "__main__":
    main()