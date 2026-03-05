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
        self.weight = 0

    def is_playable(self):
        return self.value is None
    
    def set_value(self, player):
        self.value = player

    def set_weight(self, weight):
        self.weight = weight

    def get_weight(self):
        return self.weight

    def __str__(self):
        return self.value.symbol if self.value else ' '
 

class SuperTTTCell(Cell):
    def __init__(self):
        super().__init__()
        self.sub_board = TTTBoard(3, 3, 3)
        self.sub_board_weight = 0
        self.is_decided = False

    def set_sub_board_weight(self, weight):
        self.sub_board_weight = weight

    def is_playable(self):
        return not self.is_decided


class Board:
    def __init__(self, width, height, win_condition):
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

    def make_move(self, move, player):
        """move is (row, col)"""
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
        """move is (row, col)"""
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
                if self.board[r][c].is_playable()
            ],
            key=lambda rc: self.board[rc[0]][rc[1]].weight,
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
                self.board[row][col].set_weight(score)

    def _update_board_evaluation_after_move(self, row, col, player, undo=False):
        """
        Updates the heuristic value of cells.
        When a move is made, we INCREASE the weight of windows the player occupies
        and DECREASE the weight of windows the player has blocked for the opponent.
        """
        # If we are undoing, we flip the math (e.g., subtracting a positive or adding a negative)
        op_modifier = 1 if undo else -1  # Impact on opponent windows
        self_modifier = -1 if undo else 1 # Impact on player windows

        for fwd, bck in AXES:
            dr_f, dc_f = DIRECTIONS[fwd]
            dr_b, dc_b = DIRECTIONS[bck]

            for k in range(self.win_condition):
                # Calculate window boundaries
                start_r, start_c = row + dr_b * k, col + dc_b * k
                end_r, end_c = row + dr_f * (self.win_condition - 1 - k), col + dc_f * (self.win_condition - 1 - k)

                if (0 <= start_r < self.height and 0 <= start_c < self.width and
                    0 <= end_r < self.height and 0 <= end_c < self.width):
                    
                    # Examine this specific window
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

                    # LOGIC:
                    # 1. If window contains BOTH players, it's dead. Weight = 0.
                    # 2. If it only contains 'player', it's an active threat. Weight increases.
                    # 3. If we just blocked an opponent, their potential in this window drops.
                    
                    for cell in window_cells:
                        if cell.is_playable():
                            # Simplest version: just increment/decrement
                            # You can make this smarter by checking if the window is 'alive'
                            change = self_modifier if not has_opponent else op_modifier
                            cell.weight += change


class TTTBoard(Board):
    def __init__(self, size=3, win_condition=3):
        super().__init__(size, size, win_condition)
        self._initialize_board_evaluation()


class ConnectFourBoard(Board):
    def __init__(self, width=7, height=6, win_condition=4):
        super().__init__(width, height, win_condition)
        self._initialize_board_evaluation()

    def _get_row_for_move(self, col):
        for row in range(self.height - 1, -1, -1):
            if self.board[row][col].is_playable():
                return row
        return None

    def make_move(self, move, player):
        """move is the column"""
        col = move
        row = self._get_row_for_move(col)
        if row is not None:
            return super().make_move((row, col), player)
        return False
    
    def undo_last_move(self, move):
        """move is the column"""
        col = move
        for r in range(self.height):
            if not self.board[r][col].is_playable():
                super().undo_last_move((r, col))
                return

    def get_empty_cells(self):
        return sorted(
            [(self._get_row_for_move(col), col) for col in range(self.width) if self._get_row_for_move(col) is not None],
            key=lambda rc: self.board[rc[0]][rc[1]].weight,
            reverse=True
        )
