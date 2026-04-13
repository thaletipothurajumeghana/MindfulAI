import os
from flask import Blueprint, send_from_directory, send_file

TEMPLATE_DIR = r"C:\Users\megha\OneDrive\Desktop\MindfulAI\frontend\templates"
STATIC_DIR   = r"C:\Users\megha\OneDrive\Desktop\MindfulAI\frontend\static"

frontend_bp = Blueprint(
    "frontend", __name__,
    static_folder=STATIC_DIR,
    static_url_path="/static"
)

@frontend_bp.route("/")
def index():
    return send_file(os.path.join(TEMPLATE_DIR, "index.html"))