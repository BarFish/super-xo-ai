class Player:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    def get_move(self, board):
        pass

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class AIPlayer(Player):
    def __init__(self, symbol, opponent):
        super().__init__("AI", symbol)
        self.opponent = opponent
        self.max_depth = 5

    def evaluate(self, board):
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
        if board.is_game_over():
            winner = board.get_winner()
            if winner == self: 
                return 10000 + depth
            if winner is None: 
                return 0
            return -10000 - depth

        if depth == 0:
            return self.evaluate(board)

        empty_cells = board.get_empty_cells()
        
        if maximizing:
            max_eval = float('-inf')
            for row, col in empty_cells:
                move = col if hasattr(board, '_get_row_for_move') else (row, col)
                if board.make_move(move, self):
                    eval = self.minimax(board, depth - 1, alpha, beta, False)
                    board.undo_last_move(move)
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha: break
            return max_eval
        else:
            min_eval = float('inf')
            for row, col in empty_cells:
                move = col if hasattr(board, '_get_row_for_move') else (row, col)
                if board.make_move(move, self.opponent):
                    eval = self.minimax(board, depth - 1, alpha, beta, True)
                    board.undo_last_move(move)
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha: break
            return min_eval

    def get_move(self, board):
        best_score = float('-inf')
        best_move = None
        
        for row, col in board.get_empty_cells():
            move = col if hasattr(board, '_get_row_for_move') else (row, col)
            
            if board.make_move(move, self):
                score = self.minimax(board, self.max_depth, float('-inf'), float('inf'), False)
                board.undo_last_move(move)
                
                if score > best_score:
                    best_score = score
                    best_move = move
        
        return best_move