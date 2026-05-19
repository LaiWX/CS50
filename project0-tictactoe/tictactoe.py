"""
Tic Tac Toe Player
"""

import math
import copy

X = "X"
O = "O"
EMPTY = None

BOARD_SIZE = 3


def initial_state():
    """
    Returns starting state of the board.
    """
    return [[EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY]]


def player(board):
    """
    Returns player who has the next turn on a board.
    """
    x_cnt = 0
    o_cnt = 0
    for line in board:
        for piece in line:
            if piece == X:
                x_cnt += 1
            elif piece == O:
                o_cnt += 1
    
    return O if x_cnt > o_cnt else X


def actions(board):
    """
    Returns set of all possible actions (i, j) available on the board.
    """
    all_actions = set()

    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] is None:
                all_actions.add((i, j))
    
    return all_actions


def result(board, action):
    """
    Returns the board that results from making move (i, j) on the board.
    """
    new_board = copy.deepcopy(board)
    i, j = action

    if not 0 <= i <= 2 or not 0 <= j <= 2:
        raise Exception
    if new_board[i][j] is not None:
        raise Exception

    new_board[i][j] = player(new_board)
    return new_board


def winner(board):
    """
    Returns the winner of the game, if there is one.
    """
    # TODO: more maintainable

    # Horizontally
    for i in range(BOARD_SIZE):
        if board[i][0] == board[i][1] == board[i][2] == X:
            return X
        elif board[i][0] == board[i][1] == board[i][2] == O:
            return O
    
    # Vertically
    for j in range(BOARD_SIZE):
        if board[0][j] == board[1][j] == board[2][j] == X:
            return X
        elif board[0][j] == board[1][j] == board[2][j] == O:
            return O
    
    # Diagonally
    # Main Diagonal
    if board[0][0] == board[1][1] == board[2][2] == X:
        return X
    if board[0][0] == board[1][1] == board[2][2] == O:
        return O
    # Sub Diagonal
    if board[0][2] == board[1][1] == board[2][0] == X:
        return X
    if board[0][2] == board[1][1] == board[2][0] == O:
        return O

    return None


def terminal(board):
    """
    Returns True if game is over, False otherwise.
    """
    if winner(board) is not None:
        return True
    
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] is None:
                return False

    # Filled board
    return True


def utility(board):
    """
    Returns 1 if X has won the game, -1 if O has won, 0 otherwise.
    """
    utility_map = {
        X: 1,
        O: -1,
        None: 0,
    }

    return utility_map[winner(board)]


def minimax(board):
    """
    Returns the optimal action for the current player on the board.
    """
    if terminal(board):
        return None

    _, action = _alpha_beta(board, -math.inf, math.inf)

    return action

def _alpha_beta(board, alpha, beta):
    """
    return (value, action) on this board.
    """

    if terminal(board):
        return utility(board), None

    current_player = player(board)
    best_action = None

    if current_player == X:
        value = -math.inf
        for action in actions(board):
            child_value, _ = _alpha_beta(result(board, action), alpha, beta)
            if child_value > value:
                value = child_value
                best_action = action
            alpha = max(alpha, value)
            if alpha >= beta:
                break
    else: # player == O
        value = math.inf
        for action in actions(board):
            child_value, _ = _alpha_beta(result(board, action), alpha, beta)
            if child_value < value:
                value = child_value
                best_action = action
            beta = min(beta, value)
            if alpha >= beta:
                break
    
    return value, best_action
