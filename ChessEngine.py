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
        self.move_functions = {'p': self.getPawnMoves, 'R': self.getRookMoves, 'N': self.getKnightMoves,
                              'B': self.getBishopMoves, 'Q': self.getQueenMoves, 'K': self.getKingMoves}
        self.white_to_move = True
        self.move_log = []
        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)
        self.checkmate = False
        self.stalemate = False
        self.in_check = False
        self.pins = []
        self.checks = []
        self.en_passant_possible = () # Coordonnées pour la case où l'en passant est possible
        self.current_castling_rights = CastleRights(True, True, True, True) # Les droits de roque actuels
        self.castle_rights_log = [CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks, self.current_castling_rights.wqs, self.current_castling_rights.bqs)]


    def makeMove(self, move):
        """
            Fait le mouvement donné en paramètre et l'éxécute (ne vérifie pas si le mouvement est valide)
        """
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move) # Enregistre le mouvement pour pouvoir l'annuler
        self.white_to_move = not self.white_to_move # Changement de joueur
        # Met à jour la position du roi si nécessaire
        if move.piece_moved == 'wK':
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == 'bK':
            self.black_king_location = (move.end_row, move.end_col)

        # Promotion du pion
        if move.is_pawn_promotion:
            promoted_piece = input("Promote to Q, R, B, or N:")  # take this to UI later
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + promoted_piece

        # En passant
        if move.is_enpassant_move:
            self.board[move.start_row][move.end_col] = "--" # Capture le pion

        # Met à jour enPassantPossible
        if move.piece_moved[1] == 'p' and abs(move.start_row - move.end_row) == 2:
            self.en_passant_possible = ((move.start_row + move.end_row) // 2, move.start_col)
        else:
            self.en_passant_possible = ()

        if move.is_castle_move:
            if move.end_col - move.start_col == 2:  #
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][move.end_col + 1]  # Bouge la tour à sa nouvelle case
                self.board[move.end_row][move.end_col + 1] = '--'  # Efface l'ancienne tour
            else:
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 2]  # Bouge la tour à sa nouvelle case
                self.board[move.end_row][move.end_col - 2] = '--'  # Efface l'ancienne tour

        # Met à jour les droits de roque - chaque fois qu'il s'agit d'un mouvement de tour ou de roi
        self.updateCastleRights(move)
        self.castle_rights_log.append(CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                                   self.current_castling_rights.wqs, self.current_castling_rights.bqs))


    def undoMove(self):
        """
            Annule le dernier mouvement effectué
        """
        if len(self.move_log) != 0:
            move = self.move_log.pop()
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.white_to_move = not self.white_to_move
            # Met à jour la position du roi si nécessaire
            if move.piece_moved == 'wK':
                self.white_king_location = (move.start_row, move.start_col)
            elif move.piece_moved == 'bK':
                self.black_king_location = (move.start_row, move.start_col)

            # Annule l'en passant
            if move.is_enpassant_move:
                self.board[move.end_row][move.end_col] = "--"
                self.board[move.start_row][move.end_col] = move.piece_captured
                self.en_passant_possible = (move.end_row, move.end_col)
            # Annule le mouvement double du pion
            if move.piece_moved[1] == 'p' and abs(move.start_row - move.end_row) == 2:
                self.en_passant_possible = ()

            # Annule le droit de roque

            self.castle_rights_log.pop() # Obtenir les nouveaux droits de roque du mouvement que nous annulons
            self.current_castling_rights = self.castle_rights_log[-1] # Mettre à jour les droits de roque
            # Annule le roque
            if move.is_castle_move:
                if move.end_col - move.start_col == 2:
                    self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                    self.board[move.end_row][move.end_col - 1] = '--'
                else:
                    self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                    self.board[move.end_row][move.end_col + 1] = '--'

    def updateCastleRights(self, move):
        '''
        Met à jour les droits de roque en fonction du mouvement donné
        '''
        if move.piece_captured == "wR":
            if move.end_col == 0:  # Roque gauche
                self.current_castling_rights.wqs = False
            elif move.end_col == 7:  # Roque droit
                self.current_castling_rights.wks = False
        elif move.piece_captured == "bR":
            if move.end_col == 0:  # Roque gauche
                self.current_castling_rights.bqs = False
            elif move.end_col == 7:  # Roque droit
                self.current_castling_rights.bks = False

        if move.piece_moved == 'wK':
            self.current_castling_rights.wqs = False
            self.current_castling_rights.wks = False
        elif move.piece_moved == 'bK':
            self.current_castling_rights.bqs = False
            self.current_castling_rights.bks = False
        elif move.piece_moved == 'wR':
            if move.start_row == 7:
                if move.start_col == 0:  # Roque gauche
                    self.current_castling_rights.wqs = False
                elif move.start_col == 7:  # Roque droit
                    self.current_castling_rights.wks = False
        elif move.piece_moved == 'bR':
            if move.start_row == 0:
                if move.start_col == 0:  # Roque gauche
                    self.current_castling_rights.bqs = False
                elif move.start_col == 7:  # Roque droit
                    self.current_castling_rights.bks = False

    def getValidMoves(self):
        """
            Obtient tous les mouvements possibles pour le joueur actuel
        """
        temp_castle_rights = CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                          self.current_castling_rights.wqs, self.current_castling_rights.bqs)
        moves = []
        self.in_check, self.pins, self.checks = self.checkForPinsAndChecks()
        if self.white_to_move:
            kingRow = self.white_king_location[0]
            kingCol = self.white_king_location[1]
        else:
            kingRow = self.black_king_location[0]
            kingCol = self.black_king_location[1]
        if self.in_check:
            if len(self.checks) == 1: # Le joueur est en échec, il doit bouger le roi ou capturer la pièce qui met en échec
                moves = self.getAllPossibleMoves()
                check = self.checks[0]
                checkRow = check[0]
                checkCol = check[1]
                pieceChecking = self.board[checkRow][checkCol] # La pièce qui met en échec
                validSquares = [] # Les cases où le roi peut se déplacer ou les pièces peuvent capturer la pièce qui met en échec

                if pieceChecking[1] == 'N': # Si la pièce qui met en échec est un cavalier, le joueur doit capturer le cavalier ou déplacer le roi
                    validSquares = [(checkRow, checkCol)]
                else:
                    for i in range(1, 8):
                        validSquare = (kingRow + check[2] * i, kingCol + check[3] * i) # Roi se déplace dans la direction de la pièce qui met en échec
                        validSquares.append(validSquare)
                        if validSquare[0] == checkRow and validSquare[1] == checkCol: # Roi peut capturer la pièce qui met en échec
                            break
                # Récupère les mouvements valides
                for i in range(len(moves)-1, -1, -1):
                    if moves[i].piece_moved[1] != 'K': # Le roi ne peut pas capturer une pièce
                        if not (moves[i].end_row, moves[i].end_col) in validSquares:
                            moves.remove(moves[i])
            else: # Le joueur est en échec, il doit bouger le roi
                self.getKingMoves(kingRow, kingCol, moves)
        else: # Le joueur n'est pas en échec, il peut faire n'importe quel mouvement
            moves = self.getAllPossibleMoves()
            if self.white_to_move:
                self.getCastleMoves(self.white_king_location[0], self.white_king_location[1], moves)
            else:
                self.getCastleMoves(self.black_king_location[0], self.black_king_location[1], moves)

        if len(moves) == 0: # Vérifie si le joueur est en échec et mat ou en pat
            if self.in_check:
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        self.current_castling_rights
        return moves

    """
    Vérifie si le joueur actuel est en échec
    """
    def inCheck(self):
        if self.white_to_move:
            return self.squareUnderAttack(self.white_king_location[0], self.white_king_location[1])
        else:
            return self.squareUnderAttack(self.black_king_location[0], self.black_king_location[1])

    """
    Determine si l'ennemi peut attaquer la case (r, c)
    """
    def squareUnderAttack(self, r, c):
        self.white_to_move = not self.white_to_move # Change de joueur pour obtenir les mouvements de l'adversaire
        opponentMoves = self.getAllPossibleMoves()
        self.white_to_move = not self.white_to_move
        for move in opponentMoves:
            if move.end_row == r and move.end_col == c: # Case attaquée
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
                if (turn == 'w' and self.white_to_move) or (turn == 'b' and not self.white_to_move):
                    piece = self.board[r][c][1]
                    self.move_functions[piece](r, c, moves) # Appelle la fonction de mouvement appropriée
        return moves

    def getPawnMoves(self, row, col, moves):
        '''
            Obtient tous les mouvements possibles pour une pièce de pion donnée
        '''
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if self.white_to_move:
            move_amount = -1
            start_row = 6
            enemy_color = "b"
        else:
            move_amount = 1
            start_row = 1
            enemy_color = "w"

        if self.board[row + move_amount][col] == "--":  # 1 square pawn advance
            if not piece_pinned or pin_direction == (move_amount, 0):
                moves.append(Move((row, col), (row + move_amount, col), self.board))
                if row == start_row and self.board[row + 2 * move_amount][col] == "--":  # 2 square pawn advance
                    moves.append(Move((row, col), (row + 2 * move_amount, col), self.board))
        if col - 1 >= 0:  # Capture à gauche
            if not piece_pinned or pin_direction == (move_amount, -1):
                if self.board[row + move_amount][col - 1][0] == enemy_color:
                    moves.append(Move((row, col), (row + move_amount, col - 1), self.board))
                if (row + move_amount, col - 1) == self.en_passant_possible:
                    moves.append(Move((row, col), (row + move_amount, col - 1), self.board, is_enpassant_move=True))
        if col + 1 <= 7:  # Capture à droite
            if not piece_pinned or pin_direction == (move_amount, +1):
                if self.board[row + move_amount][col + 1][0] == enemy_color:
                    moves.append(Move((row, col), (row + move_amount, col + 1), self.board))
                if (row + move_amount, col + 1) == self.en_passant_possible:
                    moves.append(Move((row, col), (row + move_amount, col + 1), self.board, is_enpassant_move=True))



    def getRookMoves(self, r, c, moves):
        """
            Obtient tous les mouvements possibles pour une pièce de tour donnée
        """
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                if self.board[r][c][1] != 'Q':
                    self.pins.remove(self.pins[i])
                break

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1)) # Haut, Gauche, Bas, Droite
        enemyColor = "b" if self.white_to_move else "w"
        for d in directions:
            for i in range(1, 8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                        else:
                            if endPiece[0] == enemyColor:
                                moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                else:
                    break



    def getKnightMoves(self, r, c, moves):
        """
            Obtient tous les mouvements possibles pour une pièce de cavalier donnée
        """
        piecePinned = False
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                self.pins.remove(self.pins[i])
                break

        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        allyColor = "w" if self.white_to_move else "b"
        for i in range(8):
            endRow = r + knightMoves[i][0]
            endCol = c + knightMoves[i][1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if not piecePinned:
                    if endPiece[0] != allyColor:
                        moves.append(Move((r, c), (endRow, endCol), self.board))


    def getBishopMoves(self, r, c, moves):
        """
            Obtient tous les mouvements possibles pour une pièce de fou donnée
        """
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1)) # Haut-Gauche, Haut-Droite, Bas-Gauche, Bas-Droite
        enemyColor = "b" if self.white_to_move else "w"
        for d in directions:
            for i in range(1, 8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                        else:
                            if endPiece[0] == enemyColor:
                                moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                else:
                    break


    def getQueenMoves(self, r, c, moves):
        """
            Obtient tous les mouvements possibles pour une pièce de reine donnée
        """
        self.getRookMoves(r, c, moves)
        self.getBishopMoves(r, c, moves)


    def getKingMoves(self, r, c, moves):
        """
            Obtient tous les mouvements possibles pour une pièce de roi donnée
        """
        rowMoves = (-1, -1, -1, 0, 0, 1, 1, 1)
        colMoves = (-1, 0, 1, -1, 1, -1, 0, 1)
        allyColor = "w" if self.white_to_move else "b"
        for i in range(8):
            endRow = r + rowMoves[i]
            endCol = c + colMoves[i]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor: # Case vide ou pièce ennemie
                    # Place le roi sur la case vide ou capture la pièce ennemie
                    if allyColor == "w":
                        self.white_king_location = (endRow, endCol)
                    else:
                        self.black_king_location = (endRow, endCol)
                    inCheck, pins, checks = self.checkForPinsAndChecks()
                    if not inCheck:
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                    if allyColor == "w":
                        self.white_king_location = (r, c)
                    else:
                        self.black_king_location = (r, c)

    def getCastleMoves(self, row, col, moves):
        '''
        Génère tous les mouvements de roque pour le roi à la position (row, col) et les ajoute à la liste de mouvements
        '''
        if self.squareUnderAttack(row, col):
            return  # Ne peut pas roquer si le roi est en échec
        if (self.white_to_move and self.current_castling_rights.wks) or (not self.white_to_move and self.current_castling_rights.bks):
            self.getKingsideCastleMoves(row, col, moves)
        if (self.white_to_move and self.current_castling_rights.wqs) or (not self.white_to_move and self.current_castling_rights.bqs):
            self.getQuennsideCastleMoves(row, col, moves)

    def getKingsideCastleMoves(self, row, col, moves):
        if self.board[row][col + 1] == '--' and self.board[row][col + 2] == '--':
            if not self.squareUnderAttack(row, col + 1) and not self.squareUnderAttack(row, col + 2):
                moves.append(Move((row, col), (row, col + 2), self.board, is_castle_move=True))

    def getQuennsideCastleMoves(self, row, col, moves):
        if self.board[row][col - 1] == '--' and self.board[row][col - 2] == '--' and self.board[row][col - 3] == '--':
            if not self.squareUnderAttack(row, col - 1) and not self.squareUnderAttack(row, col - 2):
                moves.append(Move((row, col), (row, col - 2), self.board, is_castle_move=True))

    """
    Renvoie si le joueur actuel est en échec, les broches et les échecs
    """
    def checkForPinsAndChecks(self):
        pins = [] # Les pièces qui ne peuvent pas bouger car elles protègent le roi
        checks = [] # Les pièces qui mettent le roi en échec
        inCheck = False
        if self.white_to_move:
            enemyColor = "b"
            allyColor = "w"
            kingRow = self.white_king_location[0]
            kingCol = self.white_king_location[1]
        else:
            enemyColor = "w"
            allyColor = "b"
            kingRow = self.black_king_location[0]
            kingCol = self.black_king_location[1]
        # Vérifie les mouvements des pièces ennemies
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            d = directions[j]
            possiblePin = ()
            for i in range(1, 8):
                endRow = kingRow + d[0] * i
                endCol = kingCol + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] == allyColor and endPiece[1] != 'K':
                        if possiblePin == ():
                            possiblePin = (endRow, endCol, d[0], d[1])
                        else:
                            break
                    elif endPiece[0] == enemyColor:
                        type = endPiece[1]
                        # 5 possibilités pour la pièce qui met en échec
                        # 1. Orthogonale au roi et peut être bloquée par une tour
                        # 2. Diagonale au roi et peut être bloquée par un fou
                        # 3. 1 case de distance du roi, peut être bloquée par un pion
                        # 4. Toutes les directions, peut être bloquée par une reine

                        if (0 <= j <= 3 and type == 'R') or (4 <= j <= 7 and type == 'B') or (i == 1 and type == 'p' and ((enemyColor == 'w' and 6 <= j <= 7) or (enemyColor == 'b' and 4 <= j <= 5))) or (type == 'Q') or (i == 1 and type == 'K'):
                            if possiblePin == (): # Aucune pièce entre la pièce qui met en échec et le roi
                                inCheck = True
                                checks.append((endRow, endCol, d[0], d[1]))
                                break
                            else: # Il y a une pièce entre la pièce qui met en échec et le roi
                                pins.append(possiblePin)
                                break
                        else:
                            break # La pièce ennemie ne peut pas mettre en échec le roi
                else:
                    break # Hors du tableau
        # Vérifie les mouvements des cavaliers ennemis
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        for m in knightMoves:
            endRow = kingRow + m[0]
            endCol = kingCol + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] == enemyColor and endPiece[1] == 'N': # Le roi est attaqué par un cavalier
                    inCheck = True
                    checks.append((endRow, endCol, m[0], m[1]))
        return inCheck, pins, checks


class CastleRights():
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Move():
    # Maps keys to values
    # key : value
    ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4,
                   "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}
    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3,
                   "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(self, startSq, endSq, board, is_enpassant_move=False, is_castle_move=False):
        self.start_row = startSq[0]
        self.start_col = startSq[1]
        self.end_row = endSq[0]
        self.end_col = endSq[1]
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]
        self.moveID = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col
        # Promotion du pion
        self.is_pawn_promotion = (self.piece_moved == 'wp' and self.end_row == 0) or (self.piece_moved == 'bp' and self.end_row == 7)
        # En passant
        self.is_enpassant_move = is_enpassant_move
        if self.is_enpassant_move:
            self.piece_captured = 'wp' if self.piece_moved == 'bp' else 'bp'
        # Roque
        self.is_castle_move = is_castle_move

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def getRankFile(self, r, c):
        return self.colsToFiles[c] + self.rowsToRanks[r]

    def getChessNotation(self):
        output_string = ""
        if self.is_pawn_promotion:
            output_string += self.getRankFile(self.end_row, self.end_col) + "Q"
        if self.is_castle_move:
            if self.end_col == 1:
                output_string += "0-0-0"
            else:
                output_string += "0-0"
        if self.is_enpassant_move:
            output_string += self.getRankFile(self.start_row, self.start_col)[0] + "x" + self.getRankFile(self.end_row, self.end_col) + " e.p."
        if self.piece_captured != "--":
            if self.piece_moved[1] == "p":
                output_string += self.getRankFile(self.start_row, self.start_col)[0] + "x" + self.getRankFile(self.end_row, self.end_col)
            else:
                output_string += self.piece_moved[1] + "x" + self.getRankFile(self.end_row, self.end_col)
        else:
            if self.piece_moved[1] == "p":
                output_string += self.getRankFile(self.end_row, self.end_col)
            else:
                output_string += self.piece_moved[1] + self.getRankFile(self.end_row, self.end_col)

        return output_string
