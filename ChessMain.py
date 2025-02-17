"""
Fichier Principal, gérant les entrées et sorties du jeu
"""

import pygame as p
import sys
import os
from multiprocessing import Process, Queue

# Importer les modules
import ChessEngine, ChessAI

# Configurations
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# Constantes
BOARD_WIDTH = BOARD_HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8
SQ_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

# Variables globales pour le journal scrollable
MOVE_LOG_OFFSET = 0
SCROLL_SPEED = 20

# Variables pour la promotion de pion
promotion_popup = None
promotion_pending_move = None

# --------------------------------------------------
# Classes UI
# --------------------------------------------------
class Button:
    def __init__(self, text, pos, size, callback):
        self.text = text
        self.pos = pos
        self.size = size
        self.callback = callback
        self.rect = p.Rect(pos, size)
        self.hovered = False

    def draw(self, screen):
        color = p.Color('dodgerblue2') if self.hovered else p.Color('lightgray')
        p.draw.rect(screen, color, self.rect)
        font = p.font.SysFont("Arial", 24)
        text_surf = font.render(self.text, True, p.Color('black'))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

class PromotionPopup:
    def __init__(self, pos, size, callback):
        self.rect = p.Rect(pos, size)
        self.pieces = ['Q', 'R', 'B', 'N']
        self.buttons = []
        btn_size = (60, 60)
        for i, piece in enumerate(self.pieces):
            x = self.rect.x + 10 + i * (btn_size[0] + 10)
            y = self.rect.centery - btn_size[1] // 2
            # Chaque bouton renvoie la pièce choisie via le callback
            self.buttons.append(Button(piece, (x, y), btn_size, lambda p=piece: callback(p)))

    def draw(self, screen):
        p.draw.rect(screen, p.Color('white'), self.rect)
        p.draw.rect(screen, p.Color('black'), self.rect, 3)
        for btn in self.buttons:
            btn.check_hover(p.mouse.get_pos())
            btn.draw(screen)

# --------------------------------------------------
# Fonctions d'interface et de dessin
# --------------------------------------------------
def loadImages():
    pieces = ["wp", "wR", "wN", "wB", "wQ", "wK",
              "bp", "bR", "bN", "bB", "bQ", "bK"]
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))

def drawBoard(screen):
    colors = [p.Color("white"), p.Color("gray")]
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            color = colors[(row + col) % 2]
            p.draw.rect(screen, color, p.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def highlightSquares(screen, game_state, valid_moves, square_selected):
    # Surbrillance du roi en échec
    if game_state.in_check:
        king_row, king_col = game_state.white_king_location if game_state.white_to_move else game_state.black_king_location
        s = p.Surface((SQ_SIZE, SQ_SIZE))
        s.set_alpha(150)
        s.fill(p.Color('red'))
        screen.blit(s, (king_col * SQ_SIZE, king_row * SQ_SIZE))
    # Surbrillance du dernier coup
    if len(game_state.move_log) > 0:
        last_move = game_state.move_log[-1]
        s = p.Surface((SQ_SIZE, SQ_SIZE))
        s.set_alpha(100)
        s.fill(p.Color('green'))
        screen.blit(s, (last_move.end_col * SQ_SIZE, last_move.end_row * SQ_SIZE))
    # Surbrillance de la case sélectionnée et des coups possibles
    if square_selected != ():
        row, col = square_selected
        if game_state.board[row][col][0] == ('w' if game_state.white_to_move else 'b'):
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)
            s.fill(p.Color('blue'))
            screen.blit(s, (col * SQ_SIZE, row * SQ_SIZE))
            s.fill(p.Color('yellow'))
            for move in valid_moves:
                if move.start_row == row and move.start_col == col:
                    screen.blit(s, (move.end_col * SQ_SIZE, move.end_row * SQ_SIZE))

def drawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def animateMove(move, screen, board, clock):
    d_row = move.end_row - move.start_row
    d_col = move.end_col - move.start_col
    frames_per_square = 1
    frame_count = (abs(d_row) + abs(d_col)) * frames_per_square
    for frame in range(frame_count + 1):
        row = move.start_row + d_row * frame / frame_count
        col = move.start_col + d_col * frame / frame_count
        drawBoard(screen)
        drawPieces(screen, board)
        color = p.Color('white') if (move.end_row + move.end_col) % 2 == 0 else p.Color('gray')
        end_square = p.Rect(move.end_col * SQ_SIZE, move.end_row * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, end_square)
        if move.piece_captured != '--':
            if move.is_enpassant_move:
                enpassant_row = move.end_row + 1 if move.piece_captured[0] == 'b' else move.end_row - 1
                end_square = p.Rect(move.end_col * SQ_SIZE, enpassant_row * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            screen.blit(IMAGES[move.piece_captured], end_square)
        screen.blit(IMAGES[move.piece_moved], p.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)

def drawMoveLog(screen, game_state, font):
    global MOVE_LOG_OFFSET
    move_log_rect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color('black'), move_log_rect)
    move_texts = []
    for i in range(0, len(game_state.move_log), 2):
        move_str = f"{i//2 + 1}. {game_state.move_log[i]} "
        if i+1 < len(game_state.move_log):
            move_str += f"{game_state.move_log[i+1]}"
        move_texts.append(move_str)
    scroll_area = p.Surface((MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT))
    scroll_area.fill(p.Color('black'))
    y = 5 - MOVE_LOG_OFFSET
    for i, text in enumerate(move_texts):
        color = p.Color('yellow') if i == len(move_texts)-1 else p.Color('white')
        text_surf = font.render(text, True, color)
        scroll_area.blit(text_surf, (5, y))
        y += font.get_height() + 2
    screen.blit(scroll_area, (BOARD_WIDTH, 0))

def drawLoadingIndicator(screen):
    font = p.font.SysFont("Arial", 24)
    dots = "." * ((p.time.get_ticks() // 500) % 4)
    text = font.render("IA réfléchit" + dots, True, p.Color('white'))
    screen.blit(text, (BOARD_WIDTH + 10, BOARD_HEIGHT - 40))

def drawGameState(screen, game_state, valid_moves, square_selected, move_log_font):
    drawBoard(screen)
    highlightSquares(screen, game_state, valid_moves, square_selected)
    drawPieces(screen, game_state.board)

# --------------------------------------------------
# Menus UI
# --------------------------------------------------
def open_color_selection(mode):
    screen = p.display.set_mode((800,600), p.RESIZABLE)
    buttons = []
    button_width = 200
    button_height = 50
    spacing = 20
    total_height = 2 * button_height + spacing
    start_y = (600 - total_height) // 2
    positions = [
        (400 - button_width // 2, start_y),
        (400 - button_width // 2, start_y + button_height + spacing)
    ]
    buttons.append(Button("Blanc", positions[0], (button_width, button_height), lambda: (mode, True, False)))
    buttons.append(Button("Noir", positions[1], (button_width, button_height), lambda: (mode, False, True)))
    while True:
        screen.fill(p.Color("white"))
        for btn in buttons:
            btn.check_hover(p.mouse.get_pos())
            btn.draw(screen)
        for e in p.event.get():
            if e.type == p.QUIT:
                sys.exit()
            if e.type == p.MOUSEBUTTONDOWN:
                for btn in buttons:
                    if btn.rect.collidepoint(e.pos):
                        return btn.callback()
        p.display.flip()

def gameModeMenu():
    p.font.init()  # Initialize the font module explicitly
    screen = p.display.set_mode((800, 600), p.RESIZABLE)
    buttons = []
    button_width = 200
    button_height = 50
    spacing = 20
    total_height = 4 * button_height + 3 * spacing
    start_y = (600 - total_height) // 2
    positions = [
        (400 - button_width // 2, start_y),
        (400 - button_width // 2, start_y + button_height + spacing),
        (400 - button_width // 2, start_y + 2 * (button_height + spacing)),
        (400 - button_width // 2, start_y + 3 * (button_height + spacing))
    ]
    buttons.append(Button("Joueur vs Joueur", positions[0], (button_width, button_height), lambda: ("PvP", True, True)))
    buttons.append(Button("Joueur vs IA", positions[1], (button_width, button_height), lambda: open_color_selection("PvC")))
    buttons.append(Button("IA vs IA", positions[2], (button_width, button_height), lambda: ("CvC", False, False)))
    buttons.append(Button("Quitter", positions[3], (button_width, button_height), lambda: sys.exit()))
    while True:
        screen.fill(p.Color("white"))
        for btn in buttons:
            btn.check_hover(p.mouse.get_pos())
            btn.draw(screen)
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()  # Quit Pygame completely
                sys.exit() # Exit the program
            if e.type == p.MOUSEBUTTONDOWN:
                for btn in buttons:
                    if btn.rect.collidepoint(e.pos):
                        return btn.callback()
        p.display.flip()

# --------------------------------------------------
# Fonction principale
# --------------------------------------------------
def main():
    global promotion_popup, promotion_pending_move, MOVE_LOG_OFFSET

    mode, player_one, player_two = gameModeMenu()
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    loadImages()
    game_state = ChessEngine.GameState()
    valid_moves = game_state.getValidMoves()
    move_made = False
    animate = False
    square_selected = ()
    player_clicks = []
    game_over = False
    ai_thinking = False
    move_undone = False
    move_finder_process = None
    return_queue = None
    move_log_font = p.font.SysFont("Arial", 14)

    # Boucle principale
    while True:
        human_turn = (game_state.white_to_move and player_one) or (not game_state.white_to_move and player_two)
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                sys.exit()
            # Gestion du scroll du journal
            if e.type == p.MOUSEWHEEL:
                mouse_pos = p.mouse.get_pos()
                move_log_rect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
                if move_log_rect.collidepoint(mouse_pos):
                    MOVE_LOG_OFFSET = max(0, MOVE_LOG_OFFSET - e.y * SCROLL_SPEED)
            # Si une popup de promotion est active, on gère ses clics en priorité
            if promotion_popup:
                if e.type == p.MOUSEBUTTONDOWN:
                    for btn in promotion_popup.buttons:
                        if btn.rect.collidepoint(e.pos):
                            # La fonction callback de la popup renvoie la pièce choisie
                            chosen_piece = btn.callback()  # ici, callback renvoie un tuple, on récupère la pièce
                            # On redéfinit le callback pour renvoyer la pièce choisie
                            promotion_callback = lambda: chosen_piece[0][-1] if chosen_piece[0] in ["PvC", "PvP", "CvC"] else chosen_piece[0]
                            game_state.makeMove(promotion_pending_move, promotion_callback= lambda: btn.text)
                            move_made = True
                            animate = True
                            promotion_popup = None
                            promotion_pending_move = None
                continue  # On ignore les autres événements tant que la popup est affichée

            if e.type == p.MOUSEBUTTONDOWN:
                if not game_over and human_turn:
                    location = p.mouse.get_pos()
                    col = location[0] // SQ_SIZE
                    row = location[1] // SQ_SIZE
                    if col >= DIMENSION or row >= DIMENSION:
                        continue

                    # Premier clic : on s'assure que la case cliquée contient bien ta pièce
                    if len(player_clicks) == 0:
                        piece = game_state.board[row][col]
                        if piece == "--" or piece[0] != ('w' if game_state.white_to_move else 'b'):
                            # Réinitialise la sélection si le clic est invalide
                            square_selected = ()
                            player_clicks = []
                            continue
                        else:
                            square_selected = (row, col)
                            player_clicks.append(square_selected)
                    else:
                        # Deuxième clic : la case de destination peut être vide ou occupée
                        square_selected = (row, col)
                        player_clicks.append(square_selected)

                    if len(player_clicks) == 2:
                        move = ChessEngine.Move(player_clicks[0], player_clicks[1], game_state.board)
                        for valid_move in valid_moves:
                            if move == valid_move:
                                if valid_move.is_pawn_promotion:
                                    promotion_pending_move = valid_move
                                    promotion_popup = PromotionPopup((BOARD_WIDTH // 2 - 150, BOARD_HEIGHT // 2 - 50),
                                                                     (300, 100),
                                                                     lambda piece: piece)
                                else:
                                    game_state.makeMove(valid_move)
                                    move_made = True
                                square_selected = ()
                                player_clicks = []
                                break

            if e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    if len(game_state.move_log) > 0:
                        game_state.undoMove()
                    if len(game_state.move_log) > 0:
                        game_state.undoMove()
                    move_made = True
                    animate = False
                    game_over = False
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True

                if e.key == p.K_r:
                    game_state = ChessEngine.GameState()
                    valid_moves = game_state.getValidMoves()
                    square_selected = ()
                    player_clicks = []
                    move_made = False
                    animate = False
                    game_over = False
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True
                    print("Reset de la partie")

        # Gestion du coup de l'IA
        if not game_over and not human_turn and not move_undone and not promotion_popup:
            if not ai_thinking:
                ai_thinking = True
                return_queue = Queue()
                move_finder_process = Process(target=ChessAI.findBestMove, args=(game_state, valid_moves, return_queue))
                move_finder_process.start()
            if move_finder_process and not move_finder_process.is_alive():
                ai_move = return_queue.get()
                if ai_move is None:
                    ai_move = ChessAI.findRandomMove(valid_moves)
                game_state.makeMove(ai_move)
                move_made = True
                animate = True
                ai_thinking = False

        if move_made:
            if animate:
                animateMove(game_state.move_log[-1], screen, game_state.board, clock)
            valid_moves = game_state.getValidMoves()
            move_made = False
            animate = False
            move_undone = False

        drawGameState(screen, game_state, valid_moves, square_selected, move_log_font)
        drawMoveLog(screen, game_state, move_log_font)
        if ai_thinking:
            drawLoadingIndicator(screen)
        if promotion_popup:
            promotion_popup.draw(screen)

        if game_state.checkmate:
            game_over = True
            end_text = "Noir gagne par échec et mat" if game_state.white_to_move else "Blanc gagne par échec et mat"
            drawEndGameText(screen, end_text)
        elif game_state.stalemate:
            game_over = True
            drawEndGameText(screen, "Impasse")
        clock.tick(MAX_FPS)
        p.display.flip()

def drawEndGameText(screen, text):
    font = p.font.SysFont("Helvitica", 32, True, False)
    text_object = font.render(text, True, p.Color("gray"))
    text_location = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - text_object.get_width() / 2,
                                                                 BOARD_HEIGHT / 2 - text_object.get_height() / 2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, True, p.Color('black'))
    screen.blit(text_object, text_location.move(2, 2))

if __name__ == "__main__":
    main()
