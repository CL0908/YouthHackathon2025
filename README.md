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

### Installation
```bash
git clone https://github.com/YourUser/YouthHackathon2025.git
cd YouthHackathon2025
pip install -r requirements.txt  # includes Flask, requests, nltk (optional)

Running a Demo (no APIs)
# Prepare a demo_posts.json with sample posts (see docs for format)
python backend/tracker.py demo --file demo_posts.json
python backend/nlp_topic.py
# Open the visualization:
open frontend/piechart.html
open frontend/sim.html
Live Tracking via API (Example: Reddit)
export REDDIT_CLIENT_ID=...
export REDDIT_CLIENT_SECRET=...
export REDDIT_USERNAME=...
export REDDIT_PASSWORD=...
python backend/tracker.py api --provider reddit
python backend/nlp_topic.py
open frontend/piechart.html
Ingest Server for Custom Input
python backend/tracker.py ingest --port 7070
# POST JSON with {id, platform, author_id, is_friend, text} to http://localhost:7070/ingest
Starting Bobo Chat (Optional)
export GOOGLE_API_KEY=...
python backend/bubblechat.py serve --port 5050
# Then open frontend/chat.html
