"""
MindfulAI Voice Module
Handles speech-to-text (Whisper / SpeechRecognition) and text-to-speech (gTTS / pyttsx3).
"""

import os
import io
import base64
import tempfile

# ── TTS Backend Selection ────────────────────────────────────────────────────
try:
    from gtts import gTTS
    TTS_BACKEND = "gtts"
except ImportError:
    TTS_BACKEND = None

# ── STT Backend Selection ────────────────────────────────────────────────────
try:
    import whisper
    _whisper_model = None   # lazy-loaded on first use
    STT_BACKEND = "whisper"
except ImportError:
    STT_BACKEND = None

try:
    import speech_recognition as sr
    STT_BACKEND = STT_BACKEND or "speechrecognition"
except ImportError:
    pass


# ─── Text-to-Speech ───────────────────────────────────────────────────────────

def text_to_speech(text: str, lang: str = "en") -> bytes | None:
    """
    Convert text to an MP3 audio bytes object.
    Uses gTTS (cloud) or pyttsx3 (offline) depending on what's installed.
    Returns bytes of the MP3 file, or None on failure.
    """
    # Strip markdown
    import re
    clean = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    clean = re.sub(r"\*(.*?)\*", r"\1", clean)
    clean = re.sub(r"#+\s*", "", clean)
    clean = clean.strip()

    if TTS_BACKEND == "gtts":
        try:
            tts = gTTS(text=clean, lang=lang, slow=False)
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            return buf.read()
        except Exception as e:
            print(f"[TTS] gTTS error: {e}")
            return None

    elif TTS_BACKEND == "pyttsx3":
        try:
            import pyttsx3, tempfile, os
            engine = pyttsx3.init()
            engine.setProperty("rate", 160)
            engine.setProperty("volume", 0.9)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                tmp = f.name
            engine.save_to_file(clean, tmp)
            engine.runAndWait()
            with open(tmp, "rb") as f:
                data = f.read()
            os.unlink(tmp)
            return data
        except Exception as e:
            print(f"[TTS] pyttsx3 error: {e}")
            return None

    return None


def tts_base64(text: str, lang: str = "en") -> str | None:
    """Return TTS audio as a base64 string (for JSON API responses)."""
    audio = text_to_speech(text, lang)
    if audio:
        return base64.b64encode(audio).decode("utf-8")
    return None


# ─── Speech-to-Text ───────────────────────────────────────────────────────────

def speech_to_text_whisper(audio_path: str) -> str:
    """
    Transcribe an audio file using OpenAI Whisper (local, offline).
    Requires: pip install openai-whisper
    """
    global _whisper_model
    if _whisper_model is None:
        print("[STT] Loading Whisper model (first run may take a moment)…")
        _whisper_model = whisper.load_model("base")   # base = ~140MB, fast

    result = _whisper_model.transcribe(audio_path, language="en")
    return result.get("text", "").strip()


def speech_to_text_sr(audio_path: str) -> str:
    """
    Transcribe an audio file using Google Speech Recognition (requires internet).
    Requires: pip install SpeechRecognition
    """
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print(f"[STT] Google SR error: {e}")
        return ""


def transcribe_audio(audio_bytes: bytes, ext: str = "wav") -> str:
    """
    Transcribe raw audio bytes.
    Saves to a temp file, runs STT, then cleans up.
    Returns transcription string.
    """
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name

    transcript = ""
    try:
        if STT_BACKEND == "whisper":
            transcript = speech_to_text_whisper(tmp_path)
        elif STT_BACKEND == "speechrecognition":
            transcript = speech_to_text_sr(tmp_path)
        else:
            transcript = ""
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return transcript


# ─── Utility ──────────────────────────────────────────────────────────────────

def allowed_audio_file(filename: str, allowed: set = None) -> bool:
    """Check if a filename has an allowed audio extension."""
    allowed = allowed or {"wav", "mp3", "ogg", "webm", "m4a"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed
