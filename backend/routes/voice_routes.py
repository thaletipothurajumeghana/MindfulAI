"""
MindfulAI Voice Routes
POST /api/voice/transcribe   – audio file → text (STT)
POST /api/voice/speak        – text → audio base64 (TTS)
"""

from flask import Blueprint, request, jsonify
from modules.auth import login_required
from modules.voice import transcribe_audio, tts_base64, allowed_audio_file

voice_bp = Blueprint("voice", __name__)


@voice_bp.route("/transcribe", methods=["POST"])
@login_required
def transcribe(current_user):
    """
    Receive an audio file and return the transcribed text.
    Expects multipart/form-data with field 'audio'.
    """
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    if not audio_file.filename:
        return jsonify({"error": "Empty filename"}), 400

    filename = audio_file.filename
    if not allowed_audio_file(filename):
        return jsonify({"error": "Unsupported audio format. Use wav, mp3, ogg, webm, or m4a"}), 400

    ext = filename.rsplit(".", 1)[1].lower()
    audio_bytes = audio_file.read()

    # Reject files over 10MB
    if len(audio_bytes) > 10 * 1024 * 1024:
        return jsonify({"error": "Audio file too large (max 10MB)"}), 413

    transcript = transcribe_audio(audio_bytes, ext)

    if not transcript:
        return jsonify({"error": "Could not transcribe audio. Please speak clearly and try again."}), 422

    return jsonify({"transcript": transcript})


@voice_bp.route("/speak", methods=["POST"])
@login_required
def speak(current_user):
    """
    Receive text and return base64-encoded MP3 audio.
    Expects JSON: { "text": "...", "lang": "en" }
    """
    data = request.get_json() or {}
    text = (data.get("text") or "").strip()
    lang = data.get("lang", "en")

    if not text:
        return jsonify({"error": "Text is required"}), 400

    if len(text) > 3000:
        # Truncate very long texts to prevent abuse
        text = text[:3000] + "…"

    audio_b64 = tts_base64(text, lang)

    if audio_b64 is None:
        return jsonify({"error": "TTS not available on this server. Please use browser speech synthesis."}), 503

    return jsonify({
        "audio_base64": audio_b64,
        "format": "mp3",
        "lang":   lang,
    })
