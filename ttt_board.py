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
    def __init__(self):
        self.value = None
        self.evaluation = 0

    def is_empty(self):
        return self.value is None
    
    def set_value(self, player):
        self.value = player

    def set_evaluation(self, value):
        self.evaluation = value

    def __str__(self):
        return self.value.symbol if self.value else ' '
    

class Board:
    def __init__(self, width=3, height=3, win_condition=3):
        if height < win_condition or width < win_condition:
            raise ValueError(
                "Board dimensions must be greater than or equal to the win condition."
            )

        self.width = width
        self.height = height
        self.win_condition = win_condition
        self.board = [[Cell() for _ in range(self.width)] for _ in range(self.height)]
        self.winner = None
        self.is_draw = False
        self.move_count = 0
        self._initialize_board_evaluation()

    def make_move(self, row, col, player):
        if (not (0 <= row < self.height and 0 <= col < self.width)
            or self.is_game_over()
            or not self.board[row][col].is_empty()):
            return False

        self.board[row][col].set_value(player)
        self.move_count += 1

        self.check_winner(row, col, player)
        return True

    def undo_last_move(self, row, col):
        if not (0 <= row < self.height and 0 <= col < self.width):
            return

        if not self.board[row][col].is_empty():
            self.board[row][col].value = None
            self.move_count -= 1

        self.winner = None
        self.is_draw = False

    def _count_direction(self, row, col, direction, player):
        count = 0
        direction_row, direction_col = DIRECTIONS[direction]
        r, c = row + direction_row, col + direction_col

        while (
            0 <= r < self.height
            and 0 <= c < self.width
            and self.board[r][c].value == player
        ):
            count += 1
            r += direction_row
            c += direction_col

        return count

    def _check_row(self, row, col, player):
        total = 1
        total += self._count_direction(row, col, "right", player)
        total += self._count_direction(row, col, "left", player)
        return total >= self.win_condition

    def _check_column(self, row, col, player):
        total = 1
        total += self._count_direction(row, col, "down", player)
        total += self._count_direction(row, col, "up", player)
        return total >= self.win_condition

    def _check_diagonals(self, row, col, player):
        # (\) diagonal
        total = 1
        total += self._count_direction(row, col, "down_right", player)
        total += self._count_direction(row, col, "up_left", player)
        if total >= self.win_condition:
            return True

        # (/) diagonal
        total = 1
        total += self._count_direction(row, col, "down_left", player)
        total += self._count_direction(row, col, "up_right", player)
        return total >= self.win_condition

    def check_winner(self, row, col, player):
        if (
            self._check_row(row, col, player)
            or self._check_column(row, col, player)
            or self._check_diagonals(row, col, player)
        ):
            self.winner = player
            return True

        if self.move_count == self.width * self.height:
            self.is_draw = True
            return True

        return False

    def get_winner(self):
        return self.winner

    def get_empty_cells(self):
        return sorted(
            [
                (r, c)
                for r in range(self.height)
                for c in range(self.width)
                if self.board[r][c].is_empty()
            ],
            key=lambda rc: self.board[rc[0]][rc[1]].evaluation,
            reverse=True
        )

    def is_game_over(self):
        return self.winner is not None or self.is_draw
    
    def _initialize_board_evaluation(self):
        """
        For each cell, count how many winning windows (of length win_condition)
        pass through it across all 4 axes. That count is its static evaluation.
        """
        for row in range(self.height):
            for col in range(self.width):
                score = 0
                for fwd, bck in AXES:
                    dr_f, dc_f = DIRECTIONS[fwd]
                    dr_b, dc_b = DIRECTIONS[bck]

                    for k in range(self.win_condition):
                        # Window starts k steps in the backward direction from cell
                        start_r = row + dr_b * k
                        start_c = col + dc_b * k
                        # Window ends (win_condition - 1 - k) steps forward
                        end_r = row + dr_f * (self.win_condition - 1 - k)
                        end_c = col + dc_f * (self.win_condition - 1 - k)
                        if (0 <= start_r < self.height and 0 <= start_c < self.width
                                and 0 <= end_r < self.height and 0 <= end_c < self.width):
                            score += 1
                self.board[row][col].set_evaluation(score)