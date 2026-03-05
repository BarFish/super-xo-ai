class Show:
    @staticmethod
    def display_board(board, move=None):
        if move is not None:
            if isinstance(move, int):
                move_row, move_col = None, move
            else:
                move_row, move_col = move
        else:
            move_row, move_col = None, None

        result = ""
        for i in range(len(board[0])):
            result += f"   {i}"
        result += "\n"

        for i, row in enumerate(board):
            result += f"{i}|"
            for j, cell in enumerate(row):
                if (i, j) == (move_row, move_col) or \
                    (move_row is None and j == move_col and not cell.is_playable()):
                    result += f"[{cell}]|"
                else:
                    result += f" {cell} |"
            result += "\n"

        print(result)

    @staticmethod
    def msg(text):
        print(f">> {text}")