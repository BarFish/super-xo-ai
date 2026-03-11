class Player:
    """
    Represents a human player.
    player_id: "p1" or "p2" - used to identify players on the frontend
    symbol: "X" or "O" (TTT) or "R"/"Y" (Connect Four display)
    """
    def __init__(self, name, symbol, player_id="p1"):
        self.name = name
        self.symbol = symbol
        self.player_id = player_id  # Used by frontend to color pieces

    def __str__(self):
        return f"{self.name} ({self.symbol})"

    def to_dict(self):
        """Convert player info to JSON for the frontend."""
        return {
            "name": self.name,
            "symbol": self.symbol,
            "player_id": self.player_id,
        }


class AIPlayer(Player):
    """
    AI player that uses the minimax algorithm with alpha-beta pruning.
    Alpha-beta pruning speeds up minimax by skipping branches that can't affect the result.
    """
    def __init__(self, symbol, opponent, player_id="p2", difficulty=5):
        super().__init__("Bot", symbol, player_id)
        self.opponent = opponent
        self.max_depth = difficulty  # Higher = smarter but slower

    def evaluate(self, board):
        """
        Board evaluation function - gives a score from the AI's perspective.
        Positive = good for AI, Negative = bad for AI.
        Uses the cell weights computed in board.py.
        """
        score = 0
        for r in range(board.height):
            for c in range(board.width):
                cell = board.board[r][c]
                if cell.value == self:
                    score += cell.weight
                elif cell.value == self.opponent:
                    score -= cell.weight
        return score

    def minimax(self, board, depth, alpha, beta, maximizing):
        """
        Minimax with alpha-beta pruning.
        - maximizing=True: AI's turn (tries to maximize score)
        - maximizing=False: Opponent's turn (tries to minimize score)
        - alpha/beta: pruning bounds
        """
        # Base cases: game over or max depth reached
        if board.is_game_over():
            winner = board.get_winner()
            if winner == self:
                return 10000 + depth   # Win quickly = better
            if winner is None:
                return 0               # Draw
            return -10000 - depth      # Lose late = less bad

        if depth == 0:
            return self.evaluate(board)  # Use heuristic at depth limit

        empty_cells = board.get_empty_cells()
        is_c4 = hasattr(board, '_get_row_for_move')  # Connect Four uses column as move

        if maximizing:
            max_eval = float('-inf')
            for row, col in empty_cells:
                move = col if is_c4 else (row, col)
                if board.make_move(move, self):
                    eval_score = self.minimax(board, depth - 1, alpha, beta, False)
                    board.undo_last_move(move)
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break  # Prune remaining branches
            return max_eval
        else:
            min_eval = float('inf')
            for row, col in empty_cells:
                move = col if is_c4 else (row, col)
                if board.make_move(move, self.opponent):
                    eval_score = self.minimax(board, depth - 1, alpha, beta, True)
                    board.undo_last_move(move)
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break  # Prune remaining branches
            return min_eval

    def get_move(self, board):
        """Find the best move for the AI using minimax."""
        best_score = float('-inf')
        best_move = None
        is_c4 = hasattr(board, '_get_row_for_move')

        for row, col in board.get_empty_cells():
            move = col if is_c4 else (row, col)
            if board.make_move(move, self):
                score = self.minimax(board, self.max_depth, float('-inf'), float('inf'), False)
                board.undo_last_move(move)
                if score > best_score:
                    best_score = score
                    best_move = move

        return best_move
