"""
Fichier gérant les informations du jeu
"""
class GameState():
    def __init__(self):
        # Board is an 8x8 2D List, each element of the list has 2 characters.
        # The first character represents the color of the piece (b/w)
        # The second character represents the type of the piece (R, N, B, Q, K, p)
        # "--" represents an empty space with no piece.
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]
        self.moveFunctions = {'p': self.getPawnMoves, 'R': self.getRookMoves, 'N': self.getKnightMoves,
                              'B': self.getBishopMoves, 'Q': self.getQueenMoves, 'K': self.getKingMoves}
        self.whiteToMove = True
        self.moveLog = []
        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)
        self.checkMate = False
        self.staleMate = False

    """
    Fait le mouvement donné en paramètre et l'éxécute (ne vérifie pas si le mouvement est valide)
    """
    def makeMove(self, move):
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moveLog.append(move) # Enregistre le mouvement pour pouvoir l'annuler
        self.whiteToMove = not self.whiteToMove # Changement de joueur
        # Met à jour la position du roi si nécessaire
        if move.pieceMoved == 'wK':
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == 'bK':
            self.blackKingLocation = (move.endRow, move.endCol)

    """
    Annule le dernier mouvement effectué
    """
    def undoMove(self):
        if len(self.moveLog) != 0:
            move = self.moveLog.pop()
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            self.whiteToMove = not self.whiteToMove

    """
    Obtient tous les mouvements possibles pour le joueur actuel
    """
    def getValidMoves(self):
        # 1. Génère tous les mouvements possibles
        moves = self.getAllPossibleMoves()
        # 2. Fait les mouvements possibles
        for i in range(len(moves)-1, -1, -1): # Parcours en sens inverse pour pouvoir supprimer des éléments de la liste
            self.makeMove(moves[i])
            # 3. Vérifie si le joueur actuel est en échec
            opponentMoves = self.getAllPossibleMoves()
            # 4. Vérifie si le joueur actuel est en échec
            self.whiteToMove = not self.whiteToMove
            if self.inCheck(): # 5. Si le joueur est en échec, le mouvement n'est pas valide
                moves.remove(moves[i])
            self.whiteToMove = not self.whiteToMove
            self.undoMove()
        if len(moves) == 0: # 6. Vérifie le mat ou la pat
            if self.inCheck():
                self.checkMate = True
            else:
                self.staleMate = True
        else:
            self.checkMate = False
            self.staleMate = False
        return moves

    """
    Vérifie si le joueur actuel est en échec
    """
    def inCheck(self):
        if self.whiteToMove:
            return self.squareUnderAttack(self.whiteKingLocation[0], self.whiteKingLocation[1])
        else:
            return self.squareUnderAttack(self.blackKingLocation[0], self.blackKingLocation[1])

    """
    Determine si l'ennemi peut attaquer la case (r, c)
    """
    def squareUnderAttack(self, r, c):
        self.whiteToMove = not self.whiteToMove # Change de joueur pour obtenir les mouvements de l'adversaire
        opponentMoves = self.getAllPossibleMoves()
        self.whiteToMove = not self.whiteToMove
        for move in opponentMoves:
            if move.endRow == r and move.endCol == c: # Case attaquée
                return True
        return False

    """
    Obtient tous les mouvements possibles sans vérifier si le joueur met son roi en échec
    """
    def getAllPossibleMoves(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == 'w' and self.whiteToMove) or (turn == 'b' and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r, c, moves) # Appelle la fonction de mouvement appropriée
        return moves

    """
    Obtient tous les mouvements possibles pour une pièce de pion donnée
    """
    def getPawnMoves(self, r, c, moves):
        if self.whiteToMove: # Pion blanc
            if self.board[r-1][c] == "--": # Déplacement d'une case
                moves.append(Move((r, c), (r-1, c), self.board))
                if r == 6 and self.board[r-2][c] == "--": # Déplacement de deux cases
                    moves.append(Move((r, c), (r-2, c), self.board))
            if c-1 >= 0: # Attaque à gauche
                if self.board[r-1][c-1][0] == 'b':
                    moves.append(Move((r, c), (r-1, c-1), self.board))
            if c+1 < len(self.board): # Attaque à droite
                if self.board[r-1][c+1][0] == 'b':
                    moves.append(Move((r, c), (r-1, c+1), self.board))
        else: # Pion noir
            if self.board[r+1][c] == "--": # Déplacement d'une case
                moves.append(Move((r, c), (r+1, c), self.board))
                if r == 1 and self.board[r+2][c] == "--": # Déplacement de deux cases
                    moves.append(Move((r, c), (r+2, c), self.board))
            if c-1 >= 0: # Attaque à gauche
                if self.board[r+1][c-1][0] == 'w':
                    moves.append(Move((r, c), (r+1, c-1), self.board))
            if c+1 < len(self.board): # Attaque à droite
                if self.board[r+1][c+1][0] == 'w':
                    moves.append(Move((r, c), (r+1, c+1), self.board))


    """
    Obtient tous les mouvements possibles pour une pièce de tour donnée
    """
    def getRookMoves(self, r, c, moves):
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1)) # Haut, Gauche, Bas, Droite
        enemyColor = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8): # Les tours peuvent se déplacer de 1 à 7 cases
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8: # Vérifie si la case est dans le tableau
                    endPiece = self.board[endRow][endCol]
                    if endPiece == "--": # Case vide
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                    elif endPiece[0] == enemyColor:
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                        break
                    else: # Case occupée par une pièce alliée
                        break
                else: # Hors du tableau
                    break

    """
    Obtient tous les mouvements possibles pour une pièce de cavalier donnée
    """
    def getKnightMoves(self, r, c, moves):
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        allyColor = "w" if self.whiteToMove else "b"
        for m in knightMoves:
            endRow = r + m[0]
            endCol = c + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor: # Case vide ou ennemie
                    moves.append(Move((r, c), (endRow, endCol), self.board))


    """
    Obtient tous les mouvements possibles pour une pièce de fou donnée
    """
    def getBishopMoves(self, r, c, moves):
        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1)) # Haut-Gauche, Haut-Droite, Bas-Gauche, Bas-Droite
        enemyColor = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece == "--":
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                    elif endPiece[0] == enemyColor:
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                        break
                    else:
                        break
                else:
                    break

    """
    Obtient tous les mouvements possibles pour une pièce de reine donnée
    """
    def getQueenMoves(self, r, c, moves):
        self.getRookMoves(r, c, moves)
        self.getBishopMoves(r, c, moves)

    """
    Obtient tous les mouvements possibles pour une pièce de roi donnée
    """
    def getKingMoves(self, r, c, moves):
        kingMoves = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
        allyColor = "w" if self.whiteToMove else "b"
        for i in range(8):
            endRow = r + kingMoves[i][0]
            endCol = c + kingMoves[i][1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor:
                    moves.append(Move((r, c), (endRow, endCol), self.board))

class Move():
    # Maps keys to values
    # key : value
    ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4,
                   "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}
    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3,
                   "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(self, startSq, endSq, board):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol
        print(self.moveID)

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def getChessNotation(self):
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)

    def getRankFile(self, r, c):
        return self.colsToFiles[c] + self.rowsToRanks[r]

