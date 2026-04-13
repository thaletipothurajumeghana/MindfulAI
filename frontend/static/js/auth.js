/**
 * MindfulAI — auth.js
 * Handles login, signup, logout, session restore.
 */

const Auth = (() => {

  async function login() {
    const email = document.getElementById("login-email").value.trim();
    const pass  = document.getElementById("login-pass").value;
    const errEl = document.getElementById("auth-error");
    errEl.classList.add("hidden");

    if (!email || !pass) { showAuthError("Please fill in all fields."); return; }

    try {
      const data = await API.auth.login(email, pass);
      onLoginSuccess(data.user);
    } catch (e) {
      showAuthError(e.message || "Login failed. Check your credentials.");
    }
  }

  async function signup() {
    const name  = document.getElementById("signup-name").value.trim();
    const email = document.getElementById("signup-email").value.trim();
    const pass  = document.getElementById("signup-pass").value;
    const errEl = document.getElementById("auth-error");
    errEl.classList.add("hidden");

    if (!name || !email || !pass) { showAuthError("Please fill in all fields."); return; }
    if (pass.length < 6) { showAuthError("Password must be at least 6 characters."); return; }

    try {
      const data = await API.auth.register(name, email, pass);
      onLoginSuccess(data.user);
    } catch (e) {
      showAuthError(e.message || "Signup failed. Try a different email.");
    }
  }

  function logout() {
    API.auth.logout();
    document.getElementById("app").classList.add("hidden");
    document.getElementById("auth-screen").style.display = "flex";
    // Clear state
    Chat.reset();
  }

  function onLoginSuccess(user) {
    document.getElementById("auth-screen").style.display = "none";
    document.getElementById("app").classList.remove("hidden");
    document.getElementById("nav-avatar").textContent   = user.name[0].toUpperCase();
    document.getElementById("nav-username").textContent = user.name;
    document.getElementById("journal-date").textContent =
      new Date().toLocaleDateString("en-IN", { weekday:"long", year:"numeric", month:"long", day:"numeric" });

    // Load each module
    Chat.init(user);
    Habits.init();
    Journal.init();
  }

  async function restoreSession() {
    if (!API.getToken()) return;
    try {
      const data = await API.auth.me();
      onLoginSuccess(data.user);
    } catch {
      API.clearToken();
    }
  }

  function showAuthError(msg) {
    const el = document.getElementById("auth-error");
    el.textContent = msg;
    el.classList.remove("hidden");
  }

  return { login, signup, logout, restoreSession };
})();
