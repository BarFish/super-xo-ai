DIRECTIONS = {
    "up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1),
    "up_left": (-1, -1), "up_right": (-1, 1),
    "down_left": (1, -1), "down_right": (1, 1)
}

AXES = [
    ("right", "left"),
    ("down", "up"),
    ("down_right", "up_left"),
    ("down_left", "up_right"),
]


class Cell:
    """Represents a single square on the board."""
    def __init__(self):
        self.value = None
        self.weight = 0

    def is_playable(self):
        """Returns True if this cell is empty."""
        return self.value is None

    def set_value(self, player):
        self.value = player

    def set_weight(self, weight):
        self.weight = weight

    def get_weight(self):
        return self.weight

    def __str__(self):
        return self.value.symbol if self.value else ' '


class Board:
    """
    Generic game board. Both TTT and Connect Four extend this.
    Handles move-making, win-checking, and AI heuristics.
    """
    def __init__(self, width, height, win_condition):
        if height < win_condition or width < win_condition:
            raise ValueError("Board dimensions must be >= win condition.")

        self.width = width
        self.height = height
        self.win_condition = win_condition
        self.board = [[Cell() for _ in range(self.width)] for _ in range(self.height)]
        self.winner = None
        self.is_draw = False
        self.move_count = 0

    def make_move(self, move, player):
        """Place a piece. move is (row, col). Returns True if valid."""
        row, col = move
        if (not (0 <= row < self.height and 0 <= col < self.width)
                or self.is_game_over()
                or not self.board[row][col].is_playable()):
            return False

        self.board[row][col].set_value(player)
        self.move_count += 1
        self.check_winner(row, col, player)
        self._update_board_evaluation_after_move(row, col, player)
        return True

    def undo_last_move(self, move):
        """Remove a piece (used by AI minimax). move is (row, col)."""
        row, col = move
        if not (0 <= row < self.height and 0 <= col < self.width):
            return
        if not self.board[row][col].is_playable():
            player = self.board[row][col].value
            self._update_board_evaluation_after_move(row, col, player, undo=True)
            self.board[row][col].value = None
            self.move_count -= 1
            self.winner = None
            self.is_draw = False

    def _count_direction(self, row, col, direction, player):
        """Count consecutive pieces from (row, col) in one direction."""
        count = 0
        dr, dc = DIRECTIONS[direction]
        r, c = row + dr, col + dc
        while (0 <= r < self.height and 0 <= c < self.width
               and self.board[r][c].value == player):
            count += 1
            r += dr
            c += dc
        return count

    def _check_row(self, row, col, player):
        total = 1 + self._count_direction(row, col, "right", player) \
                  + self._count_direction(row, col, "left", player)
        return total >= self.win_condition

    def _check_column(self, row, col, player):
        total = 1 + self._count_direction(row, col, "down", player) \
                  + self._count_direction(row, col, "up", player)
        return total >= self.win_condition

    def _check_diagonals(self, row, col, player):
        total = 1 + self._count_direction(row, col, "down_right", player) \
                  + self._count_direction(row, col, "up_left", player)
        if total >= self.win_condition:
            return True
        total = 1 + self._count_direction(row, col, "down_left", player) \
                  + self._count_direction(row, col, "up_right", player)
        return total >= self.win_condition

    def check_winner(self, row, col, player):
        """Check if the last move won the game or caused a draw."""
        if (self._check_row(row, col, player)
                or self._check_column(row, col, player)
                or self._check_diagonals(row, col, player)):
            self.winner = player
            self.winning_move = (row, col)   # remember so get_winning_cells can trace the line
            return True
        if self.move_count == self.width * self.height:
            self.is_draw = True
            return True
        return False

    def get_winner(self):
        return self.winner

    def get_winning_cells(self):
        """
        Return the list of (row, col) that form the winning line.
        We stored the last move that triggered check_winner as self.winning_move.
        Returns [] if no winner yet.
        """
        if not self.winner or not hasattr(self, 'winning_move'):
            return []
        row, col = self.winning_move
        player = self.winner
        for fwd, bck in AXES:
            cells_fwd = []
            dr, dc = DIRECTIONS[fwd]
            r, c = row, col
            while 0 <= r < self.height and 0 <= c < self.width and self.board[r][c].value == player:
                cells_fwd.append((r, c))
                r += dr; c += dc
            cells_bck = []
            dr, dc = DIRECTIONS[bck]
            r, c = row + dr, col + dc
            while 0 <= r < self.height and 0 <= c < self.width and self.board[r][c].value == player:
                cells_bck.append((r, c))
                r += dr; c += dc
            line = cells_bck + cells_fwd
            if len(line) >= self.win_condition:
                return line
        return []

    def get_empty_cells(self):
        """Return all playable cells, sorted by AI heuristic weight."""
        return sorted(
            [(r, c) for r in range(self.height) for c in range(self.width)
             if self.board[r][c].is_playable()],
            key=lambda rc: self.board[rc[0]][rc[1]].weight,
            reverse=True
        )

    def is_game_over(self):
        return self.winner is not None or self.is_draw

    def _initialize_board_evaluation(self):
        """Assign each cell a static weight based on how many winning windows pass through it."""
        for row in range(self.height):
            for col in range(self.width):
                score = 0
                for fwd, bck in AXES:
                    dr_f, dc_f = DIRECTIONS[fwd]
                    dr_b, dc_b = DIRECTIONS[bck]
                    for k in range(self.win_condition):
                        start_r = row + dr_b * k
                        start_c = col + dc_b * k
                        end_r = row + dr_f * (self.win_condition - 1 - k)
                        end_c = col + dc_f * (self.win_condition - 1 - k)
                        if (0 <= start_r < self.height and 0 <= start_c < self.width
                                and 0 <= end_r < self.height and 0 <= end_c < self.width):
                            score += 1
                self.board[row][col].set_weight(score)

    def _update_board_evaluation_after_move(self, row, col, player, undo=False):
        """Update cell weights around the last move to help the AI prioritize threats."""
        op_modifier = 1 if undo else -1
        self_modifier = -1 if undo else 1

        for fwd, bck in AXES:
            dr_f, dc_f = DIRECTIONS[fwd]
            dr_b, dc_b = DIRECTIONS[bck]
            for k in range(self.win_condition):
                start_r, start_c = row + dr_b * k, col + dc_b * k
                end_r, end_c = row + dr_f * (self.win_condition - 1 - k), col + dc_f * (self.win_condition - 1 - k)
                if (0 <= start_r < self.height and 0 <= start_c < self.width
                        and 0 <= end_r < self.height and 0 <= end_c < self.width):
                    window_cells = []
                    has_opponent = False
                    has_self = False
                    for i in range(self.win_condition):
                        r_idx, c_idx = start_r + dr_f * i, start_c + dc_f * i
                        cell = self.board[r_idx][c_idx]
                        window_cells.append(cell)
                        if cell.value and cell.value != player:
                            has_opponent = True
                        if cell.value == player:
                            has_self = True
                    for cell in window_cells:
                        if cell.is_playable():
                            change = self_modifier if not has_opponent else op_modifier
                            cell.weight += change

    def to_dict(self):
        """Convert board state to a JSON-serializable dictionary for the frontend."""
        return {
            "grid": [
                [
                    {
                        "symbol": self.board[r][c].value.symbol if self.board[r][c].value else None,
                        "player_id": self.board[r][c].value.player_id if self.board[r][c].value else None
                    }
                    for c in range(self.width)
                ]
                for r in range(self.height)
            ],
            "width": self.width,
            "height": self.height,
            "win_condition": self.win_condition,
            "is_game_over": self.is_game_over(),
            "winner_symbol": self.winner.symbol if self.winner else None,
            "winner_id": self.winner.player_id if self.winner else None,
            "is_draw": self.is_draw,
            "winning_cells": self.get_winning_cells(),
        }


class TTTBoard(Board):
    """Tic Tac Toe board with configurable size and win condition."""
    def __init__(self, size=3, win_condition=3):
        super().__init__(size, size, win_condition)
        self._initialize_board_evaluation()


class ConnectFourBoard(Board):
    """Connect Four board - pieces fall to the bottom of each column."""
    def __init__(self, width=7, height=6, win_condition=4):
        super().__init__(width, height, win_condition)
        self._initialize_board_evaluation()

    def _get_row_for_move(self, col):
        """Find the lowest empty row in a column (gravity effect)."""
        for row in range(self.height - 1, -1, -1):
            if self.board[row][col].is_playable():
                return row
        return None  # Column is full

    def make_move(self, move, player):
        """For Connect Four, move is just the column number."""
        col = move
        row = self._get_row_for_move(col)
        if row is not None:
            result = super().make_move((row, col), player)
            return result
        return False

    def undo_last_move(self, move):
        """Undo the topmost piece in a column."""
        col = move
        for r in range(self.height):
            if not self.board[r][col].is_playable():
                super().undo_last_move((r, col))
                return

    def get_empty_cells(self):
        """Return valid column moves (as (row, col) for compatibility)."""
        return sorted(
            [(self._get_row_for_move(col), col)
             for col in range(self.width)
             if self._get_row_for_move(col) is not None],
            key=lambda rc: self.board[rc[0]][rc[1]].weight,
            reverse=True
        )

    def get_drop_row(self, col):
        """Public method to see where a piece would land in a column."""
        return self._get_row_for_move(col)
