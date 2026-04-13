/**
 * MindfulAI — app.js
 * Application bootstrap. Runs after all other scripts are loaded.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Attempt to restore an existing session on page load
  Auth.restoreSession();

  // Allow pressing Enter in auth inputs
  document.getElementById("login-pass").addEventListener("keydown", e => {
    if (e.key === "Enter") Auth.login();
  });
  document.getElementById("signup-pass").addEventListener("keydown", e => {
    if (e.key === "Enter") Auth.signup();
  });

  // Service Worker registration (offline support)
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/static/js/sw.js")
      .then(() => console.log("[SW] Registered"))
      .catch(err => console.warn("[SW] Registration failed:", err));
  }
});
