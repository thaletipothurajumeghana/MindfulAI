/**
 * MindfulAI — journal.js
 * Journal: save entries, load history, AI insights, delete.
 */

const Journal = (() => {

  async function init() {
    await loadEntries();
  }

  async function save() {
    const content = document.getElementById("journal-textarea").value.trim();
    if (!content) { UI.showToast("Write something first ✍️"); return; }

    const mood = Mood.get();
    const moodStr = mood ? `${mood.emoji} ${mood.label}` : null;

    try {
      await API.journal.create(content, moodStr, false);
      document.getElementById("journal-textarea").value = "";
      await loadEntries();
      UI.showToast("Entry saved ✓");
    } catch (e) {
      UI.showToast("Failed to save: " + e.message);
    }
  }

  async function analyze() {
    const content = document.getElementById("journal-textarea").value.trim();
    if (!content) { UI.showToast("Write something first ✍️"); return; }

    const btn = document.querySelector(".btn-analyze");
    btn.textContent = "⏳ Analyzing…";
    btn.disabled = true;

    const mood = Mood.get();
    const moodStr = mood ? `${mood.emoji} ${mood.label}` : null;

    try {
      await API.journal.create(content, moodStr, true);
      document.getElementById("journal-textarea").value = "";
      await loadEntries();
      UI.showToast("AI insights added ✨");
    } catch (e) {
      UI.showToast("Saved without AI insights (check connection).");
      // Try saving without AI
      try { await API.journal.create(content, moodStr, false); await loadEntries(); } catch {}
    } finally {
      btn.textContent = "✨ AI Insights";
      btn.disabled = false;
    }
  }

  async function deleteEntry(id) {
    if (!confirm("Delete this journal entry?")) return;
    try {
      await API.journal.delete(id);
      await loadEntries();
      UI.showToast("Entry deleted");
    } catch (e) {
      UI.showToast("Delete failed: " + e.message);
    }
  }

  async function generateInsight(id) {
    UI.showToast("Generating insight…");
    try {
      const data = await API.journal.insight(id);
      await loadEntries();
      UI.showToast("Insight added ✨");
    } catch {
      UI.showToast("Could not generate insight.");
    }
  }

  async function loadEntries() {
    const container = document.getElementById("journal-entries");
    try {
      const data = await API.journal.list(1);
      if (!data.entries || data.entries.length === 0) {
        container.innerHTML = `<div class="empty-state">Your journal entries will appear here. Start writing above ✍️</div>`;
        return;
      }
      container.innerHTML = data.entries.map(renderEntry).join("");
    } catch {
      container.innerHTML = `<div class="empty-state">Could not load entries. Check your connection.</div>`;
    }
  }

  function renderEntry(e) {
    const date = new Date(e.created_at).toLocaleDateString("en-IN", {
      weekday: "short", month: "short", day: "numeric",
      hour: "2-digit", minute: "2-digit"
    });
    const emotionBadge = e.emotion && e.emotion !== "neutral"
      ? `<span class="entry-emotion">${e.emotion}</span>`
      : "";

    const insightHtml = e.ai_insight
      ? `<div class="entry-insight">
           <div class="entry-insight-label">✨ AI Reflection</div>
           ${escHtml(e.ai_insight)}
         </div>`
      : `<button class="btn-secondary" style="margin-top:10px;font-size:12px"
           onclick="Journal.generateInsight(${e.id})">✨ Generate insight</button>`;

    return `
      <div class="journal-entry" id="entry-${e.id}">
        <div class="entry-header">
          <div class="entry-meta">
            <span class="entry-mood">${e.mood?.split(" ")[0] || "📝"}</span>
            <span class="entry-date">${date}</span>
            ${emotionBadge}
          </div>
          <button class="btn-delete-entry" onclick="Journal.deleteEntry(${e.id})" title="Delete entry">🗑</button>
        </div>
        <div class="entry-text">${escHtml(e.content)}</div>
        ${insightHtml}
      </div>`;
  }

  function escHtml(str) {
    return (str || "")
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/\n/g, "<br>");
  }

  return { init, save, analyze, deleteEntry, generateInsight };
})();
