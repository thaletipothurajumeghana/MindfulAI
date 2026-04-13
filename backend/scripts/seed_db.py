"""
MindfulAI — scripts/seed_db.py
Seeds the database with a demo user and sample data.
Run from the backend/ directory:  python scripts/seed_db.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from database.db import get_db, seed_habits_for_user, execute, query_one
from modules.auth import hash_password
from datetime import date, timedelta
import random

app = create_app()

with app.app_context():
    db = get_db()

    # ── Demo user ─────────────────────────────────────────────────
    email = "demo@mindfulai.app"
    existing = query_one("SELECT id FROM users WHERE email=?", (email,))
    if existing:
        print(f"Demo user already exists (id={existing['id']}). Skipping user creation.")
        user_id = existing["id"]
    else:
        user_id = execute(
            "INSERT INTO users (name, email, password) VALUES (?,?,?)",
            ("Alex", email, hash_password("demo1234"))
        )
        seed_habits_for_user(user_id)
        print(f"✅ Created demo user: {email} / demo1234  (id={user_id})")

    # ── Sample habit logs for the past 14 days ────────────────────
    habits_data = {
        "sleep":    lambda: round(random.uniform(5.5, 8.5), 1),
        "water":    lambda: random.randint(4, 10),
        "exercise": lambda: random.choice([0, 0, 20, 30, 45, 60]),
        "mood":     lambda: random.randint(4, 9),
        "screen":   lambda: round(random.uniform(2, 8), 1),
    }

    for i in range(14):
        d = (date.today() - timedelta(days=i)).isoformat()
        for key, gen in habits_data.items():
            if random.random() > 0.2:   # 80% chance of logging each day
                execute(
                    """INSERT OR REPLACE INTO habit_logs (user_id, habit_key, value, log_date)
                       VALUES (?,?,?,?)""",
                    (user_id, key, gen(), d)
                )

    # ── Sample journal entries ────────────────────────────────────
    sample_entries = [
        ("Today was a mixed bag. Work was overwhelming but I had a good call with my friend in the evening. Trying to stay grateful.", "😊 Happy"),
        ("Couldn't sleep again last night. My mind just won't stop racing with all the things I need to do. Feeling drained.", "😤 Stressed"),
        ("Had a really good morning run. Something about moving my body early makes the whole day feel lighter.", "😊 Happy"),
        ("Feeling a bit low today. Not sure why exactly — just one of those days where everything feels harder than it should.", "😢 Sad"),
    ]

    for i, (content, mood) in enumerate(sample_entries):
        d = (date.today() - timedelta(days=i+1)).isoformat() + " 20:30:00"
        execute(
            """INSERT OR IGNORE INTO journal_entries (user_id, content, mood, created_at)
               VALUES (?,?,?,?)""",
            (user_id, content, mood, d)
        )

    print(f"✅ Seeded {14} days of habit logs and {len(sample_entries)} journal entries.")
    print("\n🚀 You can now log in at http://localhost:5000")
    print("   Email:    demo@mindfulai.app")
    print("   Password: demo1234\n")
