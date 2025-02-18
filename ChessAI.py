"""
Module ChessAI
----------------
Optimisation de l'IA avec élagage alpha‑beta, itération en profondeur, tri des coups et table de transposition.
"""

from typing import List, Tuple, Dict, Any, Optional, Callable
import random
import ChessEngine

CHECKMATE: int = 1000
DEPTH: int = 3  # Profondeur maximale

def findBestMove(game_state: ChessEngine.GameState, valid_moves: List[ChessEngine.Move], return_queue: Any) -> None:
    """
    Cherche le meilleur coup en itérant en profondeur.
    """
    best_move: Optional[ChessEngine.Move] = None
    transposition_table: Dict[int, Dict[str, Any]] = {}
    for current_depth in range(1, DEPTH + 1):
        best_score, best_move = negamax(game_state, valid_moves, current_depth, -CHECKMATE, CHECKMATE, 1 if game_state.white_to_move else -1, transposition_table)
    return_queue.put(best_move)

def negamax(game_state: ChessEngine.GameState, valid_moves: List[ChessEngine.Move], depth: int, alpha: int, beta: int, turn_multiplier: int, transposition_table: Dict[int, Dict[str, Any]]) -> Tuple[int, Optional[ChessEngine.Move]]:
    """
    Fonction récursive NegaMax avec élagage alpha‑beta.
    """
    board_hash: int = get_board_hash(game_state.board, game_state.white_to_move)
    if board_hash in transposition_table and transposition_table[board_hash]['depth'] >= depth:
        return transposition_table[board_hash]['score'], None
    if depth == 0:
        return turn_multiplier * scoreBoard(game_state), None

    valid_moves.sort(key=lambda move: moveOrderingHeuristic(game_state, move), reverse=True)
    max_score: int = -CHECKMATE
    best_move: Optional[ChessEngine.Move] = None
    for move in valid_moves:
        game_state.makeMove(move, validate=False)
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

def moveOrderingHeuristic(game_state: ChessEngine.GameState, move: ChessEngine.Move) -> int:
    """
    Calcule un score pour ordonner les coups.
    """
    score: int = 0
    if move.is_capture:
        score += 10 + ChessEngine.piece_score.get(move.piece_captured[1], 0)
    if move.is_pawn_promotion:
        score += 15
    return score

def scoreBoard(game_state: ChessEngine.GameState) -> int:
    """
    Évalue le plateau.
    """
    if game_state.checkmate:
        return -CHECKMATE if game_state.white_to_move else CHECKMATE
    elif game_state.stalemate:
        return 0
    total_score: int = 0
    for r in range(ChessEngine.DIMENSION):
        for c in range(ChessEngine.DIMENSION):
            piece = game_state.board[r][c]
            if piece != "--":
                piece_position_score = 0
                if piece[1] != "K":
                    piece_position_score = ChessEngine.piece_position_scores.get(piece, [[0]*ChessEngine.DIMENSION]*ChessEngine.DIMENSION)[r][c]
                if piece[0] == "w":
                    total_score += ChessEngine.piece_score.get(piece[1], 0) + piece_position_score
                else:
                    total_score -= ChessEngine.piece_score.get(piece[1], 0) + piece_position_score
    return total_score

def get_board_hash(board: List[List[str]], white_to_move: bool) -> int:
    """Génère un hash pour l'état du plateau."""
    board_tuple = tuple(tuple(row) for row in board)
    return hash((board_tuple, white_to_move))

def findRandomMove(valid_moves: List[ChessEngine.Move]) -> ChessEngine.Move:
    """Retourne un coup aléatoire parmi ceux valides."""
    return random.choice(valid_moves)
