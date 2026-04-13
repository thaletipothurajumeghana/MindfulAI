# MindfulAI — Complete Setup Guide

## Project Structure

```
mindfulai/
├── backend/
│   ├── app.py                    ← Flask app factory + entry point
│   ├── config.py                 ← All configuration (API keys, etc.)
│   ├── requirements.txt          ← Python dependencies
│   ├── .env.example              ← Environment variable template
│   ├── database/
│   │   ├── __init__.py
│   │   └── db.py                 ← SQLite schema, helpers, connection
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── chatbot.py            ← Claude API, emotion + crisis detection
│   │   ├── voice.py              ← STT (Whisper/SR) + TTS (gTTS/pyttsx3)
│   │   ├── auth.py               ← JWT + bcrypt helpers
│   │   └── habit_tracker.py      ← Streaks, weekly summary, insights
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_routes.py        ← POST /api/auth/register|login; GET /api/auth/me
│   │   ├── chat_routes.py        ← POST /api/chat/message; GET /api/chat/history
│   │   ├── habit_routes.py       ← GET/POST /api/habits/...
│   │   ├── journal_routes.py     ← CRUD /api/journal/...
│   │   ├── voice_routes.py       ← POST /api/voice/transcribe|speak
│   │   └── frontend_routes.py    ← Serves HTML/CSS/JS
│   ├── scripts/
│   │   └── seed_db.py            ← Demo data seeder
│   └── tests/
│       └── test_backend.py       ← Full pytest test suite
└── frontend/
    ├── templates/
    │   └── index.html            ← App shell (single-page app)
    └── static/
        ├── css/
        │   ├── main.css          ← Variables, auth, nav, utilities
        │   ├── chat.css          ← Chat view styles
        │   └── dashboard.css     ← Journal + Habits view styles
        └── js/
            ├── api.js            ← All fetch calls to backend
            ├── auth.js           ← Login, signup, session restore
            ├── voice.js          ← Web Speech STT + SpeechSynthesis TTS
            ├── chat.js           ← Chat engine + mood module
            ├── journal.js        ← Journal CRUD + AI insights
            ├── habits.js         ← Habit cards, chart, insights
            ├── ui.js             ← View switching, toast, utilities
            ├── app.js            ← Bootstrap + service worker
            └── sw.js             ← Service worker (offline support)
```

---

## Step 1 — Prerequisites

- Python 3.11+
- pip
- A free [Anthropic API key](https://console.anthropic.com)

---

## Step 2 — Install Dependencies

```bash
cd mindfulai/backend
pip install -r requirements.txt
```

**Optional voice packages:**
```bash
# Offline TTS (no internet needed):
pip install pyttsx3

# Offline STT with Whisper (~500MB model download on first run):
pip install openai-whisper

# System audio for SpeechRecognition (Linux):
sudo apt-get install portaudio19-dev python3-pyaudio
pip install PyAudio
```

---

## Step 3 — Configure Environment

```bash
cp .env.example .env
```

Open `.env` and set your key:
```
ANTHROPIC_API_KEY=sk-ant-...your-key-here...
SECRET_KEY=any-long-random-string
JWT_SECRET=another-long-random-string
```

---

## Step 4 — Run the App

```bash
cd mindfulai/backend
python app.py
```

Open **http://localhost:5000** in your browser.

---

## Step 5 (Optional) — Seed Demo Data

```bash
python scripts/seed_db.py
```

This creates:
- **Demo account:** `demo@mindfulai.app` / `demo1234`
- 14 days of habit logs
- 4 sample journal entries

---

## Step 6 (Optional) — Run Tests

```bash
pip install pytest
cd mindfulai/backend
pytest tests/ -v
```

---

## API Endpoints Reference

### Auth
| Method | Path | Body | Description |
|--------|------|------|-------------|
| POST | `/api/auth/register` | `{name, email, password}` | Create account |
| POST | `/api/auth/login` | `{email, password}` | Sign in, get JWT |
| GET | `/api/auth/me` | — | Get current user |

### Chat
| Method | Path | Body | Description |
|--------|------|------|-------------|
| POST | `/api/chat/message` | `{message, mood?}` | Send message, get AI reply |
| GET | `/api/chat/history` | `?limit=50` | Recent messages |
| DELETE | `/api/chat/history` | — | Clear history |
| GET | `/api/chat/activity` | `?emotion=sad` | Get activity suggestion |

### Habits
| Method | Path | Body | Description |
|--------|------|------|-------------|
| GET | `/api/habits/` | — | List habits with today's values |
| POST | `/api/habits/log` | `{habit_key, value}` | Log a habit |
| GET | `/api/habits/summary` | — | 7-day chart data |
| GET | `/api/habits/streaks` | — | All streak counts |
| GET | `/api/habits/insights` | — | Text insights |
| POST | `/api/habits/mood` | `{mood, label}` | Log mood check-in |

### Journal
| Method | Path | Body | Description |
|--------|------|------|-------------|
| POST | `/api/journal/` | `{content, mood?, with_ai_insight?}` | Create entry |
| GET | `/api/journal/` | `?page=1` | Paginated entries |
| DELETE | `/api/journal/<id>` | — | Delete entry |
| POST | `/api/journal/<id>/insight` | — | Generate AI insight |

### Voice
| Method | Path | Body | Description |
|--------|------|------|-------------|
| POST | `/api/voice/transcribe` | `FormData: audio file` | Audio → text |
| POST | `/api/voice/speak` | `{text, lang?}` | Text → MP3 base64 |

---

## Deployment Options

### Local (Development)
```bash
python app.py   # runs on http://localhost:5000
```

### Production (Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/ .
RUN pip install -r requirements.txt gunicorn
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:create_app()"]
```

### Render.com (Free Tier)
1. Push to GitHub
2. New Web Service → connect repo
3. Build command: `pip install -r backend/requirements.txt`
4. Start command: `gunicorn -w 2 -b 0.0.0.0:$PORT "backend.app:create_app()"`
5. Add environment variables in Render dashboard

### Railway / Fly.io
Both support one-click Python deployments from GitHub.

---

## Features Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Chat with Claude AI | ✅ | claude-sonnet-4-20250514 |
| Emotion detection | ✅ | Regex NLP (local, instant) |
| Crisis detection | ✅ | 17 keyword patterns |
| Indian helplines | ✅ | iCall, Vandrevala, NIMHANS, Fortis |
| Voice input (STT) | ✅ | Web Speech API (Chrome) + Whisper fallback |
| Voice output (TTS) | ✅ | Web SpeechSynthesis + gTTS backend |
| Mood check-in | ✅ | 5 emotions, sidebar UI |
| Habit tracking | ✅ | 5 habits, streaks, progress bars |
| Weekly chart | ✅ | Mon–Sun bar chart |
| Habit insights | ✅ | Personalised text analysis |
| Journal | ✅ | Full CRUD with timestamps |
| AI journal insights | ✅ | Claude reflection per entry |
| User auth (JWT) | ✅ | bcrypt passwords |
| Session persistence | ✅ | JWT stored in localStorage |
| Offline support | ✅ | Service Worker caches static assets |
| Responsive UI | ✅ | Mobile-friendly layout |
| Medical disclaimer | ✅ | Visible on every session |
| Daily reminders | ✅ | 9am and 9pm browser notifications |
| Demo data seeder | ✅ | `python scripts/seed_db.py` |
| Full test suite | ✅ | pytest, 20+ tests |

---

## Safety & Ethics

- Crisis keywords scanned **locally** (no API call needed) — instant response
- Helplines always shown during crisis responses
- Claude's system prompt explicitly prohibits diagnosis
- All data stays in your SQLite file — no external data sharing
- Passwords hashed with bcrypt (12 rounds)
- JWT tokens expire after 72 hours
- Medical disclaimer prominently displayed in the UI
