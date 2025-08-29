# YouthHackathon2025

**Bublenz — Youth Media & Information Literacy + Mental Health**

<div align="center"> <img src="assets/bobo.png" alt="Bublenz Logo" width="120" /> <h3>Algorithm Awareness + Media & Information Literacy</h3> <p> Built for <b>UNESCO Youth Hackathon 2025</b> • Empowering youth to <br/> <b>see their algorithm bubble</b>, reflect on their <b>digital diet</b>, and <br/> playfully simulate how feeds are ranked. </p> <a href="#getting-started">Getting Started</a> • <a href="#algorithm">Algorithm</a> • <a href="#roadmap">Roadmap</a> </div>

## 🔥 About the Project

Bublenz is a **mobile-first prototype** designed for youths to explore **algorithmic transparency** and **mental well-being**.  
Instead of punishing screen time, Bublenz allows users to:
- **Track** the content they consume in a 30-minute session (via official APIs or demo ingest).
- **Analyze** each post using lightweight NLP to classify topics (education, tech, entertainment, etc.).
- **Visualize** their “information diet” with a pie chart.
- **Simulate** feed ranking by adjusting sliders (diversity, novelty, friend weight) and see the impact instantly.
- Get non-judgmental **emotional support** from the AI companion **Bobo** and have fun customizing it with **gamification rewards**.


## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Optional API keys: Gemini (for Bobo), Reddit/YouTube/X (for live tracking)
- Basic web browser (frontend is pure HTML/JS)

### 🧰 Installation
```bash
git clone https://github.com/YourUser/YouthHackathon2025.git
cd YouthHackathon2025
pip install -r requirements.txt
```
# Running a Demo (no APIs)
# Prepare a demo_posts.json with sample posts (see docs for format)
```bash
python backend/tracker.py demo --file demo_posts.json
python backend/nlp_topic.py
```

# Open the visualization:
```bash
open frontend/piechart.html
open frontend/sim.html
```
#Live Tracking via API (Example: Reddit)
```bash
export REDDIT_CLIENT_ID=...
export REDDIT_CLIENT_SECRET=...
export REDDIT_USERNAME=...
export REDDIT_PASSWORD=...
python backend/tracker.py api --provider reddit
python backend/nlp_topic.py
open frontend/piechart.html
```
#Starting Bobo Chat (Optional)
```bash
export GOOGLE_API_KEY=...
python backend/bubblechat.py serve --port 5050
# Then open frontend/chat.html
```

## Algorithm

1. Data Collection
tracker.py collects posts via social media APIs or local ingest.
Stores an append-only log (session_raw.jsonl) and maintains a rolling 30-minute buffer (session_last30.json).

2. NLP Topic Analysis
nlp_topic.py tokenizes post text and assigns a topic (education, tech, entertainment, news, sports, science, health, politics, business, other).
Computes novelty = 1 / (1 + hours since post) and friend indicator (0/1).
Optional: computes sentiment for context but does not affect the pie chart.
Outputs per-post features (session_topics.json) and aggregated counts (piechart.json).

3. Visualization & Simulation
piechart.html reads piechart.json and renders the topic mix as a pie chart.
sim.html reads session_topics.json and re-ranks the last 30-minute posts based on sliders (diversity, novelty, friend and per-topic weights).

4. Emotional Support & Gamification
bubblechat.py proxies Gemini (Bobo) with a custom prompt focused on algorithm awareness and well-being.
Gamified tasks reward BubbleCoins which unlock cosmetic items for Bobo.

### 🤝 Contributors
Huge thanks to these wonderful people for making Bublenz possible!
Name	       Role	        Contribution
Contributor   1	  |Full-Stack Dev	Backend & NLP
Contributor   2	  |AI/ML Engineer	Topic Classifier & Gemini prompt
Contributor   3	  |Frontend Designer	UI/UX & Simulation
Contributor   4	  |Project Lead	Architecture & Documentation
