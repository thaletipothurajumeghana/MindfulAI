"""
MindfulAI Habit Routes
GET  /api/habits/           – list habits with today's logs
POST /api/habits/log        – log a habit value for today
GET  /api/habits/summary    – weekly chart data
GET  /api/habits/streaks    – all streak counts
GET  /api/habits/insights   – text insights
POST /api/habits/mood       – log daily mood check-in
"""

from flask import Blueprint, request, jsonify
from database.db import query_all, query_one, execute
from modules.auth import login_required
from modules.habit_tracker import (
    get_all_streaks, get_weekly_summary,
    get_today_logs, log_habit, generate_insights
)

habit_bp = Blueprint("habits", __name__)


@habit_bp.route("/", methods=["GET"])
@login_required
def list_habits(current_user):
    """Return all habits with today's logged values and streak counts."""
    user_id = current_user["id"]
    habits  = query_all("SELECT * FROM habits WHERE user_id=? ORDER BY id", (user_id,))
    today   = get_today_logs(user_id)
    streaks = get_all_streaks(user_id)

    enriched = []
    for h in habits:
        val = today.get(h["key"], 0)
        h["today_value"] = val
        h["streak"]      = streaks.get(h["key"], 0)
        goal             = h["goal"]
        if h["invert"]:
            # Lower is better — progress = how far under goal you are
            h["progress_pct"] = max(0, min(100, (1 - val / goal) * 100)) if val else 100
        else:
            h["progress_pct"] = min(100, (val / goal * 100)) if goal else 0
        enriched.append(h)

    return jsonify({"habits": enriched})


@habit_bp.route("/log", methods=["POST"])
@login_required
def log_habit_endpoint(current_user):
    """Log (or update) a habit value for today."""
    data      = request.get_json() or {}
    habit_key = data.get("habit_key")
    value     = data.get("value")

    if not habit_key or value is None:
        return jsonify({"error": "habit_key and value are required"}), 400

    try:
        value = float(value)
    except (TypeError, ValueError):
        return jsonify({"error": "value must be a number"}), 400

    user_id = current_user["id"]

    # Verify habit belongs to this user
    habit = query_one(
        "SELECT * FROM habits WHERE user_id=? AND key=?", (user_id, habit_key)
    )
    if not habit:
        return jsonify({"error": f"Habit '{habit_key}' not found"}), 404

    log_id = log_habit(user_id, habit_key, value)
    return jsonify({"log_id": log_id, "habit_key": habit_key, "value": value, "logged": True})


@habit_bp.route("/summary", methods=["GET"])
@login_required
def weekly_summary(current_user):
    """Return 7-day completion data for the habit chart."""
    return jsonify({"summary": get_weekly_summary(current_user["id"])})


@habit_bp.route("/streaks", methods=["GET"])
@login_required
def all_streaks(current_user):
    """Return streak counts for all habits."""
    return jsonify({"streaks": get_all_streaks(current_user["id"])})


@habit_bp.route("/insights", methods=["GET"])
@login_required
def insights(current_user):
    """Return personalized text insights based on today's logs."""
    return jsonify({"insights": generate_insights(current_user["id"])})


@habit_bp.route("/mood", methods=["POST"])
@login_required
def log_mood(current_user):
    """Log a mood check-in for today."""
    data  = request.get_json() or {}
    mood  = data.get("mood")
    label = data.get("label")

    if not mood or not label:
        return jsonify({"error": "mood and label are required"}), 400

    execute(
        "INSERT INTO mood_logs (user_id, mood, label) VALUES (?,?,?)",
        (current_user["id"], mood, label)
    )
    return jsonify({"logged": True, "mood": mood, "label": label})
