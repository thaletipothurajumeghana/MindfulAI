"""
MindfulAI — tests/test_backend.py
Basic test suite for auth, chatbot, and habit modules.
Run: pytest tests/ -v
"""

import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.app import create_app
from database.db import get_db, seed_habits_for_user


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def app():
    """Create a test Flask app with a temp in-memory database."""
    os.environ["DATABASE_PATH"] = ":memory:"
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    os.environ["SECRET_KEY"] = "test-secret"
    os.environ["JWT_SECRET"] = "test-jwt"

    application = create_app()
    application.config["TESTING"] = True
    application.config["DATABASE_PATH"] = ":memory:"

    with application.app_context():
        from database.db import init_db
        init_db()
        yield application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Register a user and return auth headers."""
    res = client.post("/api/auth/register", json={
        "name": "Test User", "email": "test@test.com", "password": "test1234"
    })
    token = res.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


# ── Auth Tests ─────────────────────────────────────────────────────

class TestAuth:
    def test_register_success(self, client):
        r = client.post("/api/auth/register", json={
            "name": "Alice", "email": "alice@test.com", "password": "pass1234"
        })
        assert r.status_code == 201
        assert "token" in r.get_json()

    def test_register_duplicate_email(self, client):
        data = {"name": "Bob", "email": "bob@test.com", "password": "pass1234"}
        client.post("/api/auth/register", json=data)
        r = client.post("/api/auth/register", json=data)
        assert r.status_code == 409

    def test_register_missing_fields(self, client):
        r = client.post("/api/auth/register", json={"name": "X"})
        assert r.status_code == 400

    def test_login_success(self, client):
        client.post("/api/auth/register", json={
            "name": "Carol", "email": "carol@test.com", "password": "pass1234"
        })
        r = client.post("/api/auth/login", json={
            "email": "carol@test.com", "password": "pass1234"
        })
        assert r.status_code == 200
        assert "token" in r.get_json()

    def test_login_wrong_password(self, client):
        client.post("/api/auth/register", json={
            "name": "Dave", "email": "dave@test.com", "password": "correct"
        })
        r = client.post("/api/auth/login", json={
            "email": "dave@test.com", "password": "wrong"
        })
        assert r.status_code == 401

    def test_me_requires_auth(self, client):
        r = client.get("/api/auth/me")
        assert r.status_code == 401

    def test_me_with_auth(self, client, auth_headers):
        r = client.get("/api/auth/me", headers=auth_headers)
        assert r.status_code == 200
        assert r.get_json()["user"]["email"] == "test@test.com"


# ── Chat Tests ─────────────────────────────────────────────────────

class TestChat:
    def test_history_empty(self, client, auth_headers):
        r = client.get("/api/chat/history", headers=auth_headers)
        assert r.status_code == 200
        assert r.get_json()["messages"] == []

    def test_history_requires_auth(self, client):
        r = client.get("/api/chat/history")
        assert r.status_code == 401

    def test_clear_history(self, client, auth_headers):
        r = client.delete("/api/chat/history", headers=auth_headers)
        assert r.status_code == 200


# ── Habit Tests ────────────────────────────────────────────────────

class TestHabits:
    def test_list_habits(self, client, auth_headers):
        r = client.get("/api/habits/", headers=auth_headers)
        assert r.status_code == 200
        habits = r.get_json()["habits"]
        assert len(habits) == 5  # 5 default habits
        keys = [h["key"] for h in habits]
        assert "sleep" in keys
        assert "water" in keys

    def test_log_habit(self, client, auth_headers):
        r = client.post("/api/habits/log", json={"habit_key": "sleep", "value": 7.5}, headers=auth_headers)
        assert r.status_code == 200
        assert r.get_json()["logged"] is True

    def test_log_invalid_habit(self, client, auth_headers):
        r = client.post("/api/habits/log", json={"habit_key": "nonexistent", "value": 5}, headers=auth_headers)
        assert r.status_code == 404

    def test_log_invalid_value(self, client, auth_headers):
        r = client.post("/api/habits/log", json={"habit_key": "sleep", "value": "abc"}, headers=auth_headers)
        assert r.status_code == 400

    def test_weekly_summary(self, client, auth_headers):
        r = client.get("/api/habits/summary", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.get_json()["summary"]) == 7

    def test_insights(self, client, auth_headers):
        r = client.get("/api/habits/insights", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.get_json()["insights"], list)


# ── Journal Tests ──────────────────────────────────────────────────

class TestJournal:
    def test_create_entry(self, client, auth_headers):
        r = client.post("/api/journal/", json={
            "content": "Today was a good day. I felt calm and productive.",
            "mood": "😊 Happy",
            "with_ai_insight": False,
        }, headers=auth_headers)
        assert r.status_code == 201
        data = r.get_json()
        assert data["saved"] is True
        assert data["emotion"] in ("happy", "neutral", "sad", "anxious", "stressed", "angry")

    def test_list_entries(self, client, auth_headers):
        client.post("/api/journal/", json={"content": "Entry 1"}, headers=auth_headers)
        client.post("/api/journal/", json={"content": "Entry 2"}, headers=auth_headers)
        r = client.get("/api/journal/", headers=auth_headers)
        assert r.status_code == 200
        assert r.get_json()["total"] >= 2

    def test_delete_entry(self, client, auth_headers):
        r = client.post("/api/journal/", json={"content": "To delete"}, headers=auth_headers)
        entry_id = r.get_json()["id"]
        r2 = client.delete(f"/api/journal/{entry_id}", headers=auth_headers)
        assert r2.status_code == 200

    def test_empty_content_rejected(self, client, auth_headers):
        r = client.post("/api/journal/", json={"content": "   "}, headers=auth_headers)
        assert r.status_code == 400


# ── Emotion Detection Tests ────────────────────────────────────────

class TestEmotionDetection:
    def test_detects_sad(self):
        from modules.chatbot import detect_emotion
        assert detect_emotion("I feel so sad and hopeless today") == "sad"

    def test_detects_anxious(self):
        from modules.chatbot import detect_emotion
        assert detect_emotion("I am really anxious and worried about everything") == "anxious"

    def test_detects_stressed(self):
        from modules.chatbot import detect_emotion
        assert detect_emotion("I'm completely stressed and overwhelmed with work") == "stressed"

    def test_detects_happy(self):
        from modules.chatbot import detect_emotion
        assert detect_emotion("I feel so happy and excited today!") == "happy"

    def test_detects_angry(self):
        from modules.chatbot import detect_emotion
        assert detect_emotion("I am so angry and frustrated right now") == "angry"

    def test_neutral_fallback(self):
        from modules.chatbot import detect_emotion
        assert detect_emotion("The weather is fine today.") == "neutral"


# ── Crisis Detection Tests ─────────────────────────────────────────

class TestCrisisDetection:
    def test_detects_suicide(self, app):
        with app.app_context():
            from modules.chatbot import detect_crisis
            assert detect_crisis("I want to kill myself") is True

    def test_detects_self_harm(self, app):
        with app.app_context():
            from modules.chatbot import detect_crisis
            assert detect_crisis("I've been cutting myself") is True

    def test_safe_message(self, app):
        with app.app_context():
            from modules.chatbot import detect_crisis
            assert detect_crisis("I had a hard day at work") is False


# ── Health Check ───────────────────────────────────────────────────

class TestHealth:
    def test_health_endpoint(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.get_json()["status"] == "ok"
