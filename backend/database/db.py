"""
MindfulAI Database Module
Handles SQLite connection, schema creation, and query helpers.
"""

import sqlite3
import os
from flask import g, current_app


# ─── Connection ─────────────────────────────────────────────────────────────

def get_db():
    """Get (or create) a database connection for the current request context."""
    if "db" not in g:
        db_path = current_app.config["DATABASE_PATH"]
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        g.db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row   # rows behave like dicts
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA journal_mode = WAL")  # better concurrency
    return g.db


def close_db(e=None):
    """Close database connection at end of request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ─── Schema ──────────────────────────────────────────────────────────────────

SCHEMA = """
-- ── Users ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    email       TEXT    NOT NULL UNIQUE,
    password    TEXT    NOT NULL,           -- bcrypt hash
    created_at  TEXT    DEFAULT (datetime('now')),
    last_login  TEXT
);

-- ── Chat Messages ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chat_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role        TEXT    NOT NULL CHECK(role IN ('user','assistant')),
    content     TEXT    NOT NULL,
    emotion     TEXT,                       -- detected emotion label
    is_crisis   INTEGER DEFAULT 0,         -- 1 if crisis keywords found
    created_at  TEXT    DEFAULT (datetime('now'))
);

-- ── Journal Entries ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS journal_entries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content     TEXT    NOT NULL,
    mood        TEXT,                       -- emoji + label e.g. "😊 Happy"
    emotion     TEXT,                       -- AI-detected emotion
    ai_insight  TEXT,                       -- AI reflection on the entry
    created_at  TEXT    DEFAULT (datetime('now'))
);

-- ── Habit Definitions ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS habits (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key         TEXT    NOT NULL,           -- e.g. 'sleep', 'water'
    name        TEXT    NOT NULL,
    icon        TEXT,
    unit        TEXT,
    goal        REAL    NOT NULL,
    invert      INTEGER DEFAULT 0,          -- 1 = lower is better (screen time)
    created_at  TEXT    DEFAULT (datetime('now')),
    UNIQUE(user_id, key)
);

-- ── Habit Logs ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS habit_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    habit_key   TEXT    NOT NULL,
    value       REAL    NOT NULL,
    log_date    TEXT    NOT NULL,           -- YYYY-MM-DD
    created_at  TEXT    DEFAULT (datetime('now')),
    UNIQUE(user_id, habit_key, log_date)
);

-- ── Mood Logs ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mood_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mood        TEXT    NOT NULL,
    label       TEXT    NOT NULL,
    log_date    TEXT    NOT NULL DEFAULT (date('now')),
    created_at  TEXT    DEFAULT (datetime('now'))
);

-- ── Indexes ───────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_chat_user    ON chat_messages(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_journal_user ON journal_entries(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_habit_logs   ON habit_logs(user_id, log_date);
CREATE INDEX IF NOT EXISTS idx_mood_logs    ON mood_logs(user_id, log_date);
"""

DEFAULT_HABITS = [
    ("sleep",    "Sleep",        "😴", "hours",   8.0,  0),
    ("water",    "Water Intake", "💧", "glasses",  8.0,  0),
    ("exercise", "Exercise",     "🏃", "minutes", 30.0,  0),
    ("mood",     "Mood Score",   "🌟", "/10",     10.0,  0),
    ("screen",   "Screen Time",  "📱", "hours",    4.0,  1),
]


def init_db():
    """Create all tables and seed default data."""
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()
    current_app.teardown_appcontext(close_db)


def seed_habits_for_user(user_id: int):
    """Insert the default 5 habits for a new user."""
    db = get_db()
    for key, name, icon, unit, goal, invert in DEFAULT_HABITS:
        db.execute(
            """INSERT OR IGNORE INTO habits (user_id, key, name, icon, unit, goal, invert)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, key, name, icon, unit, goal, invert)
        )
    db.commit()


# ─── Generic Query Helpers ────────────────────────────────────────────────────

def query_one(sql: str, params: tuple = ()) -> dict | None:
    """Return a single row as a dict, or None."""
    row = get_db().execute(sql, params).fetchone()
    return dict(row) if row else None


def query_all(sql: str, params: tuple = ()) -> list[dict]:
    """Return all rows as a list of dicts."""
    rows = get_db().execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def execute(sql: str, params: tuple = ()) -> int:
    """Execute a write query and return lastrowid."""
    db = get_db()
    cur = db.execute(sql, params)
    db.commit()
    return cur.lastrowid
