import random

piece_score = {"K": 0, "Q": 9, "R": 5, "B": 3, "N": 3, "p": 1}
CHECKMATE = 1000
STALEMATE = 0

def findRandomMove(valid_moves):
    '''
        Choisit un mouvement aléatoire parmi les mouvements valides
    '''
    return random.choice(valid_moves)

def findBestMove(game_state, valid_moves):
    '''
        Trouve le meilleur mouvement en utilisant Minimax avec Alpha-Beta Pruning
    '''
    turn_multiplier = 1 if game_state.white_to_move else -1
    opponent_min_max_score = CHECKMATE
    best_player_move = None
    random.shuffle(valid_moves)
    for player_move in valid_moves:
        game_state.makeMove(player_move)
        opponent_moves = game_state.getValidMoves()
        opponent_max_score = -CHECKMATE
        for opponent_move in opponent_moves:
            game_state.makeMove(opponent_move)
            if game_state.check_mate:
                score = -turn_multiplier * CHECKMATE
            elif game_state.stale_mate:
                score = STALEMATE
            else:
                score = -turn_multiplier * scoreMaterial(game_state.board)
            if score > opponent_max_score:
                opponent_max_score = score
            game_state.undoMove()
        if opponent_max_score < opponent_min_max_score:
            opponent_min_max_score = opponent_max_score
            best_player_move = player_move
        game_state.undoMove()
    return best_player_move


def scoreMaterial(board):
    '''
        Score le plateau en fonction de la valeur des pièces
    '''
    score = 0
    for row in board:
        for square in row:
            if square[0] == 'w':
                score += piece_score[square[1]]
            elif square[0] == 'b':
                score -= piece_score[square[1]]
    return score