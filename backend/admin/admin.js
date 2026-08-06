const seasonLabel = document.getElementById("season-label");
const matchdaySelect = document.getElementById("matchday");
const warning = document.getElementById("existing-warning");
const scoreRows = document.getElementById("score-rows");
const form = document.getElementById("entry-form");
const preview = document.getElementById("preview");
const previewRows = document.getElementById("preview-rows");
const saveButton = document.getElementById("save-button");
const publishCheckbox = document.getElementById("publish");
const status = document.getElementById("status");

let state;
let lastPayload;

function setStatus(message, kind = "") {
  status.textContent = message;
  status.className = kind;
}

function updateWarning() {
  const matchday = Number(matchdaySelect.value);
  const exists = state.existing_matchdays.includes(matchday);
  warning.hidden = !exists;
  warning.textContent = exists
    ? `Spieltag ${matchday} ist bereits vorhanden und wird beim Speichern ersetzt.`
    : "";
  preview.hidden = true;
  lastPayload = null;
}

function readPayload() {
  const scores = {};
  for (const participant of state.participants) {
    const ts = document.querySelector(`[data-ts="${participant}"]`);
    const ms = document.querySelector(`[data-ms="${participant}"]`);
    if (ts.value === "" || ms.value === "") {
      throw new Error(`Bitte beide Punktzahlen für ${participant} eintragen.`);
    }
    scores[participant] = {
      ts_raw_points: Number(ts.value),
      ms_raw_points: Number(ms.value)
    };
  }
  return { matchday: Number(matchdaySelect.value), scores };
}

async function request(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "Unbekannter Fehler");
  return result;
}

form.addEventListener("submit", async event => {
  event.preventDefault();
  try {
    setStatus("Vorschau wird berechnet …");
    lastPayload = readPayload();
    const result = await request("/api/preview", lastPayload);
    previewRows.innerHTML = result.combined.results.map(row => `
      <tr>
        <td>${row.matchday_rank}</td><td>${row.name}</td>
        <td>${row.ts.points} (${row.ts.raw_points})</td>
        <td>${row.ms.points} (${row.ms.raw_points})</td>
        <td>${row.matchday_points}</td>
      </tr>
    `).join("");
    preview.hidden = false;
    setStatus("Vorschau erfolgreich geprüft.", "success");
  } catch (error) {
    setStatus(error.message, "error");
  }
});

saveButton.addEventListener("click", async () => {
  if (!lastPayload) return;
  const matchday = lastPayload.matchday;
  const verb = state.existing_matchdays.includes(matchday) ? "ersetzen" : "speichern";
  if (!window.confirm(`Spieltag ${matchday} wirklich ${verb}?`)) return;
  try {
    saveButton.disabled = true;
    setStatus("Spieltag wird gespeichert …");
    const result = await request("/api/save", {
      ...lastPayload,
      publish: publishCheckbox.checked
    });
    if (!state.existing_matchdays.includes(matchday)) {
      state.existing_matchdays.push(matchday);
    }
    updateWarning();
    setStatus(
      result.publication
        ? `Gespeichert und veröffentlicht: ${result.publication}`
        : "Spieltag wurde erfolgreich gespeichert.",
      "success"
    );
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    saveButton.disabled = false;
  }
});

async function initialize() {
  const response = await fetch("/api/state", { cache: "no-store" });
  state = await response.json();
  seasonLabel.textContent = state.season_label;
  matchdaySelect.innerHTML = Array.from({ length: 34 }, (_, index) => {
    const value = index + 1;
    return `<option value="${value}">Spieltag ${value}</option>`;
  }).join("");
  const nextMatchday = Math.min(34, Math.max(0, ...state.existing_matchdays) + 1);
  matchdaySelect.value = String(nextMatchday || 1);
  scoreRows.innerHTML = state.participants.map(name => `
    <tr>
      <td>${name}</td>
      <td><input type="number" min="0" required data-ts="${name}" aria-label="Tippspielpunkte ${name}"></td>
      <td><input type="number" required data-ms="${name}" aria-label="Managerspielpunkte ${name}"></td>
    </tr>
  `).join("");
  matchdaySelect.addEventListener("change", updateWarning);
  updateWarning();
}

initialize().catch(error => setStatus(error.message, "error"));
