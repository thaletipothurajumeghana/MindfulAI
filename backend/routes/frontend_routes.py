import os
from flask import Blueprint, send_file

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATE_DIR = os.path.join(BASE_DIR, "frontend", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")

frontend_bp = Blueprint(
    "frontend", __name__,
    static_folder=STATIC_DIR,
    static_url_path="/static"
)

@frontend_bp.route("/")
def index():
    return send_file(os.path.join(TEMPLATE_DIR, "index.html"))