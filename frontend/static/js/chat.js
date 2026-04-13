/**
 * MindfulAI — chat.js
 * Chat engine: send messages, render bubbles, typing indicator,
 * emotion badges, activity cards, crisis handling.
 */

const Chat = (() => {
  let currentUser  = null;
  let currentMood  = null;   // { emoji, label }

  // ── Init ───────────────────────────────────────────────────────
  async function init(user) {
    currentUser = user;
    const container = document.getElementById("chat-messages");
    container.innerHTML = "";

    // Load recent history from backend
    try {
      const data = await API.chat.history(40);
      if (data.messages && data.messages.length > 0) {
        data.messages.forEach(m => renderBubble(m.role, m.content, m.created_at, m.emotion, m.is_crisis, false));
        scrollToBottom();
        return;
      }
    } catch { /* first run or offline */ }

    // Welcome message
    renderBubble(
      "assistant",
      `Hello ${user.name} 👋 I'm MindfulAI, your wellness companion.\n\nI'm here to listen, support, and guide you — whether you want to talk about how you're feeling, try a breathing or grounding exercise, or just need someone to be with you for a moment.\n\nHow are you doing today?`,
      new Date().toISOString(), "neutral", false, true
    );
  }

  function reset() {
    currentUser = null;
    currentMood = null;
    document.getElementById("chat-messages").innerHTML = "";
  }

  // ── Send ───────────────────────────────────────────────────────
  async function send() {
    const input = document.getElementById("chat-input");
    const text  = input.value.trim();
    if (!text || !currentUser) return;

    input.value = "";
    UI.autoResize(input);

    renderBubble("user", text, new Date().toISOString(), null, false, true);

    const typingEl = showTyping();

    try {
      const moodStr = currentMood ? `${currentMood.emoji} ${currentMood.label}` : null;
      const data = await API.chat.send(text, moodStr);

      typingEl.remove();
      renderBubble(
        "assistant",
        data.reply,
        new Date().toISOString(),
        data.emotion,
        data.is_crisis,
        true,
        data.activity,
        data.helplines
      );

      Voice.speak(data.reply);
    } catch (err) {
      typingEl.remove();
      renderBubble(
        "assistant",
        "I'm having trouble connecting right now. Please try again — I'm still here for you. 💙\n\nIf you need immediate support: iCall 9152987821",
        new Date().toISOString(), "neutral", false, true
      );
    }
  }

  function quickSend(text) {
    document.getElementById("chat-input").value = text;
    send();
  }

  function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  }

  // ── Render ─────────────────────────────────────────────────────
  function renderBubble(role, content, timestamp, emotion, isCrisis, animate, activity, helplines) {
    const container = document.getElementById("chat-messages");
    const isAI      = role === "assistant";

    const wrapper = document.createElement("div");
    wrapper.className = `msg ${isAI ? "ai" : "user"}`;
    if (animate) { wrapper.style.opacity = "0"; wrapper.style.transform = "translateY(8px)"; }

    const timeStr = timestamp
      ? new Date(timestamp).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })
      : "";

    const avatarChar = isAI ? "🧠" : currentUser?.name?.[0]?.toUpperCase() || "U";

    // Build inner HTML
    let bubbleContent = "";

    if (isCrisis && isAI) {
      bubbleContent += `<div class="crisis-badge">🆘 Crisis support</div>`;
    }
    if (emotion && isAI && emotion !== "neutral") {
      const emojiMap = { sad:"😢", anxious:"😰", stressed:"😤", angry:"😡", happy:"😊" };
      bubbleContent += `<div class="emotion-badge">${emojiMap[emotion] || ""} ${emotion}</div>`;
    }

    bubbleContent += `<div>${formatText(content)}</div>`;

    if (activity) {
      bubbleContent += `
        <div class="activity-card">
          <div class="activity-title">✨ ${activity.title}</div>
          <div class="activity-steps">${activity.steps}</div>
        </div>`;
    }

    if (helplines && isCrisis) {
      const lines = Object.entries(helplines).map(([n, v]) => `📞 ${n}: ${v}`).join("<br>");
      bubbleContent += `<div class="activity-card"><div class="activity-title">Helplines</div><div class="activity-steps">${lines}</div></div>`;
    }

    wrapper.innerHTML = `
      <div class="msg-avatar ${isAI ? "ai" : "user"}">${avatarChar}</div>
      <div class="msg-content">
        <div class="msg-bubble${isCrisis && isAI ? " crisis" : ""}">${bubbleContent}</div>
        <div class="msg-time">${timeStr}</div>
      </div>`;

    container.appendChild(wrapper);

    if (animate) {
      requestAnimationFrame(() => {
        wrapper.style.transition = "opacity .3s, transform .3s";
        wrapper.style.opacity = "1";
        wrapper.style.transform = "translateY(0)";
      });
      scrollToBottom();
    }
  }

  function formatText(text) {
    if (!text) return "";
    return text
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(/\n\n/g, "</p><p style='margin-top:8px'>")
      .replace(/\n/g, "<br>");
  }

  function showTyping() {
    const container = document.getElementById("chat-messages");
    const el = document.createElement("div");
    el.className = "msg ai";
    el.id = "typing-indicator";
    el.innerHTML = `
      <div class="msg-avatar ai">🧠</div>
      <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>`;
    container.appendChild(el);
    scrollToBottom();
    return el;
  }

  function scrollToBottom() {
    const c = document.getElementById("chat-messages");
    c.scrollTop = c.scrollHeight;
  }

  // ── Exposed API ────────────────────────────────────────────────
  return { init, reset, send, quickSend, handleKey };
})();

// ── Mood module ──────────────────────────────────────────────────
const Mood = (() => {
  let current = null;

  function select(btn) {
    const emoji = btn.dataset.mood;
    const label = btn.dataset.label;
    current = { emoji, label };

    document.querySelectorAll(".mood-btn").forEach(b => b.classList.remove("selected"));
    btn.classList.add("selected");
    document.getElementById("current-mood-text").textContent = `Feeling ${label.toLowerCase()} ${emoji}`;
    document.getElementById("journal-mood-tag").textContent  = `${emoji} ${label}`;

    // Log to backend
    API.habits.logMood(emoji, label).catch(() => {});
  }

  function get() { return current; }

  return { select, get };
})();
