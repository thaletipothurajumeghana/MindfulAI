from flask import Flask
from flask_cors import CORS
from config import Config
from database.db import init_db
from routes.auth_routes     import auth_bp
from routes.chat_routes     import chat_bp
from routes.habit_routes    import habit_bp
from routes.journal_routes  import journal_bp
from routes.voice_routes    import voice_bp
from routes.frontend_routes import frontend_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    with app.app_context():
        init_db()

    app.register_blueprint(auth_bp,    url_prefix="/api/auth")
    app.register_blueprint(chat_bp,    url_prefix="/api/chat")
    app.register_blueprint(habit_bp,   url_prefix="/api/habits")
    app.register_blueprint(journal_bp, url_prefix="/api/journal")
    app.register_blueprint(voice_bp,   url_prefix="/api/voice")
    app.register_blueprint(frontend_bp)

    @app.route("/api/health")
    def health():
        return {"status": "ok", "service": "MindfulAI"}

    return app


if __name__ == "__main__":
    import os

    app = create_app()
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "true").lower() == "true"

    print(f"\n✅  MindfulAI running at http://0.0.0.0:{port}\n")
    app.run(debug=debug, port=port, host="0.0.0.0")