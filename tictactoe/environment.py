EMPTY = " "


def available(board):
    """返回当前合法动作列表（未被占用的位置编号）"""
    moves = []
    for i in range(9):
        if board[i] == " ":
            moves.append(i)
    return moves


def winner(board):
    """检测是否有赢家，返回 'X'、'O' 或 None"""
    winning_lines = [
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        (0, 4, 8),
        (2, 4, 6),
    ]

    for a, b, c in winning_lines:
        if (
            board[a] != " "
            and board[a] == board[b]
            and board[b] == board[c]
        ):
            return board[a]

    return None


def terminal(board):
    """检测游戏是否结束，返回 (finished, result)"""
    w = winner(board)
    if w is not None:
        return True, w

    if len(available(board)) == 0:
        return True, "DRAW"

    return False, None


def render(board):
    """以可读方式显示棋盘，空位显示位置编号"""
    cells = []
    for i in range(9):
        if board[i] == " ":
            cells.append(str(i))
        else:
            cells.append(board[i])

    print(
        f" {cells[0]} | {cells[1]} | {cells[2]}\n"
        f"---+---+---\n"
        f" {cells[3]} | {cells[4]} | {cells[5]}\n"
        f"---+---+---\n"
        f" {cells[6]} | {cells[7]} | {cells[8]}"
    )
