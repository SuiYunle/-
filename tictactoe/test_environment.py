from environment import available, winner, terminal, render


def test_empty_board():
    board = [" "] * 9
    assert available(board) == [0, 1, 2, 3, 4, 5, 6, 7, 8]
    assert winner(board) is None
    finished, result = terminal(board)
    assert finished is False
    assert result is None
    print("[PASS] test 1: empty board")


def test_x_horizontal_win():
    board = [
        "X", "X", "X",
        "O", "O", " ",
        " ", " ", " ",
    ]
    assert winner(board) == "X"
    finished, result = terminal(board)
    assert finished is True
    assert result == "X"
    print("[PASS] test 2: X horizontal win")


def test_o_vertical_win():
    board = [
        "O", "X", " ",
        "O", "X", " ",
        "O", " ", "X",
    ]
    assert winner(board) == "O"
    finished, result = terminal(board)
    assert finished is True
    assert result == "O"
    print("[PASS] test 3: O vertical win")


def test_x_diagonal_win():
    board = [
        "X", "O", " ",
        " ", "X", "O",
        " ", " ", "X",
    ]
    assert winner(board) == "X"
    finished, result = terminal(board)
    assert finished is True
    assert result == "X"
    print("[PASS] test 4: X diagonal win")


def test_draw():
    board = [
        "X", "O", "X",
        "X", "O", "O",
        "O", "X", "X",
    ]
    assert winner(board) is None
    finished, result = terminal(board)
    assert finished is True
    assert result == "DRAW"
    print("[PASS] test 5: draw")


def test_not_finished():
    board = [
        "X", "O", " ",
        " ", "X", " ",
        " ", " ", "O",
    ]
    assert winner(board) is None
    finished, result = terminal(board)
    assert finished is False
    assert result is None
    print("[PASS] test 6: not finished")


def test_available_partial():
    board = [
        "X", " ", "O",
        " ", "X", " ",
        " ", " ", "O",
    ]
    assert available(board) == [1, 3, 5, 6, 7]
    print("[PASS] test 7: partial board available moves")


def test_render():
    board = [
        "X", " ", "O",
        " ", "X", " ",
        " ", " ", "O",
    ]
    print("\n--- render demo ---")
    render(board)
    print("--- end demo ---")
    print("[PASS] test 8: render display")


if __name__ == "__main__":
    test_empty_board()
    test_x_horizontal_win()
    test_o_vertical_win()
    test_x_diagonal_win()
    test_draw()
    test_not_finished()
    test_available_partial()
    test_render()
    print("\n=== ALL TESTS PASSED ===")
