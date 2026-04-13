/**
 * MindfulAI — ui.js
 * Shared UI utilities: view switching, toast, autoResize, auth tabs.
 */

const UI = (() => {

  function switchView(view) {
    document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
    document.querySelectorAll(".nav-tab").forEach(t => t.classList.remove("active"));
    document.getElementById(`view-${view}`)?.classList.add("active");
    document.querySelector(`.nav-tab[data-view="${view}"]`)?.classList.add("active");

    // Refresh data when switching to habits
    if (view === "habits") Habits.render();
  }

  function setAuthTab(tab) {
    document.getElementById("tab-login").classList.toggle("active", tab === "login");
    document.getElementById("tab-signup").classList.toggle("active", tab === "signup");
    document.getElementById("auth-login-form").classList.toggle("hidden", tab !== "login");
    document.getElementById("auth-signup-form").classList.toggle("hidden", tab !== "signup");
    document.getElementById("auth-error").classList.add("hidden");
  }

  let toastTimer = null;
  function showToast(msg, dur = 2800) {
    const el = document.getElementById("toast");
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove("show"), dur);
  }

  function autoResize(el) {
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 120) + "px";
  }

  // Keyboard shortcut: Escape to stop TTS
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") window.speechSynthesis?.cancel();
  });

  // Daily reminder (9am and 9pm)
  setInterval(() => {
    const h = new Date().getHours();
    if ((h === 9 || h === 21) && document.visibilityState === "visible") {
      const msgs = h === 9
        ? ["Good morning! How did you sleep? 🌅", "A new day, a fresh start — how are you? ☀️"]
        : ["Time to wind down. How was your day? 🌙", "Evening check-in: how are you doing tonight? ✨"];
      showToast(msgs[Math.floor(Math.random() * msgs.length)], 6000);
    }
  }, 3_600_000);

  return { switchView, setAuthTab, showToast, autoResize };
})();
