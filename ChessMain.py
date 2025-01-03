"""
Fichier Pricipal, gérera les entrées et sorties du jeu
"""

# Importer les bibliothèques nécessaires
import pygame as p
import sys
from itertools import zip_longest

# Importer mes modules
import ChessEngine
import ChessAI

# Constantes
BOARD_WIDTH  = BOARD_HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8
SQ_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}


def loadImages():
    """
    Initialiser un dictionnaire global des images. Cela sera appelé exactement une fois dans le main
    """
    pieces = ["wp", "wR", "wN", "wB", "wQ", "wK", "bp", "bR", "bN", "bB", "bQ", "bK"]
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))


def main():
    '''
    La fonction principale pour gérer les entrées et sorties du jeu
    '''
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    game_state = ChessEngine.GameState()
    valid_moves = game_state.getValidMoves()
    move_made = False  # Variable pour savoir si un mouvement a été fait
    animate = False  # Variable pour savoir si un animation est en cours
    loadImages()  # Faire cela une seule fois avant la boucle

    running = True
    square_selected = ()  # gardera la dernière case cliquée par le joueur (tuples: (row, col))
    player_clicks = []  # gardera les deux dernières cases cliquées par le joueur (liste: [(row1, col1), (row2, col2)])
    game_over = False

    white_did_check = ""
    black_did_check = ""
    last_move_printed = False
    moves_list = []
    move_log_font = p.font.SysFont("Arial", 14, False, False)

    turn = 1

    player_one = False  # Si un humain joue les blancs, alors ceci sera True, sinon False
    player_two = False  # Si un humain joue les noirs, alors ceci sera True, sinon False

    while running:
        human_turn = (game_state.white_to_move and player_one) or (not game_state.white_to_move and player_two)
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
                p.quit()
                sys.exit()
            # Gestion des événements de la souris
            elif e.type == p.MOUSEBUTTONDOWN:
                if not game_over and human_turn:
                    location = p.mouse.get_pos()  # (x, y) Localisation de la souris
                    col = location[0] // SQ_SIZE
                    row = location[1] // SQ_SIZE
                    if square_selected == (row, col) or col >= 8: # L'utilisateur a cliqué sur la même case deux fois ou en dehors du tableau
                        square_selected = () # annuler le clic
                        player_clicks = [] # annuler les clics
                    else:
                        square_selected = (row, col)
                        player_clicks.append(square_selected) # ajouter à la liste
                    if len(player_clicks) == 2: # après le deuxième clic
                        move = ChessEngine.Move(player_clicks[0], player_clicks[1], game_state.board)
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                game_state.makeMove(valid_moves[i])
                                move_made = True
                                animate = True
                                square_selected = () # réinitialiser les clics
                                player_clicks = []
                        if not move_made:
                            player_clicks = [square_selected]
            # Gestion des événements du clavier
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:  # Annuler le dernier coup si possible
                    # Annuler les deux derniers coups si possible
                    if len(game_state.move_log) > 0:
                        game_state.undoMove()  # Annuler le coup du noir
                        turn -= 1
                    if len(game_state.move_log) > 0:
                        game_state.undoMove()  # Annuler ton coup
                        turn -= 1
                    move_made = True
                    animate = False
                    game_over = False
                    last_move_printed = False

                if e.key == p.K_r:  # Réinitialiser le jeu
                    game_state = ChessEngine.GameState()
                    valid_moves = game_state.getValidMoves()
                    square_selected = ()
                    player_clicks = []
                    move_made = False
                    animate = False
                    game_over = False
                    turn = 1
                    last_move_printed = False
                    moves_list = []
                    print("Reset de la partie")

        # AI move
        if not game_over and not human_turn:
            # AI_move = ChessAI.findRandomMove(valid_moves)
            # AI_move = ChessAI.findBestMove(game_state, valid_moves)
            # AI_move = ChessAI.findBestMoveMinMax(game_state, valid_moves)
            # AI_move = ChessAI.findBestMoveNegaMax(game_state, valid_moves)
            AI_move = ChessAI.findBestMoveNegaMaxAlphaBeta(game_state, valid_moves)
            if AI_move is None:
                AI_move = ChessAI.findRandomMove(valid_moves)
            game_state.makeMove(AI_move)
            move_made = True
            animate = True

        if move_made:
            if game_state.checkForPinsAndChecks()[0]:
                if not game_state.white_to_move:
                    white_did_check = "+"
                else:
                    black_did_check = "+"
            if game_state.white_to_move:
                try:
                    moves_list.append(
                        f"\n{turn}. {game_state.move_log[-2].getChessNotation()}{white_did_check} {game_state.move_log[-1].getChessNotation()}{black_did_check}")
                    print(
                        f"\n{turn}. {game_state.move_log[-2].getChessNotation()}{white_did_check} {game_state.move_log[-1].getChessNotation()}{black_did_check}",
                        end="")
                    turn += 1
                    white_did_check = ""
                    black_did_check = ""
                except:
                    pass

            if animate:
                animateMove(game_state.move_log[-1], screen, game_state.board, clock)
            valid_moves = game_state.getValidMoves()
            move_made = False
            animate = False

        drawGameState(screen, game_state, valid_moves, square_selected, move_log_font)

        if not game_over:
            drawMoveLog(screen, game_state, move_log_font)

        if game_state.checkmate:
            game_over = True
            if game_state.white_to_move:
                drawEndGameText(screen, "Black wins by checkmate")
                if not last_move_printed:
                    moves_list[-1] += "+"
                    moves_list.append("result: 0-1")
                    print("+")
                    print("result: 0-1")
                    last_move_printed = True
                    saveGame(moves_list)
            else:
                drawEndGameText(screen, "White wins by checkmate")
                if not last_move_printed:
                    moves_list.append(f"\n{turn}. {game_state.move_log[-1].getChessNotation()}++")
                    moves_list.append("result: 1-0")
                    print(f"\n{turn}. {game_state.move_log[-1].getChessNotation()}++")
                    print("result: 1-0")
                    last_move_printed = True
                    saveGame(moves_list)
        elif game_state.stalemate:
            game_over = True
            drawEndGameText(screen, "Stalemate")
            if not last_move_printed:
                if not game_state.white_to_move:
                    moves_list.append(f"\n{turn}. {game_state.move_log[-1].getChessNotation()}")
                    moves_list.append("result: 1/2-1/2")
                    print(f"\n{turn}. {game_state.move_log[-1].getChessNotation()}")
                    print("result: 1/2-1/2")
                    last_move_printed = True
                    saveGame(moves_list)

        clock.tick(MAX_FPS)
        p.display.flip()



def drawGameState(screen, game_state, valid_moves, square_selected, move_log_font):
    """
    Gère tous les graphiques du jeu
    """
    drawBoard(screen) # dessine les carrés sur le tableau
    highlightSquares(screen, game_state, valid_moves, square_selected) # Met en évidence les carrés sélectionnés et les mouvements
    drawPieces(screen, game_state.board) # dessine les pièces sur les carrés
    # drawMoveLog(screen, game_state, move_log_font) # dessine le journal des mouvements


def drawBoard(screen):
    '''
    Dessine les carrés sur le tableau

    '''
    global colors
    colors = [p.Color("white"), p.Color("gray")]
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            color = colors[((row+column) % 2)]
            p.draw.rect(screen, color, p.Rect(column*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, SQ_SIZE))



def highlightSquares(screen, game_state, valid_moves, square_selected):
    '''
    Met en évidence les carrés sélectionnés et les mouvements
    '''
    if (len(game_state.move_log)) > 0:
        last_move = game_state.move_log[-1]
        s = p.Surface((SQ_SIZE, SQ_SIZE))
        s.set_alpha(100)
        s.fill(p.Color('green'))
        screen.blit(s, (last_move.end_col*SQ_SIZE, last_move.end_row*SQ_SIZE))
    if square_selected != ():
        row, col = square_selected
        if game_state.board[row][col][0] == ('w' if game_state.white_to_move else 'b'): # Mettre en évidence la pièce sélectionnée
            # Carré sélectionné
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100) #transparence value 0 -> transparent, 255 -> opaque
            s.fill(p.Color('blue'))
            screen.blit(s, (col*SQ_SIZE, row*SQ_SIZE))
            # Mettre en évidence les mouvements valides
            s.fill(p.Color('yellow'))
            for move in valid_moves:
                if move.start_row == row and move.start_col == col:
                    screen.blit(s, (move.end_col*SQ_SIZE, move.end_row*SQ_SIZE))

def drawPieces(screen, board):
    """
    Dessiner les pièces sur les carrés
    """
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))


def animateMove(move, screen, board, clock):
    '''
    Animation pour les mouvements
    '''
    global colors
    d_row = move.end_row - move.start_row
    d_col = move.end_col - move.start_col
    frames_per_square = 10 # frames pour déplacer une case
    frame_count = (abs(d_row) + abs(d_col)) * frames_per_square
    for frame in range(frame_count + 1):
        row, col = (move.start_row + d_row * frame / frame_count, move.start_col + d_col * frame / frame_count)
        drawBoard(screen)
        drawPieces(screen, board)
        # Supprimer la pièce déplacée de la case de départ
        color = colors[(move.end_row + move.end_col) % 2]
        end_square = p.Rect(move.end_col*SQ_SIZE, move.end_row*SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, end_square)
        # Dessiner la pièce capturée dans la case de fin
        if move.piece_captured != '--':
            if move.is_enpassant_move:
                enpassant_row = move.end_row + 1 if move.piece_captured[0] == 'b' else move.end_row - 1
                end_square = p.Rect(move.end_col * SQ_SIZE, enpassant_row * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            screen.blit(IMAGES[move.piece_captured], end_square)
        #draw moving piece
        screen.blit(IMAGES[move.piece_moved], p.Rect(col*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)


def drawMoveLog(screen, game_state, font):
    '''
    Dessine le journal des mouvements
    '''
    move_log_rect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color('black'), move_log_rect)
    move_log = game_state.move_log
    move_texts = []
    for i in range(0, len(move_log), 2):
        move_string = str(i // 2 + 1) + '. ' + str(move_log[i]) + " "
        if i + 1 < len(move_log):
            move_string += str(move_log[i + 1]) + "  "
        move_texts.append(move_string)

    moves_per_row = 3
    padding = 5
    line_spacing = 2
    text_y = padding
    for i in range(0, len(move_texts), moves_per_row):
        text = ""
        for j in range(moves_per_row):
            if i + j < len(move_texts):
                text += move_texts[i + j]
        text_object = font.render(text, True, p.Color('white'))
        text_location = move_log_rect.move(padding, text_y)
        screen.blit(text_object, text_location)
        text_y += text_object.get_height() + line_spacing


def saveGame(moves_list):
    result = moves_list.pop()
    turns_dict = {}
    for i in range(len(moves_list) - 1, -1, -1):
        try:
            int(moves_list[i][1])
            if moves_list[i][1] not in turns_dict:
                turns_dict[moves_list[i][1]] = moves_list[i][1:] + "\n"
        except:
            pass
    file = open("last_game_logs.txt", "w")
    for turn in sorted(turns_dict.keys()):
        file.write(turns_dict[turn])
    file.write(result)
    file.close()


def drawEndGameText(screen, text):
    font = p.font.SysFont("Helvitica", 32, True, False)
    text_object = font.render(text, 0, p.Color("gray"))
    text_location = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - text_object.get_width() / 2,
                                                                 BOARD_HEIGHT / 2 - text_object.get_height() / 2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, 0, p.Color('black'))
    screen.blit(text_object, text_location.move(2, 2))


if __name__ == "__main__":
    main()