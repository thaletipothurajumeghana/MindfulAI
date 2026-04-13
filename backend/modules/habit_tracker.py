"""
MindfulAI Habit Tracker Module
Streak calculation, weekly summaries, and AI-generated insights.
"""

from datetime import date, timedelta
from database.db import query_all, query_one, execute


# ─── Streaks ──────────────────────────────────────────────────────────────────

def calc_streak(user_id: int, habit_key: str) -> int:
    """
    Count consecutive days (ending today) where the habit was logged with value > 0.
    """
    streak = 0
    check_date = date.today()

    for _ in range(90):  # look back up to 90 days
        row = query_one(
            "SELECT value FROM habit_logs WHERE user_id=? AND habit_key=? AND log_date=?",
            (user_id, habit_key, check_date.isoformat())
        )
        if row and row["value"] > 0:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    return streak


def get_all_streaks(user_id: int) -> dict[str, int]:
    """Return streaks for all habits as {habit_key: streak_days}."""
    habits = query_all("SELECT key FROM habits WHERE user_id=?", (user_id,))
    return {h["key"]: calc_streak(user_id, h["key"]) for h in habits}


# ─── Weekly Summary ───────────────────────────────────────────────────────────

def get_weekly_summary(user_id: int) -> list[dict]:
    """
    Return 7 days of habit completion data for charts.
    Each entry: {date, day_label, habits_logged, total_habits, percent}
    """
    today = date.today()
    start = today - timedelta(days=6)   # Mon to today

    total_habits = query_one(
        "SELECT COUNT(*) as n FROM habits WHERE user_id=?", (user_id,)
    )["n"]

    summary = []
    for i in range(7):
        d = start + timedelta(days=i)
        logged = query_one(
            "SELECT COUNT(*) as n FROM habit_logs WHERE user_id=? AND log_date=? AND value > 0",
            (user_id, d.isoformat())
        )["n"]

        summary.append({
            "date":          d.isoformat(),
            "day_label":     d.strftime("%a"),
            "habits_logged": logged,
            "total_habits":  total_habits,
            "percent":       round((logged / total_habits * 100) if total_habits else 0, 1),
        })

    return summary


# ─── Today's Logs ─────────────────────────────────────────────────────────────

def get_today_logs(user_id: int) -> dict[str, float]:
    """Return today's habit values as {habit_key: value}."""
    today = date.today().isoformat()
    rows = query_all(
        "SELECT habit_key, value FROM habit_logs WHERE user_id=? AND log_date=?",
        (user_id, today)
    )
    return {r["habit_key"]: r["value"] for r in rows}


def log_habit(user_id: int, habit_key: str, value: float) -> int:
    """
    Upsert today's habit log.  Returns the log row id.
    """
    today = date.today().isoformat()
    return execute(
        """INSERT INTO habit_logs (user_id, habit_key, value, log_date)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(user_id, habit_key, log_date) DO UPDATE SET value=excluded.value""",
        (user_id, habit_key, value, today)
    )


# ─── Insights ─────────────────────────────────────────────────────────────────

def generate_insights(user_id: int) -> list[dict]:
    """
    Generate actionable text insights based on the user's recent logs.
    Returns list of {color, text} dicts.
    """
    logs = get_today_logs(user_id)
    habits = {h["key"]: h for h in query_all("SELECT * FROM habits WHERE user_id=?", (user_id,))}
    insights = []

    # Sleep
    sleep_val = logs.get("sleep", 0)
    if sleep_val >= 7:
        insights.append({"color": "#34d399", "text": f"Great sleep ({sleep_val}h)! Consistent 7–9h sleep is one of the strongest predictors of mental well-being."})
    elif 0 < sleep_val < 6:
        insights.append({"color": "#f59e0b", "text": f"You only slept {sleep_val}h. Try a consistent bedtime routine; even 30 extra minutes makes a difference."})

    # Water
    water_val = logs.get("water", 0)
    if water_val >= 8:
        insights.append({"color": "#60a5fa", "text": "Excellent hydration today! Water supports both cognitive function and mood regulation."})
    elif 0 < water_val < 4:
        insights.append({"color": "#f59e0b", "text": f"Only {water_val} glasses of water today. Aim for 8 — dehydration worsens anxiety and fatigue."})

    # Exercise
    ex_val = logs.get("exercise", 0)
    if ex_val >= 30:
        insights.append({"color": "#a78bfa", "text": f"You exercised for {ex_val} minutes — amazing! Exercise is one of the most effective natural antidepressants."})
    elif 0 < ex_val < 15:
        insights.append({"color": "#9b99ac", "text": "Even a short walk counts. Try to build toward 30 minutes of movement — your brain will thank you."})

    # Screen time
    screen_val = logs.get("screen", 0)
    if screen_val > 6:
        insights.append({"color": "#fb7185", "text": f"{screen_val}h of screen time is high. Try a 'digital sunset' 1 hour before bed to improve sleep quality."})
    elif 0 < screen_val <= 3:
        insights.append({"color": "#34d399", "text": f"Only {screen_val}h of screen time — great digital hygiene!"})

    # Mood score
    mood_val = logs.get("mood", 0)
    if mood_val >= 8:
        insights.append({"color": "#fbbf24", "text": f"Mood score of {mood_val}/10 — you're thriving! Notice what's working today and try to recreate it tomorrow."})
    elif 0 < mood_val <= 4:
        insights.append({"color": "#fb7185", "text": f"Mood score of {mood_val}/10. Low days are normal. Consider talking to MindfulAI about how you're feeling."})

    # Streaks
    best_streak = max(
        ((k, calc_streak(user_id, k)) for k in habits),
        key=lambda x: x[1],
        default=(None, 0)
    )
    if best_streak[1] >= 3:
        habit_name = habits.get(best_streak[0], {}).get("name", best_streak[0])
        insights.append({"color": "#fbbf24", "text": f"🔥 {best_streak[1]}-day streak for {habit_name}! Research shows habits solidify after 21 days — you're building something real."})

    if not insights:
        insights.append({"color": "#9b99ac", "text": "Log your habits to unlock personalised insights and track your wellness journey day by day."})

    return insights
