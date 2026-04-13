"""
MindfulAI Auth Routes
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
"""

from flask import Blueprint, request, jsonify
from database.db import query_one, execute, seed_habits_for_user
from modules.auth import hash_password, check_password, generate_token, login_required

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """Create a new user account."""
    data = request.get_json() or {}
    name     = (data.get("name") or "").strip()
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if query_one("SELECT id FROM users WHERE email=?", (email,)):
        return jsonify({"error": "An account with this email already exists"}), 409

    hashed = hash_password(password)
    user_id = execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        (name, email, hashed)
    )

    # Seed default habits for new user
    seed_habits_for_user(user_id)

    token = generate_token(user_id, name)
    return jsonify({"token": token, "user": {"id": user_id, "name": name, "email": email}}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate and return a JWT."""
    data  = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = query_one("SELECT * FROM users WHERE email=?", (email,))
    if not user or not check_password(password, user["password"]):
        return jsonify({"error": "Incorrect email or password"}), 401

    execute("UPDATE users SET last_login=datetime('now') WHERE id=?", (user["id"],))
    token = generate_token(user["id"], user["name"])

    return jsonify({
        "token": token,
        "user": {"id": user["id"], "name": user["name"], "email": user["email"]}
    })


@auth_bp.route("/me", methods=["GET"])
@login_required
def me(current_user):
    """Return the currently authenticated user's profile."""
    return jsonify({"user": current_user})
