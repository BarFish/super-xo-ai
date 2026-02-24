from classes import Board
import random

class Player:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    def get_move(self, board):
        while True:
            try:
                move = input(f"{self}, enter your move (row col): ")
                row, col = map(int, move.split())
                if 0 <= row < board.height and 0 <= col < board.width:
                    return row, col
                else:
                    print("Invalid move. Please enter row and column within the board dimensions.")
            except ValueError:
                print("Invalid input. Please enter row and column as integers separated by a space.")


    def __str__(self):
        return f"{self.name} ({self.symbol})"


class AIPlayer(Player):
    def __init__(self, symbol, opponent):
        super().__init__(f"AI", symbol)
        self.opponent = opponent

    def get_move(self, board):
        best_score = float('-inf')
        best_move = None
        alpha = float('-inf')
        beta = float('inf')
        for row, col in board.get_empty_cells():
            board.make_move(row, col, self)
            score = self.minimax(board, depth=5, alpha=alpha, beta=beta, maximizing_player=False)
            board.undo_last_move(row, col)
            if score > best_score:
                best_score = score
                best_move = (row, col)
            alpha = max(alpha, best_score)
        return best_move
    
    def evaluate(self, board):
        sum_evaluation = 0
        for row in board.board:
            for cell in row:
                if cell.value == self:
                    sum_evaluation += cell.evaluation
                elif cell.value is not None:
                    sum_evaluation -= cell.evaluation
        return sum_evaluation
    
    def minimax(self, board, depth, alpha, beta, maximizing_player):
        if board.is_game_over():
            if board.get_winner() == self:
                return 100000 - depth
            elif board.get_winner() is None:
                return 0
            else:
                return -100000 + depth
            
        if depth == 0:
            return self.evaluate(board)
        
        if maximizing_player:
            max_eval = float('-inf')
            for row, col in board.get_empty_cells():
                board.make_move(row, col, self)
                eval = self.minimax(board, depth - 1, alpha, beta, False)
                board.undo_last_move(row, col)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for row, col in board.get_empty_cells():
                board.make_move(row, col, self.opponent)
                eval = self.minimax(board, depth - 1, alpha, beta, True)
                board.undo_last_move(row, col)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval


class Game:
    def __init__(self, player1, player2, width=3, height=3, win_condition=3):
        self.player1 = player1
        self.player2 = player2
        self.board = Board(width, height, win_condition)
        self.current_player = player1

    def run(self):
        while self.board.get_winner() is None and not self.board.is_draw:
            row, col = self.current_player.get_move(self.board)
            if self.board.make_move(row, col, self.current_player):
                self.current_player = self.player2 if self.current_player == self.player1 else self.player1
                self.show()
            else:
                print("Invalid move. Try again.")
        if self.board.is_draw:
            print("Game over! It's a draw.")
        else:
            print(f"Game over! Winner: {self.board.get_winner()}")

    def show(self):
        result = ""
        for row in self.board.board:
            result += " | ".join(str(cell) for cell in row) + "\n"
        print(result)


if __name__ == "__main__":
    player1 = Player("Alice", "X")
    ai_player = AIPlayer("O", player1)
    game = Game(ai_player, player1, 6, 6, 4)
    game.run()
