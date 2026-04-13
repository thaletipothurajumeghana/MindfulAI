/**
 * MindfulAI — habits.js
 * Habit tracker: render cards, log values, weekly chart, insights.
 */

const Habits = (() => {

  async function init() {
    await render();
  }

  async function render() {
    await Promise.all([renderCards(), renderWeeklyChart(), renderInsights()]);
  }

  // ── Habit Cards ────────────────────────────────────────────────
  async function renderCards() {
    const grid = document.getElementById("habits-grid");
    try {
      const data = await API.habits.list();
      if (!data.habits || data.habits.length === 0) {
        grid.innerHTML = `<div class="empty-state">No habits found. Make sure you're signed in.</div>`;
        return;
      }
      grid.innerHTML = data.habits.map(habitCard).join("");
    } catch (e) {
      grid.innerHTML = `<div class="empty-state">Could not load habits. ${e.message}</div>`;
    }
  }

  function habitCard(h) {
    const colorMap = {
      sleep:    { color: "#7c3aed", bg: "rgba(124,58,237,.15)" },
      water:    { color: "#0ea5e9", bg: "rgba(14,165,233,.15)" },
      exercise: { color: "#10b981", bg: "rgba(16,185,129,.15)" },
      mood:     { color: "#f59e0b", bg: "rgba(245,158,11,.15)"  },
      screen:   { color: "#ef4444", bg: "rgba(239,68,68,.15)"   },
    };
    const theme = colorMap[h.key] || { color: "#a78bfa", bg: "rgba(167,139,250,.15)" };
    const pct   = h.progress_pct || 0;
    const isLogged = (h.today_value || 0) > 0;
    const goalLabel = h.invert
      ? `Max ${h.goal} ${h.unit}${h.today_value ? ` · Logged: ${h.today_value}` : ""}`
      : `Goal: ${h.goal} ${h.unit}${h.today_value ? ` · Logged: ${h.today_value}` : ""}`;

    return `
      <div class="habit-card" id="hcard-${h.key}">
        <div class="habit-card-header">
          <div class="habit-icon-wrap" style="background:${theme.bg};color:${theme.color}">${h.icon}</div>
          <div class="habit-streak">🔥 ${h.streak}d streak</div>
        </div>
        <div class="habit-name">${h.name}</div>
        <div class="habit-goal">${goalLabel}</div>
        <div class="habit-input-row">
          <input
            type="number" min="0" step="0.5"
            class="habit-input"
            id="hinput-${h.key}"
            value="${h.today_value || ""}"
            placeholder="0"
          />
          <span class="habit-unit">${h.unit}</span>
          <button
            class="btn-log${isLogged ? " logged" : ""}"
            onclick="Habits.log('${h.key}')"
          >${isLogged ? "✓ Logged" : "Log"}</button>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" style="width:${pct}%;background:${theme.color}"></div>
        </div>
      </div>`;
  }

  async function log(habitKey) {
    const input = document.getElementById(`hinput-${habitKey}`);
    const value = parseFloat(input.value);
    if (isNaN(value) || value < 0) { UI.showToast("Enter a valid number"); return; }

    try {
      await API.habits.log(habitKey, value);
      UI.showToast("Logged ✓");
      await render();
    } catch (e) {
      UI.showToast("Could not log: " + e.message);
    }
  }

  // ── Weekly Chart ───────────────────────────────────────────────
  async function renderWeeklyChart() {
    const chart = document.getElementById("weekly-chart");
    try {
      const data = await API.habits.summary();
      const days = data.summary || [];
      if (!days.length) { chart.innerHTML = ""; return; }

      const maxPct = Math.max(...days.map(d => d.percent), 1);

      chart.innerHTML = days.map(d => {
        const barH  = Math.max(4, (d.percent / 100) * 72);
        const color = d.percent >= 60 ? "#34d399"
                    : d.percent >= 30 ? "#f59e0b"
                    : "#3a3d4a";
        const today = new Date().toISOString().slice(0, 10);
        const isTodayDay = d.date === today;
        return `
          <div class="week-bar-wrap" title="${d.day_label}: ${d.percent}% complete">
            <div class="week-bar" style="height:${barH}px;background:${color};${isTodayDay ? "outline:2px solid #a78bfa;outline-offset:2px" : ""}"></div>
            <div class="week-label" style="${isTodayDay ? "color:var(--accent)" : ""}">${d.day_label}</div>
          </div>`;
      }).join("");
    } catch {
      chart.innerHTML = `<div style="color:var(--text3);font-size:13px">Chart unavailable</div>`;
    }
  }

  // ── Insights ───────────────────────────────────────────────────
  async function renderInsights() {
    const list = document.getElementById("insights-list");
    try {
      const data = await API.habits.insights();
      const items = data.insights || [];
      list.innerHTML = items.map(ins => `
        <div class="insight-item">
          <div class="insight-dot" style="background:${ins.color}"></div>
          <div class="insight-text">${ins.text}</div>
        </div>`).join("");
    } catch {
      list.innerHTML = `<div class="insight-text" style="color:var(--text3)">Log habits to see insights.</div>`;
    }
  }

  return { init, render, log };
})();
