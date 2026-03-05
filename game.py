from board import TTTBoard, ConnectFourBoard
from player import Player, AIPlayer
from show import Show


class Game:
    def __init__(self, board_type="TTT"):
        if board_type == "C4":
            self.board = ConnectFourBoard()
        else:
            self.board = TTTBoard(6, 4)
            
        self.p1 = Player("Human", "X")
        self.p2 = AIPlayer("O", self.p1)
        self.current_player = self.p1

    def switch_player(self):
        self.current_player = self.p2 if self.current_player == self.p1 else self.p1

    def get_human_input(self):
        while True:
            try:
                if isinstance(self.board, ConnectFourBoard):
                    move = int(input(f"{self.current_player}, enter column: "))
                    return move
                else:
                    inp = input(f"{self.current_player}, enter row and col: ").split()
                    return (int(inp[0]), int(inp[1]))
            except (ValueError, IndexError):
                print("Invalid input format.")

    def run(self):
        Show.display_board(self.board.board)
        
        while not self.board.is_game_over():
            if isinstance(self.current_player, AIPlayer):
                Show.msg("AI is thinking...")
                move = self.current_player.get_move(self.board)
            else:
                move = self.get_human_input()

            if self.board.make_move(move, self.current_player):
                Show.display_board(self.board.board, move)
                if self.board.is_game_over():
                    break
                self.switch_player()
            else:
                Show.msg("Invalid move! Try again.")

        winner = self.board.get_winner()
        if winner:
            Show.msg(f"GAME OVER: {winner} wins!")
        else:
            Show.msg("GAME OVER: It's a draw!")

if __name__ == "__main__":
    # Change to "C4" to play Connect Four
    game = Game(board_type="TTT")
    game.run()