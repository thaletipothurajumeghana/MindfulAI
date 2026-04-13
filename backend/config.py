"""
MindfulAI Configuration
Edit this file to change API keys, database path, and app settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env file

class Config:
    # ── Flask ──────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production-please")
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"

    # ── Anthropic Claude API ───────────────────────────
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL = "claude-sonnet-4-20250514"
    CLAUDE_MAX_TOKENS = 1024

    # ── Database ───────────────────────────────────────
    DATABASE_PATH = os.getenv("DATABASE_PATH", "database/mindfulai.db")

    # ── JWT Auth ───────────────────────────────────────
    JWT_SECRET = os.getenv("JWT_SECRET", "jwt-secret-change-me")
    JWT_EXPIRY_HOURS = 72

    # ── Voice / Audio ──────────────────────────────────
    UPLOAD_FOLDER = "uploads/audio"
    ALLOWED_AUDIO_EXTENSIONS = {"wav", "mp3", "ogg", "webm", "m4a"}
    MAX_AUDIO_SIZE_MB = 10

    # ── Rate Limiting ──────────────────────────────────
    CHAT_RATE_LIMIT = 60          # messages per hour per user
    API_RATE_LIMIT = 100          # API calls per hour per user

    # ── Crisis Keywords ────────────────────────────────
    CRISIS_KEYWORDS = [
        "suicide", "suicidal", "kill myself", "end my life",
        "want to die", "self harm", "self-harm", "cut myself",
        "overdose", "no reason to live", "give up on life",
        "hurt myself", "not worth living", "end it all",
        "take my life", "can't go on", "better off dead"
    ]

    # ── Helplines (India) ─────────────────────────────
    HELPLINES = {
        "iCall (TISS)": "9152987821",
        "Vandrevala Foundation": "1860-2662-345",
        "NIMHANS": "080-46110007",
        "Fortis Stress": "8376804102",
        "iCall WhatsApp": "9152987821",
    }
