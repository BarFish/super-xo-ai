# matchmaking.py - Simple online matchmaking system
# When two players want to play the same game online, we pair them up.

from game_manager import game_manager


class Matchmaker:
    """
    Manages a queue of players waiting for an online opponent.
    
    How it works:
    1. Player A clicks "Online" for TTT → added to waiting queue
    2. Player B clicks "Online" for TTT → matched with Player A → game starts
    3. Both players get the same game_id and can play against each other
    """

    def __init__(self):
        # Separate queues for each game type
        # Each entry is a dict: {"player_name": ..., "ttt_size": ..., "ttt_win": ...}
        self.waiting = {
            "TTT": [],
            "C4": [],
        }

    def join_queue(self, game_type, player_name, ttt_size=3, ttt_win=3):
        """
        Add a player to the waiting queue.
        If someone is already waiting for the same game, start a match!

        Returns:
        - {"status": "waiting"} if no opponent yet
        - {"status": "matched", "game_id": "abc123", "player_role": "p2"} if matched immediately
        """
        queue = self.waiting.get(game_type, [])

        # Look for a waiting player who hasn't been matched yet
        for entry in queue:
            if entry["matched_game_id"] is None and entry["player_name"] != player_name:
                # Found an unmatched opponent — create the game
                game = game_manager.create_game(
                    game_type=game_type,
                    mode="online",
                    player1_name=entry["player_name"],   # first waiter is P1
                    player2_name=player_name,             # new joiner is P2
                    ttt_size=entry.get("ttt_size", ttt_size),
                    ttt_win=entry.get("ttt_win", ttt_win),
                )
                # Write game_id into the waiting entry so P1's next poll finds it.
                # We do NOT remove the entry here — check_match removes it after P1 reads it.
                entry["matched_game_id"] = game.game_id

                return {
                    "status": "matched",
                    "game_id": game.game_id,
                    "player_role": "p2",
                }

        # No unmatched opponent — add this player to the queue
        entry = {
            "player_name": player_name,
            "ttt_size": ttt_size,
            "ttt_win": ttt_win,
            "matched_game_id": None,
        }
        queue.append(entry)
        self.waiting[game_type] = queue
        return {"status": "waiting"}

    def check_match(self, game_type, player_name):
        """
        Poll to see if a waiting player has been matched.
        Called every 2 seconds by the frontend while on the waiting screen.
        Once the match is confirmed, the entry is removed from the queue.
        """
        queue = self.waiting.get(game_type, [])
        for entry in queue:
            if entry["player_name"] == player_name:
                if entry["matched_game_id"]:
                    game_id = entry["matched_game_id"]
                    # Now safe to remove — P1 has read the result
                    queue.remove(entry)
                    return {
                        "status": "matched",
                        "game_id": game_id,
                        "player_role": "p1",
                    }
                return {"status": "waiting"}
        return {"status": "not_found"}

    def leave_queue(self, game_type, player_name):
        """Remove a player from the queue (e.g., they navigated away)."""
        queue = self.waiting.get(game_type, [])
        self.waiting[game_type] = [e for e in queue if e["player_name"] != player_name]


# Singleton - shared across the entire app
matchmaker = Matchmaker()
