"""
MindfulAI Auth Helpers
JWT token generation/validation and bcrypt password utilities.
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from database.db import query_one


# ─── Password ─────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain.encode(), salt).decode()


def check_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ─── JWT ──────────────────────────────────────────────────────────────────────

def generate_token(user_id: int, user_name: str) -> str:
    """Create a signed JWT for the given user."""
    payload = {
        "user_id":  user_id,
        "user_name": user_name,
        "exp": datetime.utcnow() + timedelta(
            hours=current_app.config["JWT_EXPIRY_HOURS"]
        ),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT. Returns payload dict or None."""
    try:
        return jwt.decode(
            token,
            current_app.config["JWT_SECRET"],
            algorithms=["HS256"]
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ─── Route Decorator ──────────────────────────────────────────────────────────

def login_required(f):
    """
    Decorator for routes that require authentication.
    Injects `current_user` dict into the wrapped function.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid token"}), 401

        token = auth_header.split(" ", 1)[1]
        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "Token expired or invalid"}), 401

        user = query_one("SELECT * FROM users WHERE id = ?", (payload["user_id"],))
        if not user:
            return jsonify({"error": "User not found"}), 401

        # Remove password before passing to route
        user.pop("password", None)
        kwargs["current_user"] = user
        return f(*args, **kwargs)

    return decorated
