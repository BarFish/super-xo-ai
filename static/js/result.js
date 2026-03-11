// result.js — Result (Game Over) screen
// Loads the final game state, shows winner, stats, and confetti on a win.

const root = document.getElementById("game-root");
const GAME_ID     = root.dataset.gameId;
const PLAYER_ROLE = root.dataset.playerRole;

// ─────────────────────────────────────────────
// Load result on page load
// ─────────────────────────────────────────────

async function loadResult() {
  try {
    const res = await fetch(`/api/game_state/${GAME_ID}`);
    const state = await res.json();
    renderResult(state);
  } catch (err) {
    console.error("Result load error:", err);
  }
}

function renderResult(state) {
  const icon    = document.getElementById("result-icon");
  const title   = document.getElementById("result-title");
  const winner  = document.getElementById("result-winner");
  const reason  = document.getElementById("result-reason");

  // Determine outcome message
  if (state.is_draw) {
    icon.textContent  = "🤝";
    title.textContent = "IT'S A DRAW";
    winner.textContent = "Nobody wins this time!";
    winner.style.color = "var(--text-dim)";
  } else if (state.winner) {
    const isMyWin = state.winner.player_id === PLAYER_ROLE;
    icon.textContent   = isMyWin ? "🏆" : "😔";
    title.textContent  = isMyWin ? "YOU WIN!" : "GAME OVER";
    winner.textContent = `${state.winner.name} wins!`;
    winner.style.color = state.winner.player_id === "p1" ? "var(--accent1)" : "var(--accent2)";

    if (isMyWin) {
      launchConfetti();
    }
  }

  // Show reason (resign/timeout)
  if (state.resigned) {
    reason.textContent = "(opponent resigned)";
  } else if (state.timed_out) {
    reason.textContent = "(time ran out)";
  }

  // Hide rematch button for online games — rematching online requires a new queue
  if (state.mode === "online") {
    document.getElementById("restart-btn").style.display = "none";
  }

  // Stats table
  document.getElementById("stats-p1-name").textContent   = state.p1.name;
  document.getElementById("stats-p1-wins").textContent   = state.stats.p1.wins;
  document.getElementById("stats-p1-losses").textContent = state.stats.p1.losses;
  document.getElementById("stats-p1-draws").textContent  = state.stats.p1.draws;

  document.getElementById("stats-p2-name").textContent   = state.p2.name;
  document.getElementById("stats-p2-wins").textContent   = state.stats.p2.wins;
  document.getElementById("stats-p2-losses").textContent = state.stats.p2.losses;
  document.getElementById("stats-p2-draws").textContent  = state.stats.p2.draws;
}

// ─────────────────────────────────────────────
// Restart / Rematch button
// ─────────────────────────────────────────────

document.getElementById("restart-btn").addEventListener("click", async () => {
  try {
    const res = await fetch("/api/restart", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_id: GAME_ID }),
    });

    const state = await res.json();
    // Go back to the game screen
    window.location.href = `/game/${GAME_ID}?role=${PLAYER_ROLE}`;
  } catch (err) {
    console.error("Restart error:", err);
  }
});

// ─────────────────────────────────────────────
// Confetti animation (canvas-based)
// ─────────────────────────────────────────────

function launchConfetti() {
  const canvas = document.getElementById("confetti-canvas");
  const ctx    = canvas.getContext("2d");

  canvas.width  = window.innerWidth;
  canvas.height = window.innerHeight;

  const pieces  = [];
  const colors  = ["#ff3f6c", "#ffd700", "#4488ff", "#44ffaa", "#ff8800", "#cc44ff"];
  const count   = 120;

  // Create confetti particles
  for (let i = 0; i < count; i++) {
    pieces.push({
      x:      Math.random() * canvas.width,
      y:      Math.random() * canvas.height - canvas.height,
      w:      Math.random() * 12 + 6,
      h:      Math.random() * 6 + 4,
      color:  colors[Math.floor(Math.random() * colors.length)],
      speed:  Math.random() * 3 + 2,
      angle:  Math.random() * 360,
      spin:   (Math.random() - 0.5) * 5,
      drift:  (Math.random() - 0.5) * 1.5,
      alpha:  1,
    });
  }

  let frame;
  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    let allGone = true;
    pieces.forEach(p => {
      p.y     += p.speed;
      p.x     += p.drift;
      p.angle += p.spin;
      p.alpha  = Math.max(0, 1 - p.y / canvas.height);

      if (p.y < canvas.height) allGone = false;

      ctx.save();
      ctx.globalAlpha = p.alpha;
      ctx.translate(p.x + p.w / 2, p.y + p.h / 2);
      ctx.rotate((p.angle * Math.PI) / 180);
      ctx.fillStyle = p.color;
      ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
      ctx.restore();
    });

    if (!allGone) {
      frame = requestAnimationFrame(animate);
    }
  }

  animate();

  // Stop confetti after 4 seconds
  setTimeout(() => cancelAnimationFrame(frame), 4000);
}

// ─────────────────────────────────────────────
// Start
// ─────────────────────────────────────────────

loadResult();
