"""
Fichier Principal, gérant les entrées/sorties, la personnalisation et les sauvegardes.
"""

import pygame as p
import sys, os, pickle
from multiprocessing import Process, Queue
import ChessEngine, ChessAI

# --------------------------------------------------
# Constantes d'affichage
# --------------------------------------------------
DIMENSION = 8
BOARD_WIDTH = BOARD_HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
MAX_FPS = 15
SQ_SIZE = BOARD_HEIGHT // DIMENSION

# Drapeau pour inverser le plateau (True = plateau retourné, i.e. les noirs en bas)
flip_board = False

# --------------------------------------------------
# Gestion des ressources
# --------------------------------------------------
class ResourceManager:
    _instance = None

    def __new__(cls, sq_size, image_path="images"):
        if cls._instance is None:
            cls._instance = super(ResourceManager, cls).__new__(cls)
            cls._instance.sq_size = sq_size
            cls._instance.image_path = image_path
            cls._instance.cache = {}
        return cls._instance

    def get_image(self, piece):
        if piece in self.cache:
            return self.cache[piece]
        path = os.path.join(self.image_path, piece + ".png")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Image not found: {path}")
        image = p.transform.scale(p.image.load(path), (self.sq_size, self.sq_size))
        self.cache[piece] = image
        return image

# --------------------------------------------------
# UI Manager
# --------------------------------------------------
class UIManager:
    def __init__(self, board_width, board_height, move_log_panel_width, move_log_panel_height):
        self.board_width = board_width
        self.board_height = board_height
        self.move_log_panel_width = move_log_panel_width
        self.move_log_panel_height = move_log_panel_height
        self.move_log_offset = 0
        self.SCROLL_SPEED = 20
        # Couleurs par défaut du plateau
        self.board_color1 = p.Color("white")
        self.board_color2 = p.Color("gray")

    def draw_move_log(self, screen, game_state, font):
        move_log_rect = p.Rect(self.board_width, 0, self.move_log_panel_width, self.move_log_panel_height)
        p.draw.rect(screen, p.Color('black'), move_log_rect)
        move_texts = []
        for i in range(0, len(game_state.move_log), 2):
            move_str = f"{i//2 + 1}. {game_state.move_log[i]} "
            if i+1 < len(game_state.move_log):
                move_str += f"{game_state.move_log[i+1]}"
            move_texts.append(move_str)
        scroll_area = p.Surface((self.move_log_panel_width, self.move_log_panel_height))
        scroll_area.fill(p.Color('black'))
        y = 5 - self.move_log_offset
        for i, text in enumerate(move_texts):
            color = p.Color('yellow') if i == len(move_texts)-1 else p.Color('white')
            text_surf = font.render(text, True, color)
            scroll_area.blit(text_surf, (5, y))
            y += font.get_height() + 2
        screen.blit(scroll_area, (self.board_width, 0))

    def handle_scroll(self, event, mouse_pos):
        move_log_rect = p.Rect(self.board_width, 0, self.move_log_panel_width, self.move_log_panel_height)
        if move_log_rect.collidepoint(mouse_pos):
            self.move_log_offset = max(0, self.move_log_offset - event.y * self.SCROLL_SPEED)

    def draw_loading_indicator(self, screen):
        font = p.font.SysFont("Arial", 24)
        dots = "." * ((p.time.get_ticks() // 500) % 4)
        text = font.render("IA réfléchit" + dots, True, p.Color('white'))
        screen.blit(text, (self.board_width + 10, self.board_height - 40))

# --------------------------------------------------
# Classes UI de base
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
            self.buttons.append(Button(piece, (x, y), btn_size, lambda p=piece: callback(p)))

    def draw(self, screen):
        p.draw.rect(screen, p.Color('white'), self.rect)
        p.draw.rect(screen, p.Color('black'), self.rect, 3)
        for btn in self.buttons:
            btn.check_hover(p.mouse.get_pos())
            btn.draw(screen)

# --------------------------------------------------
# Module d'animation
# --------------------------------------------------
class Animation:
    @staticmethod
    def easeOutCubic(t: float) -> float:
        """Fonction easing pour une interpolation plus fluide (t entre 0 et 1)."""
        return 1 - pow(1 - t, 3)

    @staticmethod
    def animate_move(move: ChessEngine.Move, screen: p.Surface, board: list, sq_size: int, clock: p.time.Clock):
        d_row = move.end_row - move.start_row
        d_col = move.end_col - move.start_col
        frames_per_square = 3  # augmente pour une animation plus longue
        frame_count = int((abs(d_row) + abs(d_col)) * frames_per_square)
        resource_manager = ResourceManager(sq_size)
        for frame in range(frame_count + 1):
            t = frame / frame_count  # t varie de 0 à 1
            eased_t = Animation.easeOutCubic(t)
            row = move.start_row + d_row * eased_t
            col = move.start_col + d_col * eased_t
            if flip_board:
                disp_row = DIMENSION - 1 - row
            else:
                disp_row = row
            draw_board(screen, sq_size)
            draw_pieces(screen, board, sq_size, resource_manager)
            if flip_board:
                disp_end_row = DIMENSION - 1 - move.end_row
            else:
                disp_end_row = move.end_row
            color = ui_manager.board_color1 if (disp_end_row + move.end_col) % 2 == 0 else ui_manager.board_color2
            end_square = p.Rect(move.end_col * sq_size, disp_end_row * sq_size, sq_size, sq_size)
            p.draw.rect(screen, color, end_square)
            if move.piece_captured != '--':
                if move.is_enpassant_move:
                    enpassant_row = move.end_row + 1 if move.piece_captured[0] == 'b' else move.end_row - 1
                    if flip_board:
                        enpassant_row = DIMENSION - 1 - enpassant_row
                    end_square = p.Rect(move.end_col * sq_size, enpassant_row * sq_size, sq_size, sq_size)
                image = resource_manager.get_image(move.piece_captured)
                screen.blit(image, end_square)
            image = resource_manager.get_image(move.piece_moved)
            if flip_board:
                disp_current_row = DIMENSION - 1 - row
            else:
                disp_current_row = row
            screen.blit(image, p.Rect(col * sq_size, disp_current_row * sq_size, sq_size, sq_size))
            p.display.flip()
            clock.tick(60)


# --------------------------------------------------
# Fonctions de dessin
# --------------------------------------------------
def draw_board(screen, sq_size):
    for row in range(DIMENSION):
        # Calcul de la ligne d'affichage en fonction du flip
        display_row = row if not flip_board else DIMENSION - 1 - row
        for col in range(DIMENSION):
            color = ui_manager.board_color1 if (display_row + col) % 2 == 0 else ui_manager.board_color2
            p.draw.rect(screen, color, p.Rect(col * sq_size, display_row * sq_size, sq_size, sq_size))

def draw_pieces(screen, board, sq_size, resource_manager):
    for row in range(DIMENSION):
        # La ligne affichée dépend du flip
        display_row = row if not flip_board else DIMENSION - 1 - row
        for col in range(DIMENSION):
            piece = board[row][col]
            if piece != "--":
                screen.blit(resource_manager.get_image(piece), p.Rect(col * sq_size, display_row * sq_size, sq_size, sq_size))

def highlightSquares(screen, game_state, valid_moves, square_selected, sq_size):
    if game_state.in_check:
        king_row, king_col = game_state.white_king_location if game_state.white_to_move else game_state.black_king_location
        if flip_board:
            king_row = DIMENSION - 1 - king_row
        s = p.Surface((sq_size, sq_size))
        s.set_alpha(150)
        s.fill(p.Color('red'))
        screen.blit(s, (king_col * sq_size, king_row * sq_size))
    if game_state.move_log:
        last_move = game_state.move_log[-1]
        if flip_board:
            disp_end_row = DIMENSION - 1 - last_move.end_row
        else:
            disp_end_row = last_move.end_row
        s = p.Surface((sq_size, sq_size))
        s.set_alpha(100)
        s.fill(p.Color('green'))
        screen.blit(s, (last_move.end_col * sq_size, disp_end_row * sq_size))
    if square_selected:
        row, col = square_selected
        # Pour la sélection, on ne transforme pas car la conversion s'effectue lors de l'interprétation des clics
        s = p.Surface((sq_size, sq_size))
        s.set_alpha(100)
        s.fill(p.Color('blue'))
        # Convertir la ligne de sélection
        disp_row = row if not flip_board else DIMENSION - 1 - row
        screen.blit(s, (col * sq_size, disp_row * sq_size))
        s.fill(p.Color('yellow'))
        for move in valid_moves:
            if move.start_row == row and move.start_col == col:
                target_row = move.end_row if not flip_board else DIMENSION - 1 - move.end_row
                screen.blit(s, (move.end_col * sq_size, target_row * sq_size))

def drawEndGameText(screen, text, board_width, board_height):
    font = p.font.SysFont("Helvitica", 32, True, False)
    text_object = font.render(text, True, p.Color("gray"))
    text_location = p.Rect(0, 0, board_width, board_height).move(board_width/2 - text_object.get_width()/2,
                                                                 board_height/2 - text_object.get_height()/2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, True, p.Color('black'))
    screen.blit(text_object, text_location.move(2, 2))

# --------------------------------------------------
# Sauvegarde / Chargement
# --------------------------------------------------
def save_game(game_state, filename="saved_game.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(game_state, f)

def load_game(filename="saved_game.pkl"):
    with open(filename, "rb") as f:
        return pickle.load(f)

# --------------------------------------------------
# Menus dynamiques de personnalisation
# --------------------------------------------------
def gameModeMenu(screen):
    buttons = []
    button_width = 200
    button_height = 50
    spacing = 20
    menu_surface = p.Surface(screen.get_size())
    menu_surface.fill(p.Color("white"))
    w, h = screen.get_size()
    total_height = 4 * button_height + 3 * spacing
    start_y = (h - total_height) // 2
    positions = [
        ((w - button_width) // 2, start_y),
        ((w - button_width) // 2, start_y + button_height + spacing),
        ((w - button_width) // 2, start_y + 2 * (button_height + spacing)),
        ((w - button_width) // 2, start_y + 3 * (button_height + spacing))
    ]
    buttons.append(Button("Joueur vs Joueur", positions[0], (button_width, button_height), lambda: ("PvP", True, True)))
    buttons.append(Button("Joueur vs IA", positions[1], (button_width, button_height), lambda: open_color_selection(screen, "PvC")))
    buttons.append(Button("IA vs IA", positions[2], (button_width, button_height), lambda: ("CvC", False, False)))
    buttons.append(Button("Quitter", positions[3], (button_width, button_height), lambda: sys.exit()))
    while True:
        menu_surface.fill(p.Color("white"))
        for btn in buttons:
            btn.check_hover(p.mouse.get_pos())
            btn.draw(menu_surface)
        for e in p.event.get():
            if e.type == p.QUIT:
                sys.exit()
            if e.type == p.MOUSEBUTTONDOWN:
                for btn in buttons:
                    if btn.rect.collidepoint(e.pos):
                        return btn.callback()
        screen.blit(menu_surface, (0, 0))
        p.display.flip()

def open_color_selection(screen, mode):
    buttons = []
    button_width = 200
    button_height = 50
    spacing = 20
    menu_surface = p.Surface(screen.get_size())
    menu_surface.fill(p.Color("white"))
    w, h = screen.get_size()
    total_height = 2 * button_height + spacing
    start_y = (h - total_height) // 2
    positions = [
        ((w - button_width) // 2, start_y),
        ((w - button_width) // 2, start_y + button_height + spacing)
    ]
    buttons.append(Button("Blanc", positions[0], (button_width, button_height), lambda: (mode, True, False)))
    buttons.append(Button("Noir", positions[1], (button_width, button_height), lambda: (mode, False, True)))
    while True:
        menu_surface.fill(p.Color("white"))
        for btn in buttons:
            btn.check_hover(p.mouse.get_pos())
            btn.draw(menu_surface)
        for e in p.event.get():
            if e.type == p.QUIT:
                sys.exit()
            if e.type == p.MOUSEBUTTONDOWN:
                for btn in buttons:
                    if btn.rect.collidepoint(e.pos):
                        return btn.callback()
        screen.blit(menu_surface, (0, 0))
        p.display.flip()

def customization_menu(screen, ui_manager):
    options = [
        (p.Color("white"), p.Color("gray")),
        (p.Color("beige"), p.Color("saddlebrown")),
        (p.Color("lightgreen"), p.Color("darkgreen"))
    ]
    buttons = []
    button_width = 250
    button_height = 50
    spacing = 20
    menu_surface = p.Surface(screen.get_size())
    menu_surface.fill(p.Color("white"))
    w, h = screen.get_size()
    total_height = len(options) * button_height + (len(options) - 1) * spacing
    start_y = (h - total_height) // 2
    for i, (col1, col2) in enumerate(options):
        pos = ((w - button_width) // 2, start_y + i*(button_height + spacing))
        def callback(c1=col1, c2=col2):
            ui_manager.board_color1 = c1
            ui_manager.board_color2 = c2
        buttons.append(Button(f"Couleurs {i+1}", pos, (button_width, button_height), callback))
    while True:
        menu_surface.fill(p.Color("white"))
        for btn in buttons:
            btn.check_hover(p.mouse.get_pos())
            btn.draw(menu_surface)
        for e in p.event.get():
            if e.type == p.QUIT:
                sys.exit()
            if e.type == p.MOUSEBUTTONDOWN:
                for btn in buttons:
                    if btn.rect.collidepoint(e.pos):
                        btn.callback()
                        return
        screen.blit(menu_surface, (0, 0))
        p.display.flip()

# --------------------------------------------------
# Fonction principale
# --------------------------------------------------
def main():
    global flip_board, ui_manager
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT), p.RESIZABLE)
    clock = p.time.Clock()
    ui_manager = UIManager(BOARD_WIDTH, BOARD_HEIGHT, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    resource_manager = ResourceManager(SQ_SIZE)
    game_state = ChessEngine.GameState()
    valid_moves = game_state.getValidMoves()
    move_made = False
    animate = False
    square_selected = ()
    player_clicks = []
    game_over = False
    ai_thinking = False
    move_undone = False
    promotion_popup = None
    promotion_pending_move = None
    move_finder_process = None
    return_queue = None
    move_log_font = p.font.SysFont("Arial", 14)

    # Choix du mode de jeu
    mode, player_one, player_two = gameModeMenu(screen)
    # Si en mode PvC et que le joueur humain joue les noirs, on inverse le plateau.
    if mode == "PvC" and not player_one:
        flip_board = True
    else:
        flip_board = False

    # Boucle principale
    while True:
        # Conversion des clics : si flip_board, convertir la ligne (pour la saisie)
        human_turn = (game_state.white_to_move and player_one) or (not game_state.white_to_move and player_two)
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                sys.exit()
            if e.type == p.MOUSEWHEEL:
                ui_manager.handle_scroll(e, p.mouse.get_pos())
            # Si une popup de promotion est active, traiter ses clics en priorité
            if promotion_popup:
                if e.type == p.MOUSEBUTTONDOWN:
                    for btn in promotion_popup.buttons:
                        if btn.rect.collidepoint(e.pos):
                            promotion_callback = lambda: btn.text
                            game_state.makeMove(promotion_pending_move, promotion_callback=promotion_callback)
                            move_made = True
                            animate = True
                            promotion_popup = None
                            promotion_pending_move = None
                continue
            if e.type == p.MOUSEBUTTONDOWN:
                if not game_over and human_turn:
                    location = p.mouse.get_pos()
                    col = location[0] // SQ_SIZE
                    # Conversion de la coordonnée verticale selon flip_board
                    if flip_board:
                        row = DIMENSION - 1 - (location[1] // SQ_SIZE)
                    else:
                        row = location[1] // SQ_SIZE
                    if col >= DIMENSION or row >= DIMENSION:
                        continue
                    # Premier clic ou modification de sélection
                    if not player_clicks:
                        piece = game_state.board[row][col]
                        if piece == "--" or piece[0] != ('w' if game_state.white_to_move else 'b'):
                            square_selected = ()
                            player_clicks = []
                            continue
                        else:
                            square_selected = (row, col)
                            player_clicks.append(square_selected)
                    else:
                        # Si le joueur clique sur une pièce de son camp, on réinitialise la sélection
                        piece = game_state.board[row][col]
                        if piece != "--" and piece[0] == ('w' if game_state.white_to_move else 'b'):
                            square_selected = (row, col)
                            player_clicks = [square_selected]
                            continue
                        else:
                            square_selected = (row, col)
                            player_clicks.append(square_selected)
                    if len(player_clicks) == 2:
                        move = ChessEngine.Move(player_clicks[0], player_clicks[1], game_state.board)
                        for valid_move in valid_moves:
                            if move == valid_move:
                                if valid_move.is_pawn_promotion:
                                    promotion_pending_move = valid_move
                                    promotion_popup = PromotionPopup((BOARD_WIDTH // 2 - 150, BOARD_HEIGHT // 2 - 50),
                                                                     (300, 100), lambda piece: piece)
                                else:
                                    game_state.makeMove(valid_move)
                                    move_made = True
                                square_selected = ()
                                player_clicks = []
                                break
            if e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    if game_state.move_log:
                        game_state.undoMove()
                    if game_state.move_log:
                        game_state.undoMove()
                    move_made = True
                    animate = False
                    game_over = False
                    if ai_thinking and move_finder_process:
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
                    if ai_thinking and move_finder_process:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True
                if e.key == p.K_s:
                    save_game(game_state)
                if e.key == p.K_l:
                    try:
                        game_state = load_game()
                        valid_moves = game_state.getValidMoves()
                    except Exception as ex:
                        print("Erreur lors du chargement :", ex)
                if e.key == p.K_c:
                    customization_menu(screen, ui_manager)

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
                Animation.animate_move(game_state.move_log[-1], screen, game_state.board, SQ_SIZE, clock)
            valid_moves = game_state.getValidMoves()
            move_made = False
            animate = False
            move_undone = False

        draw_board(screen, SQ_SIZE)
        draw_pieces(screen, game_state.board, SQ_SIZE, resource_manager)
        highlightSquares(screen, game_state, valid_moves, square_selected, SQ_SIZE)
        ui_manager.draw_move_log(screen, game_state, move_log_font)
        if ai_thinking:
            ui_manager.draw_loading_indicator(screen)
        if promotion_popup:
            promotion_popup.draw(screen)
        if game_state.checkmate:
            game_over = True
            end_text = "Noir gagne par échec et mat" if game_state.white_to_move else "Blanc gagne par échec et mat"
            drawEndGameText(screen, end_text, BOARD_WIDTH, BOARD_HEIGHT)
        elif game_state.stalemate:
            game_over = True
            drawEndGameText(screen, "Impasse", BOARD_WIDTH, BOARD_HEIGHT)
        clock.tick(MAX_FPS)
        p.display.flip()

if __name__ == "__main__":
    main()