"""
MindfulAI Chatbot Module
Uses requests (HTTP) to call Anthropic API directly — no anthropic package needed.
"""

import re
import requests
from flask import current_app

# ─── Emotion Detection ────────────────────────────────────────────────────────

EMOTION_PATTERNS = {
    "sad":      [r"\b(sad|unhappy|depress|cry|crying|hopeless|lonely|miserable|grief|heartbroken|devastated|sorrowful|blue|down|low)\b"],
    "anxious":  [r"\b(anxi|worry|worri|nervous|panic|scared|fear|dread|overwhelm|uneasy|apprehens|tense|jitter|restless)\b"],
    "stressed": [r"\b(stress|pressure|burden|exhaust|burnout|overload|drained|overwhelm|frantic|chaos|hectic|swamp)\b"],
    "angry":    [r"\b(angry|anger|furious|rage|mad|irritat|frustrat|annoyed|resent|hatred|hate|livid|fuming|aggravat)\b"],
    "happy":    [r"\b(happy|joyful|excited|great|wonderful|fantastic|elated|cheerful|content|grateful|blessed|thrilled|amazing)\b"],
}

def detect_emotion(text: str) -> str:
    text_lower = text.lower()
    scores = {e: 0 for e in EMOTION_PATTERNS}
    for emotion, patterns in EMOTION_PATTERNS.items():
        for pattern in patterns:
            scores[emotion] += len(re.findall(pattern, text_lower))
    top = max(scores, key=scores.get)
    return top if scores[top] > 0 else "neutral"


# ─── Crisis Detection ─────────────────────────────────────────────────────────

def detect_crisis(text: str) -> bool:
    keywords = current_app.config.get("CRISIS_KEYWORDS", [])
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def get_crisis_response() -> str:
    helplines = current_app.config.get("HELPLINES", {})
    lines = "\n".join(f"📞 {name}: {number}" for name, number in helplines.items())
    return (
        "I hear you, and I'm really glad you're talking to me right now. "
        "What you're feeling is real, and you matter deeply.\n\n"
        "Please reach out to someone who can help right now:\n\n"
        f"{lines}\n\n"
        "These are free, confidential, and available 24/7. "
        "You don't have to go through this alone. 💙"
    )


# ─── Activity Suggestions ─────────────────────────────────────────────────────

ACTIVITIES = {
    "sad": {
        "title": "Gentle Breathing Exercise",
        "steps": "1. Sit comfortably and close your eyes.\n2. Breathe in slowly for 4 counts.\n3. Hold gently for 2 counts.\n4. Breathe out for 6 counts.\n5. Repeat 5–8 times. 💙"
    },
    "anxious": {
        "title": "5-4-3-2-1 Grounding Technique",
        "steps": "Notice around you right now:\n👁 5 things you can SEE\n🤚 4 things you can TOUCH\n👂 3 things you can HEAR\n👃 2 things you can SMELL\n👅 1 thing you can TASTE\n\nTake a slow breath after each sense. 🌿"
    },
    "stressed": {
        "title": "Box Breathing",
        "steps": "1. Breathe IN for 4 seconds\n2. HOLD for 4 seconds\n3. Breathe OUT for 4 seconds\n4. HOLD for 4 seconds\n\nRepeat 4 times. 🧘"
    },
    "angry": {
        "title": "Cool-Down Technique",
        "steps": "1. Step away if possible.\n2. Take 10 slow deep breaths.\n3. Drink a glass of cold water.\n4. Write down what happened.\n5. Ask: Will this matter in 5 days? 🧊"
    },
    "happy": {
        "title": "Gratitude Amplifier",
        "steps": "✨ 3 things that made today good\n💙 1 person you're grateful for\n🌱 1 thing you're proud of yourself for\n\nSavoring positive experiences builds resilience! 🌟"
    },
    "neutral": {
        "title": "Mindfulness Check-In",
        "steps": "• How does your body feel right now?\n• What emotion is closest to what you're feeling?\n• What do you need in this moment?\n\nJust noticing is enough. 🌿"
    }
}

def get_activity(emotion: str) -> dict:
    return ACTIVITIES.get(emotion, ACTIVITIES["neutral"])


# ─── Anthropic API via requests ───────────────────────────────────────────────

def call_claude(system: str, messages: list) -> str:
    """Call Anthropic API using plain HTTP requests — no anthropic package needed."""
    api_key = current_app.config.get("ANTHROPIC_API_KEY", "")

    headers = {
        "x-api-key":         api_key,
        "anthropic-version": "2023-06-01",
        "content-type":      "application/json",
    }

    payload = {
        "model":      current_app.config.get("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
        "max_tokens": current_app.config.get("CLAUDE_MAX_TOKENS", 1024),
        "system":     system,
        "messages":   messages,
    }

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=payload,
        timeout=30,
    )

    if response.status_code != 200:
        raise Exception(f"Anthropic API error {response.status_code}: {response.text}")

    data = response.json()
    return data["content"][0]["text"]


# ─── System Prompt ────────────────────────────────────────────────────────────

def build_system_prompt(user_name: str, mood: str | None, is_crisis: bool) -> str:
    mood_ctx = f"\nUser's current mood: {mood}" if mood else ""

    crisis_instructions = ""
    if is_crisis:
        helplines = current_app.config.get("HELPLINES", {})
        lines = ", ".join(f"{n}: {v}" for n, v in helplines.items())
        crisis_instructions = f"""
⚠️ CRISIS MODE:
The user may be expressing thoughts of self-harm or suicide.
- Respond with genuine warmth and empathy
- Tell them their life has value
- Strongly encourage them to call: {lines}
- Do NOT be clinical — be a caring human voice
"""

    return f"""You are MindfulAI, a warm and empathetic mental wellness companion.
The user's name is {user_name}.{mood_ctx}

Your character:
- Warm, gentle, non-judgmental, genuinely caring
- Speak like a wise caring friend — not a therapist or doctor
- Use the user's name occasionally
- Keep responses to 2–4 paragraphs
- Ask one thoughtful follow-up question when appropriate

Your capabilities:
- Emotional support and active listening
- Guided breathing, meditation, and grounding exercises
- Journaling prompts
- Habit and routine encouragement

Your boundaries:
- You are NOT a licensed therapist or medical professional
- Never diagnose any condition
- Always recommend professional help for serious concerns
{crisis_instructions}"""


# ─── Main Chat Function ───────────────────────────────────────────────────────

def get_chat_response(user_message: str, history: list, user_name: str, mood: str | None = None):
    """Returns (reply_text, emotion, is_crisis)"""
    is_crisis = detect_crisis(user_message)
    emotion   = detect_emotion(user_message)

    # Build message list for API
    messages = []
    for msg in history[-20:]:
        role = "assistant" if msg["role"] == "assistant" else "user"
        messages.append({"role": role, "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    system = build_system_prompt(user_name, mood, is_crisis)

    try:
        reply = call_claude(system, messages)
    except Exception as e:
        print(f"[Claude API Error] {e}")
        if is_crisis:
            reply = get_crisis_response()
        else:
            reply = (
                "I'm having a little trouble connecting right now, but I'm still here. "
                "Please try again in a moment. If you need immediate support, "
                "iCall is available at 9152987821."
            )

    return reply, emotion, is_crisis


# ─── Journal Insight ──────────────────────────────────────────────────────────

def get_journal_insight(entry_text: str) -> str:
    try:
        return call_claude(
            system="You are a warm, empathetic wellness companion. When given a journal entry, provide a brief 3-4 sentence reflection. Identify the core emotion, validate it warmly, and offer one gentle perspective or question. Be a caring friend, not a therapist.",
            messages=[{"role": "user", "content": f"Journal entry:\n\"{entry_text}\""}]
        )
    except Exception as e:
        print(f"[Journal Insight Error] {e}")
        return "Your thoughts and feelings are completely valid. Writing them down takes courage and self-awareness."