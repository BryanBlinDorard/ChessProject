import random
import ChessEngine

CHECKMATE = 1000
DEPTH = 3  # Profondeur maximale

def findBestMove(game_state, valid_moves, return_queue):
    best_move = None
    transposition_table = {}
    # Itération en profondeur
    for current_depth in range(1, DEPTH + 1):
        best_score, best_move = negamax(game_state, valid_moves, current_depth, -CHECKMATE, CHECKMATE, 1 if game_state.white_to_move else -1, transposition_table)
    return_queue.put(best_move)

def negamax(game_state, valid_moves, depth, alpha, beta, turn_multiplier, transposition_table):
    board_hash = get_board_hash(game_state.board, game_state.white_to_move)
    if board_hash in transposition_table and transposition_table[board_hash]['depth'] >= depth:
        return transposition_table[board_hash]['score'], None
    if depth == 0:
        return turn_multiplier * scoreBoard(game_state), None

    # Tri des mouvements
    valid_moves.sort(key=lambda move: moveOrderingHeuristic(game_state, move), reverse=True)
    max_score = -CHECKMATE
    best_move = None
    for move in valid_moves:
        game_state.makeMove(move)
        next_moves = game_state.getValidMoves()
        score, _ = negamax(game_state, next_moves, depth - 1, -beta, -alpha, -turn_multiplier, transposition_table)
        score = -score
        game_state.undoMove()
        if score > max_score:
            max_score = score
            best_move = move
        alpha = max(alpha, score)
        if alpha >= beta:
            break
    transposition_table[board_hash] = {'score': max_score, 'depth': depth}
    return max_score, best_move

def moveOrderingHeuristic(game_state, move):
    score = 0
    if move.is_capture:
        score += 10 + ChessEngine.piece_score.get(move.piece_captured[1], 0)
    if move.is_pawn_promotion:
        score += 15
    return score

def scoreBoard(game_state):
    if game_state.checkmate:
        return -CHECKMATE if game_state.white_to_move else CHECKMATE
    elif game_state.stalemate:
        return 0
    score = 0
    for r in range(8):
        for c in range(8):
            piece = game_state.board[r][c]
            if piece != "--":
                piece_position_score = 0
                if piece[1] != "K":
                    piece_position_score = ChessEngine.piece_position_scores.get(piece, [[0]*8]*8)[r][c]
                if piece[0] == "w":
                    score += ChessEngine.piece_score.get(piece[1], 0) + piece_position_score
                else:
                    score -= ChessEngine.piece_score.get(piece[1], 0) + piece_position_score
    return score

def get_board_hash(board, white_to_move):
    board_tuple = tuple(tuple(row) for row in board)
    return hash((board_tuple, white_to_move))

def findRandomMove(valid_moves):
    return random.choice(valid_moves)
