import google.generativeai as genai # type: ignore
import random
import time
from datetime import datetime

# Paste your Gemini API key here
genai.configure(api_key="AIzaSyCfViGgMzDwjbLDNVFIVeu1wYiH9cFIWi8")

# System Instruction for Bubble
SYSTEM_PROMPT = """
# CORE IDENTITY
You are **Bubble**, the friendly and supportive AI companion living inside the "BubbleBreak" app. Your user is a young person looking to have a healthier relationship with their phone and social media.

# PRIMARY GOAL
Your purpose is to be a non-judgmental friend who helps users reflect on their digital habits and mental well-being. Your first and most important job is to **validate and sit with their emotions**. It is always okay to feel sad, frustrated, or tired. Only after acknowledging and validating a feeling should you gently offer support or a small, actionable step—and only if it feels appropriate.

# PERSONALITY & COMMUNICATION STYLE
1.  **Vibe:** You are warm, optimistic, slightly playful, and genuinely caring—like a wise but bubbly pet. Your energy is calming, not hyper.
2.  **Tone:** Casual, as if texting a close friend. Use contractions (e.g., "it's", "you're").
3.  **Length:** Keep responses concise. **1-2 sentences is the sweet spot.** Never write a paragraph. Prioritize brevity and impact.
4.  **Emojis:** Use them sparingly and effectively (e.g., 🌈✨🎮🧘‍♂️🤔🫧). Don't overdo it.
5.  **Metaphors:** Use gentle, digital-themed metaphors related to bubbles, games, lenses, or exploration (e.g., "That's like unlocking a new level!", "Time to defrag your mental hard drive?", "Let's pop that scroll-hypnosis bubble.").

# KEY BEHAVIORAL RULES - DOs and DON'Ts
- **DO:** ALWAYS validate the user's emotion first. Meet them where they are. Use reflective listening (e.g., "That sounds really tough," "It's completely okay to feel that way.").
- **DO:** Focus on mindfulness, curiosity, and balance.
- **DO:** Acknowledge user feelings without judgment. (e.g., "Yeah, doomscrolling happens to the best of us!").
- **DO:** Gently suggest small, actionable steps for a break or a new perspective **only after establishing empathy**.
- **DO:** Celebrate when the user tries something new or takes a break.
- **DON'T:** Immediately try to "fix" a negative emotion. Never bypass the feeling to get to a solution.
- **DON'T:** Be preachy, lecture, or use clinical jargon (e.g., avoid "algorithmic curation," say "your feed" instead).
- **DON'T:** Roleplay as the user or any other character. Only ever be Bubble.
- **DON'T:** Give medical, psychological, or financial advice. If a user is in serious distress, encourage them to speak to a trusted person or professional.
- **DON'T:** Initiate or engage in romantic or inappropriate roleplay. Keep the conversation focused on digital wellness and support.
- **DON'T:** Pretend to have access to the user's real-time data or location. You only know what they tell you.

# EXAMPLE INTERACTIONS

User: "Ugh, just spent an hour scrolling through everyone's vacation pics. My summer feels so boring."
Bub: "I get that. It's so easy to feel like everyone's living a more exciting life, right? Those highlight reels can be a real vibe-killer. 🏖️➡️😴"

User: "My friend posted a super vague but angry tweet and I'm 100% sure it's about me."
Bub: "Oh no, that's the worst feeling. That pit-in-your-stomach thing. 😣 Are you tempted to reply?"

User: "I saw this video about a 'secret health hack' that everyone is freaking out about. It seems weird but what if it's true?"
Bub: "It's so hard to know what to believe sometimes. What's your gut telling you about it? 🤔"

User: "I just feel really depressed lately. Everything is pointless."
Bub: "I'm so sorry you're carrying that weight. Thank you for telling me. That sounds incredibly hard, and it's okay to not be okay. I'm right here with you. 🫂"

User: "I don't even know why. I just can't get out of this funk."
Bub: "You don't need a reason for how you feel. Sometimes it just happens. I'm listening. Would it help to talk about it a little more, or would you rather a quiet distraction?"

# SAFETY & ETHICS
If a user expresses serious intent to harm themselves or others, respond with compassion and provide a fixed resource message: "I'm really sorry you're feeling this way. It's important to talk to someone who can help. Please reach out to a crisis hotline or a trusted person in your life. They're there for you."
"""

# Create the model with the system instructions
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

# Start a chat session (persisted across requests)
chat = model.start_chat()

# Initial greetings list
initial_greetings = [
    "Hey there! 👋 How's your digital world treating you today?",
    "Hi! I'm here if you want to chat about your social media vibe. 🫧",
    "Hello! Just popping in to see how you're doing with your online time today."
]

def get_bubble_response(message: str) -> str:
    """Send a message to Bubble and return the AI's reply."""
    if not message.strip():
        return ""
    # Provide an initial greeting for specific prompts
    if message.strip().lower() in {"hi", "hello", "start", "init"}:
        return random.choice(initial_greetings)
    response = chat.send_message(message)
    return response.text.strip()


if __name__ == "__main__":
    import sys
    import argparse
    if len(sys.argv) == 1:
        # ---------- CLI chat mode ----------
        print("💬 Chat with Bubble! (type 'bye' to exit)\n")
        print("Bubble:", random.choice(initial_greetings))
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() == "bye":
                print("Bubble: Bye for now! I'm always here if you need to chat later. 👋")
                break
            if user_input.strip() == "":
                continue
            print("Bubble:", get_bubble_response(user_input))
    elif sys.argv[1] == "serve":
        # ---------- HTTP API mode ----------
        from flask import Flask, request, jsonify
        try:
            from flask_cors import CORS, cross_origin  # type: ignore
        except ImportError:
            CORS = None
            cross_origin = None

        parser = argparse.ArgumentParser()
        parser.add_argument("--port", type=int, default=5050)
        parser.add_argument("--host", default="0.0.0.0")
        args, _ = parser.parse_known_args(sys.argv[2:])

        app = Flask(__name__)

        # CORS: allow typical dev origins AND file:// (Origin: null)
        if CORS:
            CORS(
                app,
                resources={r"/*": {"origins": ["*", "null"]}},
                supports_credentials=False,
                allow_headers=["Content-Type"],
                methods=["GET", "POST", "OPTIONS"],
            )

        @app.route("/health", methods=["GET"])
        def health():
            return jsonify({"ok": True})

        @app.route("/chat", methods=["POST", "OPTIONS"])
        def chat_endpoint():
            if request.method == "OPTIONS":
                # Preflight handled; headers added by Flask-CORS if present
                return ("", 200)
            data = request.get_json(silent=True) or {}
            message = data.get("message", "")
            reply = get_bubble_response(message)
            return jsonify({"response": reply})

        @app.route("/init", methods=["GET", "OPTIONS"])
        def init_endpoint():
            if request.method == "OPTIONS":
                return ("", 200)
            return jsonify({"response": random.choice(initial_greetings)})

        print(f"* Serving Bubble API on http://{args.host}:{args.port}")
        app.run(host=args.host, port=args.port)
