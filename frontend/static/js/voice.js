/**
 * MindfulAI — voice.js
 * Speech-to-Text (Web Speech API / MediaRecorder → backend Whisper)
 * Text-to-Speech (Web SpeechSynthesis)
 */

const Voice = (() => {
  let recognition    = null;
  let isListening    = false;
  let ttsEnabled     = false;
  let mediaRecorder  = null;
  let audioChunks    = [];

  // ── TTS ────────────────────────────────────────────────────────
  function toggleTTS(enabled) {
    ttsEnabled = enabled;
    if (!enabled) window.speechSynthesis?.cancel();
  }

  function speak(text) {
    if (!ttsEnabled) return;
    if (!("speechSynthesis" in window)) return;

    // Strip markdown for cleaner speech
    const clean = text
      .replace(/\*\*(.*?)\*\*/g, "$1")
      .replace(/\*(.*?)\*/g, "$1")
      .replace(/#+\s/g, "")
      .replace(/<[^>]+>/g, "")
      .trim();

    window.speechSynthesis.cancel();
    const utt = new SpeechSynthesisUtterance(clean);
    utt.lang  = "en-IN";
    utt.rate  = 0.93;
    utt.pitch = 1.0;

    // Prefer a female English voice if available
    const voices = window.speechSynthesis.getVoices();
    const pref   =
      voices.find(v => v.lang.startsWith("en") && /female|woman|zira|karen|moira/i.test(v.name)) ||
      voices.find(v => v.lang.startsWith("en-IN")) ||
      voices.find(v => v.lang.startsWith("en"));
    if (pref) utt.voice = pref;

    window.speechSynthesis.speak(utt);
  }

  // Pre-load voices (required in some browsers)
  if ("speechSynthesis" in window) {
    window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
    window.speechSynthesis.getVoices();
  }

  // ── STT — Web Speech API (Chrome/Edge) ─────────────────────────
  function startWebSpeech() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SR();
    recognition.lang             = "en-IN";
    recognition.continuous       = false;
    recognition.interimResults   = true;
    recognition.maxAlternatives  = 1;

    recognition.onstart = () => {
      isListening = true;
      setBtnState(true);
      UI.showToast("Listening… speak now 🎤");
    };

    recognition.onresult = (e) => {
      const transcript = Array.from(e.results)
        .map(r => r[0].transcript).join("");
      document.getElementById("chat-input").value = transcript;
      UI.autoResize(document.getElementById("chat-input"));
    };

    recognition.onend = () => {
      isListening = false;
      setBtnState(false);
      const txt = document.getElementById("chat-input").value.trim();
      if (txt) setTimeout(() => Chat.send(), 350);
    };

    recognition.onerror = (e) => {
      isListening = false;
      setBtnState(false);
      if (e.error !== "no-speech") UI.showToast("Voice error: " + e.error);
    };

    recognition.start();
  }

  // ── STT — MediaRecorder → Backend Whisper (fallback) ───────────
  async function startMediaRecorder() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunks  = [];
      mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });

      mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const blob = new Blob(audioChunks, { type: "audio/webm" });
        setBtnState(false);
        isListening = false;
        UI.showToast("Transcribing…");
        try {
          const data = await API.voice.transcribe(blob, "webm");
          if (data.transcript) {
            document.getElementById("chat-input").value = data.transcript;
            UI.autoResize(document.getElementById("chat-input"));
            setTimeout(() => Chat.send(), 350);
          } else {
            UI.showToast("Could not understand audio. Please try again.");
          }
        } catch {
          UI.showToast("Transcription failed. Check your connection.");
        }
      };

      mediaRecorder.start();
      isListening = true;
      setBtnState(true);
      UI.showToast("Recording… tap again to stop 🎤");
    } catch (err) {
      UI.showToast("Microphone access denied.");
      console.error("[Voice] MediaRecorder error:", err);
    }
  }

  // ── Toggle STT ─────────────────────────────────────────────────
  function toggleSTT() {
    if (isListening) {
      stopListening();
      return;
    }

    const hasWebSpeech = "SpeechRecognition" in window || "webkitSpeechRecognition" in window;
    if (hasWebSpeech) {
      startWebSpeech();
    } else if (navigator.mediaDevices?.getUserMedia) {
      startMediaRecorder();
    } else {
      UI.showToast("Voice input not supported. Try Chrome or Edge.");
    }
  }

  function stopListening() {
    if (recognition) { recognition.stop(); recognition = null; }
    if (mediaRecorder && mediaRecorder.state !== "inactive") mediaRecorder.stop();
    isListening = false;
    setBtnState(false);
  }

  function setBtnState(active) {
    const btn = document.getElementById("btn-voice");
    btn.textContent = active ? "⏹" : "🎤";
    btn.classList.toggle("listening", active);
  }

  return { toggleSTT, speak, toggleTTS };
})();
