from game_logic.board import TTTBoard, ConnectFourBoard
from game_logic.player import Player, AIPlayer


class Game:
    """
    Manages a single game session.
    Tracks players, current turn, and win/loss/draw stats.
    """

    def __init__(self, game_type, mode, player1_name, player2_name=None,
                 ttt_size=3, ttt_win=3, game_id=None):
        """
        game_type: "TTT" or "C4"
        mode: "bot", "local", or "online"
        player1_name: Name entered on home screen
        player2_name: Name of second player (or "Bot" if vs AI)
        ttt_size: Board size for TTT (3-8)
        ttt_win: Win condition for TTT (3-5)
        game_id: Unique ID used to look up this game
        """
        self.game_id = game_id
        self.game_type = game_type
        self.mode = mode

        # Create the right board type
        if game_type == "C4":
            self.board = ConnectFourBoard()
        else:
            # Clamp win condition to board size
            ttt_win = min(ttt_win, ttt_size)
            self.board = TTTBoard(size=ttt_size, win_condition=ttt_win)

        # Create Player 1
        symbol1 = "X" if game_type == "TTT" else "R"
        self.p1 = Player(player1_name, symbol1, player_id="p1")

        # Create Player 2 (either AI or human)
        symbol2 = "O" if game_type == "TTT" else "Y"
        if mode == "bot":
            self.p2 = AIPlayer(symbol2, self.p1, player_id="p2", difficulty=5)
        else:
            name2 = player2_name if player2_name else "Player 2"
            self.p2 = Player(name2, symbol2, player_id="p2")

        # Track whose turn it is
        self.current_player = self.p1

        # Session stats - persist across restarts
        self.stats = {
            "p1": {"wins": 0, "losses": 0, "draws": 0},
            "p2": {"wins": 0, "losses": 0, "draws": 0},
        }

        # Track if game ended by timeout
        self.timed_out = False
        self.resigned = False

    def switch_player(self):
        """Swap current player between p1 and p2."""
        self.current_player = self.p2 if self.current_player == self.p1 else self.p1

    def make_move(self, move):
        """
        Apply a move from the current player.
        Returns True if the move was valid.
        """
        success = self.board.make_move(move, self.current_player)
        if success and not self.board.is_game_over():
            self.switch_player()
        return success

    def get_ai_move(self):
        """Ask the AI player to calculate and make its move."""
        if isinstance(self.current_player, AIPlayer):
            move = self.current_player.get_move(self.board)
            if move is not None:
                self.make_move(move)
            return move
        return None

    def handle_timeout(self, timed_out_player_id):
        """Called when a player's timer runs out - they automatically lose."""
        self.timed_out = True
        if timed_out_player_id == "p1":
            self.board.winner = self.p2
        else:
            self.board.winner = self.p1
        self._update_stats()

    def handle_resign(self, resigning_player_id):
        """Called when a player clicks Resign."""
        self.resigned = True
        if resigning_player_id == "p1":
            self.board.winner = self.p2
        else:
            self.board.winner = self.p1
        self._update_stats()

    def _update_stats(self):
        """Update win/loss/draw counters after a game ends."""
        winner = self.board.get_winner()
        if self.board.is_draw:
            self.stats["p1"]["draws"] += 1
            self.stats["p2"]["draws"] += 1
        elif winner == self.p1:
            self.stats["p1"]["wins"] += 1
            self.stats["p2"]["losses"] += 1
        elif winner == self.p2:
            self.stats["p2"]["wins"] += 1
            self.stats["p1"]["losses"] += 1

    def check_and_update_stats(self):
        """Call after each move to auto-update stats when game ends normally."""
        if self.board.is_game_over():
            self._update_stats()

    def reset(self):
        """Reset the board for a rematch, keeping the same players and stats."""
        if self.game_type == "C4":
            self.board = ConnectFourBoard()
        else:
            self.board = TTTBoard(
                size=self.board.width,
                win_condition=self.board.win_condition
            )
        # If AIPlayer, update opponent reference (player objects stay same)
        if isinstance(self.p2, AIPlayer):
            self.p2.opponent = self.p1
        self.current_player = self.p1
        self.timed_out = False
        self.resigned = False

    def to_dict(self):
        """Serialize game state to JSON for the frontend."""
        winner = self.board.get_winner()
        return {
            "game_id": self.game_id,
            "game_type": self.game_type,
            "mode": self.mode,
            "board": self.board.to_dict(),
            "current_player": self.current_player.to_dict(),
            "p1": self.p1.to_dict(),
            "p2": self.p2.to_dict(),
            "winner": winner.to_dict() if winner else None,
            "is_draw": self.board.is_draw,
            "is_game_over": self.board.is_game_over(),
            "timed_out": self.timed_out,
            "resigned": self.resigned,
            "stats": self.stats,
        }
