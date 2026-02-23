import random

class Player:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    def __str__(self):
        return f"{self.name} ({self.symbol})"
    

class Cell:
    def __init__(self):
        self.value = None

    def is_empty(self):
        return self.value is None
    
    def set_value(self, player):
        self.value = player

    def __str__(self):
        return self.value.symbol if self.value else ' '
    

class Board:
    def __init__(self, width=3, height=3, win_condition=3):
        if height < win_condition or width < win_condition:
            raise ValueError("Board dimensions must be greater than or equal to the win condition.")
        self.width = width
        self.height = height
        self.win_condition = win_condition
        self.board = [[Cell() for _ in range(self.width)] for _ in range(self.height)]
        self.winner = None
        self.move_count = 0

    def make_move(self, row, col, player):
        if self.board[row][col].is_empty() and self.winner is None:
            self.board[row][col].set_value(player)
            self.move_count += 1

            show_board.show(self)
            self.check_winner(player)
            return True
        
        return False
    
    def _check_rows(self, player):
        for row in self.board:
            count = 0
            for cell in row:
                if cell.value == player:
                    count += 1
                    if count == self.win_condition:
                        return True
                else:
                    count = 0
        return False
    
    def _check_columns(self, player):
        for c in range(self.width):
            count = 0
            for r in range(self.height):
                if self.board[r][c].value == player:
                    count += 1
                    if count == self.win_condition:
                        return True
                else:
                    count = 0
        return False
    
    def _check_diagonal(self, player, r, c):
        cur_r, cur_c = r, c
        count = 0
        while cur_r < self.height and cur_c < self.width:
            if self.board[cur_r][cur_c].value == player:
                count += 1
                if count == self.win_condition:
                    return True
            else:
                count = 0
            cur_r += 1
            cur_c += 1

        cur_r, cur_c = r, c
        count = 0
        while cur_r < self.height and cur_c >= 0:
            if self.board[cur_r][cur_c].value == player:
                count += 1
                if count == self.win_condition:
                    return True
            else:
                count = 0
            cur_r += 1
            cur_c -= 1
        return False
    
    def _check_diagonals(self, player):
        for c in range(self.width):
            if self._check_diagonal(player, 0, c):
                return True
        
        for r in range(1, self.height):
            if self._check_diagonal(player, r, 0) \
                or self._check_diagonal(player, r, self.width - 1):
                return True
        
        return False

    def check_winner(self, player):
        if self._check_rows(player) or self._check_columns(player) \
            or self._check_diagonals(player):
            self.winner = player
            print(f"{player} wins!")
            return True
        
        if self.move_count == self.width * self.height:
            print("It's a draw!")
            self.winner = ""
            return True
        
        return False
    

class show_board:
    @staticmethod
    def show(board):
        result = ""
        for row in board.board:
            result += " | ".join(str(cell) for cell in row) + "\n"
        print(result)
    

if __name__ == "__main__":
    player1 = Player("Alice", "X")
    player2 = Player("Bob", "O")
    board = Board()

    moves = [(r, c) for r in range(board.height) for c in range(board.width)]
    random.shuffle(moves)

    winner = None
    while winner is None:
        row, col = moves.pop()
        board.make_move(row, col, player1)
        winner = board.winner
        if board.winner is not None:
            break
        row, col = moves.pop()
        board.make_move(row, col, player2)
        winner = board.winner
        

    # board.make_move(0, 2, player1)
    # board.make_move(0, 1, player2)
    # board.make_move(1, 1, player1)
    # board.make_move(0, 0, player2)
    # board.make_move(2, 0, player1)