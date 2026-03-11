// home.js — Home page logic

let selectedGame   = "TTT";
let selectedMode   = "bot";
let tttPreset      = "3x3";   // "3x3" or "6x6"
let pollInterval   = null;
let playerName     = "";

// ── Restore saved name from localStorage ────────────────────────────────────
// This persists the name across page visits so the player doesn't retype it.
const nameInput = document.getElementById("player-name");
const savedName = localStorage.getItem("playerName");
if (savedName) nameInput.value = savedName;

// Save name whenever it changes
nameInput.addEventListener("input", () => {
  localStorage.setItem("playerName", nameInput.value.trim());
});

// ── Toggle button groups ─────────────────────────────────────────────────────

function setupToggleGroup(groupId, onChange) {
  const group = document.getElementById(groupId);
  if (!group) return;
  group.querySelectorAll(".toggle-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      group.querySelectorAll(".toggle-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      onChange(btn.dataset.value);
    });
  });
}

setupToggleGroup("game-select", (value) => {
  selectedGame = value;
  document.getElementById("ttt-settings").style.display = value === "TTT" ? "block" : "none";
});

setupToggleGroup("mode-select", (value) => {
  selectedMode = value;
  document.getElementById("p2-section").style.display = value === "local" ? "block" : "none";
});

setupToggleGroup("ttt-preset-select", (value) => {
  tttPreset = value;
});

// ── Form submit ───────────────────────────────────────────────────────────────

document.getElementById("setup-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  playerName = nameInput.value.trim();
  if (!playerName) { alert("Please enter your name!"); return; }
  localStorage.setItem("playerName", playerName);  // save on submit too

  if (selectedMode === "online") joinOnlineQueue();
  else startLocalGame();
});

// ── Resolve TTT settings from preset ─────────────────────────────────────────

function getTTTSettings() {
  if (tttPreset === "6x6") return { ttt_size: 6, ttt_win: 4 };
  if (tttPreset === "8x8") return { ttt_size: 8, ttt_win: 4 };
  return { ttt_size: 3, ttt_win: 3 };
}

// ── Start local / bot game ────────────────────────────────────────────────────

async function startLocalGame() {
  const { ttt_size, ttt_win } = getTTTSettings();
  const p2name = document.getElementById("player2-name").value.trim() || "Player 2";

  const body = {
    game_type: selectedGame,
    mode: selectedMode,
    player1_name: playerName,
    player2_name: p2name,
    ttt_size,
    ttt_win,
  };

  try {
    const res  = await fetch("/api/start_game", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (data.status === "ok") window.location.href = data.redirect;
    else alert("Error: " + JSON.stringify(data));
  } catch (err) {
    console.error(err);
    alert("Could not connect to server.");
  }
}

// ── Online matchmaking ────────────────────────────────────────────────────────

async function joinOnlineQueue() {
  const { ttt_size, ttt_win } = getTTTSettings();

  document.getElementById("setup-form").style.display  = "none";
  document.getElementById("waiting-screen").style.display = "flex";

  try {
    const res  = await fetch("/api/join_online", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_type: selectedGame, player_name: playerName, ttt_size, ttt_win }),
    });
    const data = await res.json();

    if (data.status === "matched") {
      clearInterval(pollInterval);
      window.location.href = data.redirect;
    } else {
      pollInterval = setInterval(pollForMatch, 2000);
    }
  } catch (err) {
    console.error(err);
    showForm();
    alert("Could not connect to server.");
  }
}

async function pollForMatch() {
  try {
    const res  = await fetch("/api/check_match", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_type: selectedGame, player_name: playerName }),
    });
    const data = await res.json();
    if (data.status === "matched") {
      clearInterval(pollInterval);
      window.location.href = data.redirect;
    }
  } catch (err) { console.error("Poll error:", err); }
}

document.getElementById("cancel-wait").addEventListener("click", async () => {
  clearInterval(pollInterval);
  await fetch("/api/leave_queue", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ game_type: selectedGame, player_name: playerName }),
  });
  showForm();
});

function showForm() {
  document.getElementById("waiting-screen").style.display = "none";
  document.getElementById("setup-form").style.display = "flex";
}
