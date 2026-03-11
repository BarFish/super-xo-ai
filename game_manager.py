# game_manager.py - Manages all active game sessions
# Acts like a database in memory - stores game objects by their ID.

import uuid
from game_logic.game import Game


class GameManager:
    """
    Stores and retrieves all active games.
    In a real production app you'd use a database,
    but for a school project, a dictionary works great!
    """

    def __init__(self):
        # Dictionary mapping game_id -> Game object
        self.games = {}

    def create_game(self, game_type, mode, player1_name,
                    player2_name=None, ttt_size=3, ttt_win=3):
        """
        Create a new game and store it.
        Returns the Game object.
        """
        game_id = str(uuid.uuid4())[:8]  # Short random ID like "a3f8bc12"
        game = Game(
            game_type=game_type,
            mode=mode,
            player1_name=player1_name,
            player2_name=player2_name,
            ttt_size=ttt_size,
            ttt_win=ttt_win,
            game_id=game_id,
        )
        self.games[game_id] = game
        return game

    def get_game(self, game_id):
        """Look up a game by ID. Returns None if not found."""
        return self.games.get(game_id)

    def remove_game(self, game_id):
        """Delete a game (e.g., when both players leave)."""
        if game_id in self.games:
            del self.games[game_id]


# Singleton - one GameManager shared across the entire app
game_manager = GameManager()
