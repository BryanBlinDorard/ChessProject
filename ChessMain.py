"""
Fichier Pricipal, gérera les entrées et sorties du jeu
"""
from wsgiref.validate import validator

import pygame as p
import ChessEngine

WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

"""
Initialiser un dictionnaire global des images. Cela sera appelé exactement une fois dans le main
"""
def loadImages():
    pieces = ["wp", "wR", "wN", "wB", "wQ", "wK", "bp", "bR", "bN", "bB", "bQ", "bK"]
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))


"""
Le code principal pour gérer les entrées utilisateur et mettre à jour l'interface graphique
"""
def main():
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessEngine.GameState()
    validMoves = gs.getValidMoves()
    moveMade = False # pour gérer les événements de clics

    loadImages()
    running = True
    sqSelected = () # aucun carré n'est sélectionné, garde une trace du dernier clic de l'utilisateur (tuple : (row, col))
    playerClicks = [] # garde une trace des clics du joueur (deux tuples : [(6, 4), (4, 4)])
    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            elif e.type == p.MOUSEBUTTONDOWN:
                location = p.mouse.get_pos() # (x, y) Location de la souris
                col = location[0]//SQ_SIZE
                row = location[1]//SQ_SIZE
                if sqSelected == (row, col): # l'utilisateur a cliqué deux fois sur la même case
                    sqSelected = () # désélectionne
                    playerClicks = [] # efface les clics du joueur
                else:
                    sqSelected = (row, col)
                    playerClicks.append(sqSelected) # ajoute au clic
                if len(playerClicks) == 2: # après le deuxième clic
                    move = ChessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                    for i in range(len(validMoves)):
                        if move == validMoves[i]:
                            print(move.getChessNotation())
                            gs.makeMove(validMoves[i])
                            moveMade = True
                            sqSelected = ()
                            playerClicks = []
                    if not moveMade:
                        playerClicks = [sqSelected]
            # Vérifie si une touche est enfoncée
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    gs.undoMove()
                    moveMade = True

        if moveMade:
            validMoves = gs.getValidMoves()
            moveMade = False

        drawGameState(screen, gs)
        clock.tick(MAX_FPS)
        p.display.flip()

"""
Gère tous les graphiques du jeu
"""
def drawGameState(screen, gs):
    drawBoard(screen) # dessine les carrés sur le tableau
    drawPieces(screen, gs.board) # dessine les pièces sur les carrés

"""
Dessiner les carrés sur le tableau
"""
def drawBoard(screen):
    colors = [p.Color("white"), p.Color("gray")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r+c) % 2)]
            p.draw.rect(screen, color, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

"""
Dessiner les pièces sur les carrés
"""
def drawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

if __name__ == "__main__":
    main()