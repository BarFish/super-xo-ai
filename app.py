# app.py - Main Flask server
# Defines all the routes (URLs) that the frontend can talk to.
# Run with: python app.py

from flask import Flask, render_template, request, jsonify, session
from game_manager import game_manager
from matchmaking import matchmaker

app = Flask(__name__)
app.secret_key = "boardgame_secret_2024"  # Needed for Flask sessions

# ─────────────────────────────────────────────
# PAGE ROUTES - These render HTML templates
# ─────────────────────────────────────────────

@app.route("/")
def home():
    """Main page with game setup form."""
    return render_template("home.html")


@app.route("/game/<game_id>")
def game_page(game_id):
    """
    Game screen. The game_id identifies which game session to load.
    player_role is "p1" or "p2" - stored in URL query string.
    """
    player_role = request.args.get("role", "p1")
    game = game_manager.get_game(game_id)
    if not game:
        return "Game not found!", 404
    return render_template("game.html", game_id=game_id, player_role=player_role)


@app.route("/result/<game_id>")
def result_page(game_id):
    """End game screen showing winner and stats."""
    player_role = request.args.get("role", "p1")
    game = game_manager.get_game(game_id)
    if not game:
        return "Game not found!", 404
    return render_template("result.html", game_id=game_id, player_role=player_role)


# ─────────────────────────────────────────────
# API ROUTES - These return JSON data
# The frontend uses fetch() to call these
# ─────────────────────────────────────────────

@app.route("/api/start_game", methods=["POST"])
def start_game():
    """
    Create a new local game (vs Bot or 2-player local).
    Frontend sends: game_type, mode, player1_name, (optional) player2_name, ttt_size, ttt_win
    Returns: game_id and redirect URL
    """
    data = request.json

    game_type   = data.get("game_type", "TTT")
    mode        = data.get("mode", "bot")
    name1       = data.get("player1_name", "Player 1")
    name2       = data.get("player2_name", "Player 2")
    ttt_size    = int(data.get("ttt_size", 3))
    ttt_win     = int(data.get("ttt_win", 3))

    # Clamp win condition to board size (can't win more than the board is wide)
    ttt_win = min(ttt_win, ttt_size)

    game = game_manager.create_game(
        game_type=game_type,
        mode=mode,
        player1_name=name1,
        player2_name=name2 if mode == "local" else None,
        ttt_size=ttt_size,
        ttt_win=ttt_win,
    )

    return jsonify({
        "status": "ok",
        "game_id": game.game_id,
        "redirect": f"/game/{game.game_id}?role=p1"
    })


@app.route("/api/join_online", methods=["POST"])
def join_online():
    """
    Join the matchmaking queue for an online game.
    Returns immediately with status "waiting" or "matched".
    Frontend polls /api/check_match to find out when matched.
    """
    data = request.json
    game_type   = data.get("game_type", "TTT")
    player_name = data.get("player_name", "Player")
    ttt_size    = int(data.get("ttt_size", 3))
    ttt_win     = int(data.get("ttt_win", 3))

    result = matchmaker.join_queue(game_type, player_name, ttt_size, ttt_win)

    if result["status"] == "matched":
        return jsonify({
            "status": "matched",
            "game_id": result["game_id"],
            "player_role": result["player_role"],
            "redirect": f"/game/{result['game_id']}?role={result['player_role']}"
        })
    else:
        return jsonify({"status": "waiting"})


@app.route("/api/check_match", methods=["POST"])
def check_match():
    """
    Poll endpoint: called every 2 seconds by a waiting player.
    Returns "matched" with game_id once an opponent is found.
    """
    data = request.json
    game_type   = data.get("game_type", "TTT")
    player_name = data.get("player_name", "Player")

    result = matchmaker.check_match(game_type, player_name)

    if result["status"] == "matched":
        return jsonify({
            "status": "matched",
            "game_id": result["game_id"],
            "player_role": result["player_role"],
            "redirect": f"/game/{result['game_id']}?role={result['player_role']}"
        })
    return jsonify(result)


@app.route("/api/leave_queue", methods=["POST"])
def leave_queue():
    """Called when a waiting player navigates away."""
    data = request.json
    matchmaker.leave_queue(data.get("game_type"), data.get("player_name"))
    return jsonify({"status": "ok"})


@app.route("/api/game_state/<game_id>")
def game_state(game_id):
    """
    Return the current game state as JSON.
    The frontend calls this to render the board.
    Also polls this for online multiplayer sync.
    """
    game = game_manager.get_game(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404
    return jsonify(game.to_dict())


@app.route("/api/make_move", methods=["POST"])
def make_move():
    """
    Apply a player's move.
    For TTT: move = [row, col]
    For C4:  move = col (integer)
    Returns updated game state.
    """
    data = request.json
    game_id     = data.get("game_id")
    move_data   = data.get("move")
    player_role = data.get("player_role", "p1")

    game = game_manager.get_game(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    # Validate it's this player's turn (prevent cheating in online mode)
    if game.current_player.player_id != player_role:
        return jsonify({"error": "Not your turn"}), 403

    # Convert move format
    if game.game_type == "C4":
        move = int(move_data)
    else:
        move = tuple(move_data)  # [row, col] → (row, col)

    # Find which row the C4 piece would land in (for animation)
    drop_row = None
    if game.game_type == "C4":
        drop_row = game.board.get_drop_row(move)

    success = game.make_move(move)

    if not success:
        return jsonify({"error": "Invalid move"}), 400

    # Check if game ended after this move
    game.check_and_update_stats()

    state = game.to_dict()
    state["drop_row"] = drop_row  # Tell frontend where piece landed
    return jsonify(state)


@app.route("/api/ai_move", methods=["POST"])
def ai_move():
    """
    Ask the AI to make its move. Called by frontend after player moves.
    Only valid in "bot" mode.
    """
    data = request.json
    game_id = data.get("game_id")

    game = game_manager.get_game(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    if game.mode != "bot":
        return jsonify({"error": "Not a bot game"}), 400

    # Find drop row before move (for animation)
    drop_row = None
    if game.game_type == "C4":
        empty = game.board.get_empty_cells()
        if empty:
            # We'll get the actual move after AI plays
            pass

    move = game.get_ai_move()

    if move is None:
        return jsonify({"error": "No move available"}), 400

    # Get drop row for the move the AI actually made
    if game.game_type == "C4":
        col = move
        # The piece was placed, find topmost occupied cell in that column
        for r in range(game.board.height):
            if not game.board.board[r][col].is_playable():
                drop_row = r
                break

    game.check_and_update_stats()

    state = game.to_dict()
    state["ai_move"] = move if game.game_type == "C4" else list(move)
    state["drop_row"] = drop_row
    return jsonify(state)


@app.route("/api/timeout", methods=["POST"])
def timeout():
    """Called when a player's move timer hits zero."""
    data = request.json
    game_id           = data.get("game_id")
    timed_out_player  = data.get("player_role")

    game = game_manager.get_game(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    game.handle_timeout(timed_out_player)
    return jsonify(game.to_dict())


@app.route("/api/resign", methods=["POST"])
def resign():
    """Called when a player clicks the Resign button."""
    data = request.json
    game_id       = data.get("game_id")
    player_role   = data.get("player_role")

    game = game_manager.get_game(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    game.handle_resign(player_role)
    return jsonify(game.to_dict())


@app.route("/api/restart", methods=["POST"])
def restart():
    """Reset the board for a rematch (same players, same settings, stats preserved)."""
    data = request.json
    game_id = data.get("game_id")

    game = game_manager.get_game(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    game.reset()
    return jsonify(game.to_dict())


# ─────────────────────────────────────────────
# RUN THE SERVER
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("🎮 Game server starting at http://100.10.102.24:5000")
    app.run(host="0.0.0.0", debug=True, port=5000)
