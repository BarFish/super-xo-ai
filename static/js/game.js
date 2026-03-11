// game.js — Game screen logic

const root        = document.getElementById("game-root");
const GAME_ID     = root.dataset.gameId;
const PLAYER_ROLE = root.dataset.playerRole; // "p1" or "p2"

const TIMER_SECONDS = 30;
let timerValue     = TIMER_SECONDS;
let timerInterval  = null;
let gameOver       = false;
let lastTurnOwner  = null;  // which player_id the current timer is counting for
let onlinePollInterval = null;

// ─── Init ─────────────────────────────────────────────────────────────────────

async function init() {
  const state = await fetchState();
  if (!state) return;
  renderAll(state);

  // Bot: if AI somehow goes first
  if (state.mode === "bot" && !state.is_game_over &&
      state.current_player.player_id !== PLAYER_ROLE) {
    requestAIMove();
  }

  // Online: poll so both players see each other's moves
  if (state.mode === "online") {
    onlinePollInterval = setInterval(pollGameState, 1500);
  }
}

async function fetchState() {
  try {
    const res = await fetch(`/api/game_state/${GAME_ID}`);
    return await res.json();
  } catch (e) { console.error(e); return null; }
}

// ─── Render ───────────────────────────────────────────────────────────────────

function renderAll(state) {
  renderSidebar(state);
  renderTurnIndicator(state);
  renderInfoCards(state);

  if (state.game_type === "TTT") renderTTTBoard(state);
  else renderC4Board(state);

  // Game over: highlight winning cells, wait 2.5s, then go to results
  if (state.is_game_over && !gameOver) {
    gameOver = true;
    stopTimer();
    stopOnlinePolling();

    if (!state.is_draw && state.board.winning_cells && state.board.winning_cells.length > 0) {
      highlightWinningCells(state);
      setTimeout(() => {
        window.location.href = `/result/${GAME_ID}?role=${PLAYER_ROLE}`;
      }, 2500);
    } else {
      setTimeout(() => {
        window.location.href = `/result/${GAME_ID}?role=${PLAYER_ROLE}`;
      }, 1000);
    }
  }
}

// ─── Highlight winning cells ──────────────────────────────────────────────────

function highlightWinningCells(state) {
  const cells = state.board.winning_cells; // list of [row, col]
  if (!cells || cells.length === 0) return;

  if (state.game_type === "TTT") {
    const allCells = document.querySelectorAll(".ttt-cell");
    cells.forEach(([r, c]) => {
      const idx  = r * state.board.width + c;
      const el   = allCells[idx];
      if (el) el.classList.add("winner-cell");
    });
  } else {
    cells.forEach(([r, c]) => {
      const el = document.getElementById(`c4-${r}-${c}`);
      if (el) el.classList.add("winner-cell");
    });
  }
}

function renderSidebar(state) {
  document.getElementById("p1-name").textContent    = state.p1.name;
  document.getElementById("p2-name").textContent    = state.p2.name;
  document.getElementById("p1-symbol").textContent  = state.p1.symbol;
  document.getElementById("p2-symbol").textContent  = state.p2.symbol;
  document.getElementById("p1-wins").textContent    = state.stats.p1.wins;
  document.getElementById("p1-losses").textContent  = state.stats.p1.losses;
  document.getElementById("p1-draws").textContent   = state.stats.p1.draws;
  document.getElementById("p2-wins").textContent    = state.stats.p2.wins;
  document.getElementById("p2-losses").textContent  = state.stats.p2.losses;
  document.getElementById("p2-draws").textContent   = state.stats.p2.draws;
  const p1Turn = state.current_player.player_id === "p1";
  document.getElementById("p1-card").classList.toggle("active-turn",  p1Turn && !state.is_game_over);
  document.getElementById("p2-card").classList.toggle("active-turn", !p1Turn && !state.is_game_over);
}

function renderTurnIndicator(state) {
  const el = document.getElementById("turn-text");
  if (state.is_game_over)
    el.textContent = state.is_draw ? "It's a draw!" : `${state.winner.name} wins! 🎉`;
  else
    el.textContent = `${state.current_player.name}'s Turn`;
}

function renderInfoCards(state) {
  document.getElementById("game-type-display").textContent = state.game_type;
  const modes = { bot: "vs Bot", local: "2 Players", online: "Online" };
  document.getElementById("mode-display").textContent = modes[state.mode] || state.mode;
  document.getElementById("move-count").textContent =
    state.board.grid.flat().filter(c => c.symbol !== null).length;
}

// ─── Timer ────────────────────────────────────────────────────────────────────
// Rules:
//  • bot mode:    only run when it is the HUMAN player's turn (never during AI thinking)
//  • local mode:  always run for whoever's turn it is (both players share the screen)
//  • online mode: always run for whoever's turn it is (each browser enforces its own timeout)
// The timer only resets when lastTurnOwner changes — prevents restarts on every render.

function updateTimer(state) {
  if (state.is_game_over) { stopTimer(); lastTurnOwner = null; return; }

  const nowTurn = state.current_player.player_id;
  const isAITurn = state.mode === "bot" && nowTurn !== PLAYER_ROLE;

  if (isAITurn) {
    // Never count down against the bot
    stopTimer();
    lastTurnOwner = nowTurn;
    return;
  }

  if (nowTurn !== lastTurnOwner) {
    lastTurnOwner = nowTurn;
    resetTimer();
  }
}

function resetTimer() {
  stopTimer();
  timerValue = TIMER_SECONDS;
  updateTimerDisplay();
  timerInterval = setInterval(tickTimer, 1000);
}

function stopTimer() {
  if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
}

function tickTimer() {
  timerValue--;
  updateTimerDisplay();
  if (timerValue <= 0) { stopTimer(); handleTimeout(); }
}

function updateTimerDisplay() {
  const bar  = document.getElementById("timer-bar");
  const text = document.getElementById("timer-text");
  bar.style.setProperty("--timer-pct", (timerValue / TIMER_SECONDS * 100) + "%");
  text.textContent = timerValue;
  const warn = timerValue <= 15, danger = timerValue <= 8;
  bar.classList.toggle("warning",  warn && !danger);
  bar.classList.toggle("danger",   danger);
  text.classList.toggle("warning", warn && !danger);
  text.classList.toggle("danger",  danger);
}

async function handleTimeout() {
  const timedOutRole = lastTurnOwner || PLAYER_ROLE;
  try {
    const res = await fetch("/api/timeout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_id: GAME_ID, player_role: timedOutRole }),
    });
    renderAll(await res.json());
  } catch (e) { console.error(e); }
}

// ─── TTT Board ────────────────────────────────────────────────────────────────

function renderTTTBoard(state) {
  const container  = document.getElementById("board-container");
  const grid       = state.board.grid;
  const rows       = grid.length, cols = grid[0].length;
  const isGameOver = state.is_game_over;

  // local: always allow move for whoever's turn; bot/online: only MY role
  const myRoleMatches = state.current_player.player_id === PLAYER_ROLE;
  const canClick = !isGameOver && (state.mode === "local" || myRoleMatches);

  let board = document.querySelector(".ttt-board");
  if (!board) {
    board = document.createElement("div");
    board.className = "ttt-board";
    board.style.gridTemplateColumns = `repeat(${cols}, var(--cell-size))`;
    container.innerHTML = "";
    container.appendChild(board);
  }
  board.innerHTML = "";

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const cell = document.createElement("div");
      cell.className = "ttt-cell";
      const data = grid[r][c];
      if (data.symbol) {
        cell.textContent = data.symbol;
        cell.classList.add("occupied", data.player_id);
      } else if (canClick) {
        cell.addEventListener("click", () =>
          handleTTTClick(r, c, state.current_player.player_id));
      }
      board.appendChild(cell);
    }
  }
  updateTimer(state);
}

// ─── C4 Board ─────────────────────────────────────────────────────────────────

function renderC4Board(state) {
  const container  = document.getElementById("board-container");
  const grid       = state.board.grid;
  const rows       = grid.length, cols = grid[0].length;
  const isGameOver = state.is_game_over;

  const myRoleMatches = state.current_player.player_id === PLAYER_ROLE;
  const canClick = !isGameOver && (state.mode === "local" || myRoleMatches);

  let wrapper = document.querySelector(".c4-board-wrapper");
  if (!wrapper) {
    container.innerHTML = "";
    wrapper = document.createElement("div");
    wrapper.className = "c4-board-wrapper";

    const colBtns = document.createElement("div");
    colBtns.className = "c4-column-buttons";
    for (let c = 0; c < cols; c++) {
      const btn = document.createElement("button");
      btn.className = "c4-col-btn";
      btn.textContent = "▼";
      btn.dataset.col = c;
      btn.addEventListener("click", () =>
        handleC4Click(c, wrapper.__currentPlayerRole));
      colBtns.appendChild(btn);
    }

    const board = document.createElement("div");
    board.className = "c4-board";
    board.style.gridTemplateColumns = `repeat(${cols}, 64px)`;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const cell = document.createElement("div");
        cell.className = "c4-cell";
        cell.id = `c4-${r}-${c}`;
        board.appendChild(cell);
      }
    }
    wrapper.appendChild(colBtns);
    wrapper.appendChild(board);
    container.appendChild(wrapper);
  }

  wrapper.__currentPlayerRole = state.current_player.player_id;

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const cell = document.getElementById(`c4-${r}-${c}`);
      if (!cell) continue;
      cell.className = "c4-cell";
      if (grid[r][c].player_id) cell.classList.add(grid[r][c].player_id);
    }
  }

  document.querySelectorAll(".c4-col-btn").forEach(btn => {
    btn.disabled = !canClick;
    btn.style.opacity = canClick ? "1" : "0.3";
  });

  updateTimer(state);
}

// ─── Move handlers ────────────────────────────────────────────────────────────

async function handleTTTClick(row, col, actingRole) {
  const state = await sendMove([row, col], actingRole);
  if (!state) return;

  const cells = document.querySelectorAll(".ttt-cell");
  const idx   = row * state.board.width + col;
  if (cells[idx]) {
    cells[idx].classList.add("just-placed");
    setTimeout(() => cells[idx].classList.remove("just-placed"), 400);
  }
  renderAll(state);
  if (state.mode === "bot" && !state.is_game_over) requestAIMove();
}

async function handleC4Click(col, actingRole) {
  const state = await sendMove(col, actingRole || PLAYER_ROLE);
  if (!state) return;

  if (state.drop_row != null) {
    const cell = document.getElementById(`c4-${state.drop_row}-${col}`);
    if (cell) {
      cell.classList.add("dropping");
      setTimeout(() => cell.classList.remove("dropping"), 500);
    }
  }
  renderAll(state);
  if (state.mode === "bot" && !state.is_game_over) requestAIMove();
}

async function sendMove(move, playerRole) {
  lastTurnOwner = null;  // cleared so updateTimer fires a fresh countdown after this move
  stopTimer();
  try {
    const res = await fetch("/api/make_move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_id: GAME_ID, move, player_role: playerRole }),
    });
    if (!res.ok) { console.warn("Move rejected:", (await res.json()).error); return null; }
    return await res.json();
  } catch (e) { console.error(e); return null; }
}

// ─── AI move ──────────────────────────────────────────────────────────────────

async function requestAIMove() {
  document.getElementById("ai-overlay").style.display = "flex";
  await new Promise(r => setTimeout(r, 1000));  // 1 second pause so player can see the board
  try {
    const res   = await fetch("/api/ai_move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_id: GAME_ID }),
    });
    const state = await res.json();
    document.getElementById("ai-overlay").style.display = "none";

    // Animate AI piece
    if (state.game_type === "C4" && state.drop_row != null) {
      const cell = document.getElementById(`c4-${state.drop_row}-${state.ai_move}`);
      if (cell) { cell.classList.add("dropping"); setTimeout(() => cell.classList.remove("dropping"), 500); }
    } else if (Array.isArray(state.ai_move)) {
      const [r, c] = state.ai_move;
      const cells  = document.querySelectorAll(".ttt-cell");
      const idx    = r * state.board.width + c;
      if (cells[idx]) { cells[idx].classList.add("just-placed"); setTimeout(() => cells[idx].classList.remove("just-placed"), 400); }
    }
    renderAll(state);
  } catch (e) {
    document.getElementById("ai-overlay").style.display = "none";
    console.error(e);
  }
}

// ─── Online polling ───────────────────────────────────────────────────────────
// Poll when it's the opponent's turn (lastTurnOwner !== PLAYER_ROLE).
// Also always poll when lastTurnOwner is null (fresh page load) so both
// players see the board immediately on connect.

async function pollGameState() {
  if (lastTurnOwner === PLAYER_ROLE) return; // it's my turn, I'm the one clicking
  const state = await fetchState();
  if (!state) return;
  renderAll(state);
  if (state.is_game_over) stopOnlinePolling();
}

function stopOnlinePolling() {
  if (onlinePollInterval) { clearInterval(onlinePollInterval); onlinePollInterval = null; }
}

// ─── Resign ───────────────────────────────────────────────────────────────────

document.getElementById("resign-btn").addEventListener("click", async () => {
  if (!confirm("Are you sure you want to resign?")) return;
  stopTimer();
  // local: resign for whoever's turn it is; bot/online: resign for this browser's player
  const role = (lastTurnOwner &&
    document.getElementById("mode-display").textContent === "2 Players")
    ? lastTurnOwner : PLAYER_ROLE;
  try {
    const res = await fetch("/api/resign", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_id: GAME_ID, player_role: role }),
    });
    renderAll(await res.json());
  } catch (e) { console.error(e); }
});

init();
