import pygame
from pygame import mixer
import math
import copy
import clipboard as cb
import random
import os

class Pieces: 
    # when true pawnBeingUpgraded = [colour, pawn coord]
    pawnBeingUpgraded = None
    enPassant = None
    checkmate = False
    staleMate = False
    halfMoves = 0
    numberOfMoves = 0
    previousMove = None

    # castlingControl = [w kingSide, w queenSide, b kingSide, b queenSide]
    castlingControl = [False, False, False, False]
    # if true check = [which king(either white or black), coords of king, coords of attacking pieces...]
    check = None

    pieceImages = None
    pieceSounds = []

    def __init__(self, coord, type, colour, image) -> None:
        self.coord = coord
        self.pos = (self.coord[1]*75-1, self.coord[0]*75)
        self.type = type
        self.image = image
        self.colour = colour

        if self.type == 'pawn' and (self.colour == 'white' and self.coord[0] == 6 or self.colour == 'black' and self.coord[0] == 1):
            self.firstMove = True
        elif self.type == 'pawn':
            self.firstMove = False
        elif self.type == 'rook':
            if Pieces.castlingControl[0] and self.coord == (7, 7) or Pieces.castlingControl[1] and self.coord == (7, 0) or Pieces.castlingControl[2] and self.coord == (0, 7) or Pieces.castlingControl[3] and self.coord == (0, 0):
                self.firstMove = True
            else:
                self.firstMove = False
        self.selected = False
        # pinned = [king position, position of pieces...]
        self.pinned = None

        self.possibleMoves = []
        self.AddPieceDirections()

        self.dragged = False
        self.rect = pygame.Rect(self.pos[0], self.pos[1], 75, 75)

    def AddPieceDirections(self):
        numOfDirections = {
            'pawn': 3,
            'bishop': 4,
            'rook': 4,
            'queen': 8,
        }
        if self.type not in ('knight', 'king'):
            for turn in range(numOfDirections[self.type]):
                self.possibleMoves.append([])

    def DetectPieceSelection(mousePos):
        for x in range(8):
            for y in range(8):
                if Board.storage[x][y] is not None and Board.storage[x][y].rect.collidepoint(Board.FlipCoord(mousePos)):
                    return (x, y)
        return None

    def Update(self, replacePos=False):
        if not replacePos:
            self.pos = (self.coord[1]*75-1, self.coord[0]*75)
        self.rect = pygame.Rect(self.pos[0], self.pos[1], 75, 75)

    def MoveFinder(self, _coord):
        moves = self.possibleMoves.copy()
        if self.type in ('pawn', 'bishop', 'rook', 'queen'):
            for directionNum in range(len(moves)):
                for positionNum in range(len(moves[directionNum])):
                    if moves[directionNum][positionNum][1] == _coord and moves[directionNum][positionNum][0] != 'friendly' and moves[directionNum][positionNum][0] != 'empty':
                        return moves[directionNum][positionNum]
        else:
            for positionNum in range(len(moves)):
                if moves[positionNum][1] == _coord and moves[positionNum][0] != 'friendly':
                    return moves[positionNum]
        return None

    def Move(self):
        def MakeMove(castleNum=None, enpassant=None):
            # Uses the move selected  and the conditions it is under to carry out the move 
            # whether that is moveing the king and then the rook for a castle or 
            # moving a pawn via enpassant and emptying the position of the pawn taken 
            if Board.playerTurn == 'black':
                Pieces.numberOfMoves += 1
            castleFixer = {  # change name
                    (7, 7): 0,
                    (7, 0): 1,
                    (0, 7): 2,
                    (0, 0): 3
                }
                
            if castleFixer.get(moveFound[1], None) is not None:
                Pieces.castlingControl[castleFixer[moveFound[1]]] = False
                self.firstMove = False

            pieceTaken = False
            oldCoord = self.coord
            Pieces.previousMove = [oldCoord, moveFound[1]]
            if castleNum is None and enpassant is None:
                self.coord = moveFound[1]
                self.Update()
                pieceBeingTaken = Board.storage[moveFound[1][0]][moveFound[1][1]]
                if pieceBeingTaken is None:
                    Board.soundQueue.append(0)
                    if self.type == 'pawn':
                        Pieces.halfMoves = 0
                    else:
                        Pieces.halfMoves += 1
                else:
                    Board.soundQueue.append(1)
                    pieceTaken = True
                    Pieces.halfMoves = 0
                Board.storage[moveFound[1][0]][moveFound[1][1]
                                                ] = Board.storage[oldCoord[0]][oldCoord[1]]
                Board.storage[oldCoord[0]][oldCoord[1]] = None
            elif castleNum is not None:
                Pieces.halfMoves += 1
                Pieces.previousMove[1] = (oldCoord[0], oldCoord[1] + castleNum)
                self.coord = (oldCoord[0], oldCoord[1] + castleNum)
                self.Update()
                Board.storage[self.coord[0]][self.coord[1]
                                              ] = Board.storage[oldCoord[0]][oldCoord[1]]
                Board.storage[oldCoord[0]][oldCoord[1]] = None
                Board.storage[oldCoord[0]][7 if castleNum == 2 else 0].coord = (
                    self.coord[0], self.coord[1] - (castleNum//2))
                Board.storage[oldCoord[0]
                               ][7 if castleNum == 2 else 0].Update()
                Board.storage[self.coord[0]][self.coord[1] - (
                    castleNum//2)] = Board.storage[oldCoord[0]][7 if castleNum == 2 else 0]
                Board.storage[oldCoord[0]][7 if castleNum == 2 else 0] = None
                SideScreen.AddMove(Pieces.previousMove[1], self.type, self.colour, None, False, 1 if cNum == 2 else 2)
                Board.SetBoard('', resetting=True)
                return
            elif enpassant:
                Pieces.halfMoves = 0
                self.coord = moveFound[1]
                self.Update()
                Board.soundQueue.append(1)
                pieceTaken = True
                Board.storage[moveFound[1][0]][moveFound[1][1]
                                                ] = Board.storage[oldCoord[0]][oldCoord[1]]
                Board.storage[oldCoord[0]][oldCoord[1]] = None
                Board.storage[oldCoord[0]][enpassant[1]] = None
            SideScreen.AddMove(Pieces.previousMove[1], self.type, self.colour, Pieces.previousMove[0] if self.type == 'pawn' else None, pieceTaken)
            Board.SetBoard('', resetting=True)


        if SideScreen.currentBoardPos != SideScreen.maxCurrentBoardPos:
            return False

        playerTurnReverser = {
            'white': 'black',
            'black': 'white'
        }

        # the coordinates for the board where the mouse is pressed/released
        # finds the move for the piece that is being moved
        # if not present then this function will return and the move cancelled
        # if found then other checks are done to determine the event that is occuring either a simple move or a castle for some examples
        # then that move is made

        self.selected = False
        coOrds = Board.GetCo_Ords()
        # movefound = [positionType (None, 'enemy', 'forward1/2', 'castle'), coord, how to access from self.possibleMoves]
        moveFound = self.MoveFinder(coOrds)
        if self.colour == Board.playerTurn and moveFound is not None:
            if self.type == 'pawn':
                self.firstMove = False
                if moveFound[0] == 'forward2':
                    Pieces.enPassant = self.EnpassantCheck((moveFound[1][0] + (-1 if self.colour == 'black' else 1), moveFound[1][1]))
                    MakeMove()
                    Board.playerTurn = playerTurnReverser[Board.playerTurn]
                    return True
                else:
                    if moveFound[0] == 'enpassant':
                        MakeMove(enpassant=Pieces.enPassant)
                        Board.playerTurn = playerTurnReverser[Board.playerTurn]
                        Pieces.enPassant = None
                        return True
                    Pieces.enPassant = None

            elif self.type == 'king':
                cNum = None
                if moveFound[0] == 'castleKingSide':
                    Board.soundQueue.append(2)
                    cNum = 2
                elif moveFound[0] == 'castleQueenSide':
                    Board.soundQueue.append(2)
                    cNum = -2
                    
                elif moveFound[0] == 'kingBarrier':
                    return False
                if self.colour == 'white':
                    Pieces.castlingControl = [
                        False, False, Pieces.castlingControl[2], Pieces.castlingControl[3]]
                else:
                    Pieces.castlingControl = [
                        Pieces.castlingControl[0], Pieces.castlingControl[1], False, False]
                MakeMove(castleNum=cNum)
                Board.playerTurn = playerTurnReverser[Board.playerTurn]
                Board.soundQueue.append(0)
                
                Pieces.enPassant = None
                return True

            elif self.type == 'rook' and self.firstMove:
                castleFixer = {  # change name
                    (7, 7): 0,
                    (7, 0): 1,
                    (0, 7): 2,
                    (0, 0): 3
                }
                try:
                    Pieces.castlingControl[castleFixer[self.coord]] = False
                except:
                    print(self.type, self.colour, self.coord)
                self.firstMove = False
            MakeMove()
            Board.playerTurn = playerTurnReverser[Board.playerTurn]
            Pieces.enPassant = None
            return True
        return False


    def CalculateMoves(simulation=False):
        def AnyMovesPossible():
            # searches through all of the pieces t-for the colour whos current move it is and checks if any have any valid moves
            # if not then the game is either a stalemate or checkmate
            for x in range(8):
                for y in range(8):
                    if Board.storage[x][y] is not None and Board.storage[x][y].colour == Board.playerTurn:
                        if Board.storage[x][y].type in ('pawn', 'bishop', 'rook', 'queen'):
                            for directionNum in range(len(Board.storage[x][y].possibleMoves)):
                                for positionNum in range(len(Board.storage[x][y].possibleMoves[directionNum])):
                                    if Board.storage[x][y].type == 'pawn' and positionNum != 1 and Board.storage[x][y].possibleMoves[directionNum][positionNum][0] in ('friendly', 'empty'):
                                        continue
                                    if Board.storage[x][y].possibleMoves[directionNum][positionNum][0] not in ('friendly', 'empty'):
                                        return True
                        else:
                            for move in Board.storage[x][y].possibleMoves:
                                if (Board.storage[x][y].type == 'knight' or move[0] != 'kingBarrier') and move[0] != 'friendly':
                                    return True
            return False

        def DrawnPosition():
            # is a check for most possible drawn positions
            # which are positions where a checkmate is impossible
            _piecesLength = len(_pieces)
            if _piecesLength <= 4:
                if _piecesLength > 2:
                    if _piecesLength == 3 and (_pieces.count('knightwhite') == 1 or _pieces.count('knightblack') == 1 or _pieces.count('bishopwhite') == 1 or _pieces.count('bishopblack') == 1):
                        return True
                    elif _piecesLength == 4 and _pieces.count('bishopwhite') == 1 and _pieces.count('bishopblack') == 1:# bishop on white square vs bishop on black square is not a draw but oh well
                        return True
                else:
                    return True
            return False

            # king vs king
            # king vs king and knight
            # king vs king and bishop
            # king and light square bishop vs king and dark square bishop

        
        _pieces = []
        for x in range(8):
            for y in range(8):
                if Board.storage[x][y] is not None:
                    Board.storage[x][y].pinned = None
                    _pieces.append(Board.storage[x][y].type + Board.storage[x][y].colour)
                    

        # performs first set of checks for moves all pieces can make including illegal ones
        Pieces.check = None
        for x in range(8):
            for y in range(8):
                if Board.storage[x][y] is not None:
                    Board.storage[x][y].PossibleMoves()

        if Pieces.check is not None:
            Board.soundQueue.append(3)
            # Pieces.pieceSounds[3].play() when done plays piece moving and check sound, sounds wierd

        # goes through each piece and removes illegal moves due to checks/ being pinned
        for x in range(8):
            for y in range(8):
                if Board.storage[x][y] is not None:
                    Board.storage[x][y].RemoveIllegalMoves()

        if Window.currentMode == 'tutorial':
            return
                        
        # checks if the are any legal moves for any piece to do if not it is checkmate
        if not AnyMovesPossible():
            Board.soundQueue.append(5)
            if Pieces.check is not None:
                Pieces.checkmate = True
                Window.currentEvent = 'checkmate' + ('black' if Board.playerTurn == 'white' else 'white')
                Window.changingFen = Board.BoardToFen()
            else:
                Pieces.staleMate = True
                Window.currentEvent = 'stalemate'
                Window.changingFen = Board.BoardToFen()
        elif Pieces.halfMoves >= 50:
            Board.soundQueue.append(5)
            Pieces.staleMate = True
            Window.currentEvent = 'stalemate'
            Window.changingFen = Board.BoardToFen()
        elif DrawnPosition():
            Window.currentEvent = 'stalemate'
            Board.soundQueue.append(5)
            Pieces.staleMate = True
            Window.changingFen = Board.BoardToFen()

        if Window.currentEvent != 'game' and not simulation:
            SideScreen.Resetting()

    def KingMoveIsThere(self, _coord, sameLine=None):
        # sameLine = [x or y direction, x/y value]
        for turn in range(len(self.possibleMoves)):
            if sameLine is None:
                if self.possibleMoves[turn][1] == _coord:
                    return turn
            elif self.possibleMoves[turn][1] == sameLine[1]:
                print(self.possibleMoves[turn][1], sameLine[1])
                return turn
        return None

    def TrigCalc(startCoord, endCoord, extra= 0, returnDirection = False):
        # starts the starting position and either goes through all the coordinates
        # either a long the straight or diagonal path
        if extra != 0:
            extra += (extra/abs(extra))
        xDif = startCoord[0] - endCoord[0]
        yDif = startCoord[1] - endCoord[1]
        if xDif != 0:
            xDif += (xDif/abs(xDif)) * extra
        if yDif != 0:
            yDif += (yDif/abs(yDif)) * extra

        if xDif != 0 and yDif != 0:
            if xDif/yDif > 0:
                direction = 'negative'
            else:
                direction = 'positive'
        else:
            direction = 'straight'

        xChange = 0
        yChange = 0
        possibleCoords = []
        while (xDif > xChange or xDif < xChange) or (yDif > yChange or yDif < yChange):
            possibleCoords.append(
                (endCoord[0] + xChange, endCoord[1] + yChange))
            xChange += 1 if xChange < xDif else (-1 if xChange >
                                                    xDif else 0)
            yChange += 1 if yChange < yDif else (-1 if yChange >
                                                    yDif else 0)
        if not returnDirection:
            return possibleCoords
        else:
            return possibleCoords, direction 

    def RemoveIllegalMoves(self):
        # goes through all the pieces on the board after all legal and illegal moves have been calculated
        # and checks for cases where doing that move would result in its colour king being in check
        # it then removes them and deals with any other situations required
        def MultipleChecks(_check):
            # finds all the directions check are coming from and compares to find moves that don't interefere with either

            illegalPositions = []
            for turn in range(2, len(_check)):
                if Board.storage[Pieces.check[turn][0]][Pieces.check[turn][1]].type not in ('knight', 'pawn'):
                    _moves = Pieces.TrigCalc(_check[1], _check[turn], extra=1)
                    _moves.pop(0)
                    for item in _moves:
                        if item not in illegalPositions:
                            illegalPositions.append(item)
                
            return illegalPositions

        if self.type == 'king': #r1bqk2r/pppp1ppp/4pn2/8/1b2P3/1BN2Q2/PPPP1PPP/R1B2RK1 b kq - 2 6
            if Pieces.check is not None and self.colour == Pieces.check[0]:
                illegals = MultipleChecks(Pieces.check) #Pieces.TrigCalc(Pieces.check[1], Pieces.check[2], 1)
                moves = self.possibleMoves.copy()
                for positionNum in range(len(moves)):
                    if moves[positionNum][1] in illegals:
                        self.possibleMoves.remove(moves[positionNum])
            moves = self.possibleMoves.copy()
            deletionNum = 0
            for positionNum in range(len(moves)):
                if moves[positionNum][0] == None or moves[positionNum][0] == 'enemy':
                    if self.possibleMoves[positionNum - deletionNum][0] != 'kingBarrier' and self.MarkedSquare(moves[positionNum][1]):
                        self.possibleMoves.remove(moves[positionNum])
                        deletionNum += 1
                elif moves[positionNum][0] == 'castleKingSide':
                    if self.MarkedSquare((self.coord[0], self.coord[1]+1)) or self.MarkedSquare((self.coord[0], self.coord[1]+2)):
                        self.possibleMoves.remove(moves[positionNum])
                        deletionNum += 1
                    elif Pieces.check is not None and Pieces.check[0] == self.colour:
                        self.possibleMoves.remove(moves[positionNum])
                        deletionNum += 1
                elif moves[positionNum][0] == 'castleQueenSide':
                    if self.MarkedSquare((self.coord[0], self.coord[1]-1)) or self.MarkedSquare((self.coord[0], self.coord[1]-2)):
                        self.possibleMoves.remove(moves[positionNum])
                        deletionNum += 1
                    elif Pieces.check is not None and Pieces.check[0] == self.colour:
                        self.possibleMoves.remove(moves[positionNum])
                        deletionNum += 1
        else:
            # pinned = [king position, position of pieces...]
            if self.pinned is not None:
                legalPositions = Pieces.TrigCalc(self.pinned[0], self.pinned[1])
                moves = copy.deepcopy(self.possibleMoves)
                if self.type in ('pawn', 'bishop', 'rook', 'queen'):
                    for directionNum in range(len(moves)):
                        for positionNum in range(len(moves[directionNum])):
                            if moves[directionNum][positionNum][1] not in legalPositions:
                                self.possibleMoves[directionNum].remove(
                                    moves[directionNum][positionNum])
                else:
                    for positionNum in range(len(moves)):
                        if moves[positionNum][1] not in legalPositions:
                            self.possibleMoves.remove(moves[positionNum])

            # check = [colour of king, coords of king, coords of attacking pieces...]
            if Pieces.check is not None and self.colour == Pieces.check[0]:
                # blocking/ taking the attacker
                if len(Pieces.check) == 3:
                    legalPositions = Pieces.TrigCalc(Pieces.check[1], Pieces.check[2])
                    if Board.storage[Pieces.check[2][0]][Pieces.check[2][1]].type == 'knight':
                        legalPositions = [Pieces.check[2]]
                else:
                    legalPositions = []

                moves = copy.deepcopy(self.possibleMoves)
                if self.type in ('pawn', 'bishop', 'rook', 'queen'):
                    for directionNum in range(len(moves)):
                        for positionNum in range(len(moves[directionNum])):
                            if moves[directionNum][positionNum][1] not in legalPositions:
                                self.possibleMoves[directionNum].remove(
                                    moves[directionNum][positionNum])
                elif self.type == 'knight':
                    for positionNum in range(len(moves)):
                        if moves[positionNum][1] not in legalPositions:
                            self.possibleMoves.remove(moves[positionNum])

    def PossibleMoves(self):
        # this method is called for every piece and every move it could do
        # not considering wether it is illegal or not is calculated and added
        def CheckForCheck(kCoordX, kCoordY):
            if Board.storage[kCoordX][kCoordY].type == 'king':
                Pieces.enPassant = None
                if Pieces.check is not None:
                    Pieces.check.append(self.coord)
                else:
                    Pieces.check = [Board.storage[kCoordX][kCoordY].colour,
                                    (kCoordX, kCoordY), self.coord]

        def MovementLogic(xChange, yChange, blocked=None, directionNum=None, QueenAddition=0):
            newXCoord = self.coord[0]+xChange
            newYCoord = self.coord[1]+yChange
            if blocked is not None:
                if Board.storage[newXCoord][newYCoord] is None:
                    if not blocked[directionNum]:
                        self.possibleMoves[directionNum+QueenAddition].append(
                            [None, (newXCoord, newYCoord)])
                else:
                    if Board.storage[newXCoord][newYCoord].colour != self.colour:
                        if not blocked[directionNum]:
                            self.possibleMoves[directionNum+QueenAddition].append(
                                ['enemy', (newXCoord, newYCoord)])
                            CheckForCheck(newXCoord, newYCoord)
                        if Board.storage[newXCoord][newYCoord].type == 'king' and blocked[directionNum] == 1 and self.possibleMoves[directionNum + QueenAddition][-1][0] != 'friendly':

                            _coord = self.possibleMoves[directionNum +
                                                        QueenAddition][-1][1]
                            Board.storage[_coord[0]][_coord[1]].pinned = [
                                (newXCoord, newYCoord), self.coord]
                    elif blocked[directionNum] == 0:
                        self.possibleMoves[directionNum+QueenAddition].append(
                            ['friendly', (newXCoord, newYCoord)])
                    blocked[directionNum] += 1
            else:
                if Board.storage[newXCoord][newYCoord] is None:
                    self.possibleMoves.append([None, (newXCoord, newYCoord)])
                elif Board.storage[newXCoord][newYCoord].colour != self.colour:
                    self.possibleMoves.append(
                        ['enemy', (newXCoord, newYCoord)])
                    CheckForCheck(newXCoord, newYCoord)
                else:
                    self.possibleMoves.append(
                        ['friendly', (newXCoord, newYCoord)])

        def PawnMoves(thing):
            # left position
            if (self.colour == 'white' and self.coord[0] == 0 or self.colour == 'black' and self.coord[0] == 7):
                Pieces.pawnBeingUpgraded = [
                    self.colour, self.coord]
            else:
                if self.coord[1]-1 >= 0:
                    if Board.storage[self.coord[0]+thing][self.coord[1]-1] is not None:
                        if Board.storage[self.coord[0]+thing][self.coord[1]-1].colour != self.colour:
                            self.possibleMoves[0].append(['enemy',
                                                        (self.coord[0]+thing, self.coord[1]-1)])
                            CheckForCheck(
                                self.coord[0]+thing, self.coord[1]-1)
                        else:
                            self.possibleMoves[0].append(['friendly',
                                                        (self.coord[0]+thing, self.coord[1]-1)])
                    elif Pieces.enPassant is not None and Pieces.enPassant == (self.coord[0]+thing, self.coord[1]-1):
                        if (Pieces.enPassant[0] == 5 and self.colour == 'black') or (Pieces.enPassant[0] == 2 and self.colour == 'white'):
                            self.possibleMoves[0].append(['enpassant',
                                                            (self.coord[0]+thing, self.coord[1]-1)])
                    else:
                        self.possibleMoves[0].append(['empty',
                                                    (self.coord[0]+thing, self.coord[1]-1)])
                # right position
                if self.coord[1]+1 <= 7:
                    if Board.storage[self.coord[0]+thing][self.coord[1]+1] is not None:
                        if Board.storage[self.coord[0]+thing][self.coord[1]+1].colour != self.colour:
                            self.possibleMoves[2].append(['enemy',
                                                        (self.coord[0]+thing, self.coord[1]+1)])
                            CheckForCheck(
                                self.coord[0]+thing, self.coord[1]+1)
                        else:
                            self.possibleMoves[0].append(['friendly',
                                                        (self.coord[0]+thing, self.coord[1]+1)])
                    elif Pieces.enPassant is not None and Pieces.enPassant == (self.coord[0]+thing, self.coord[1]+1):
                        if (Pieces.enPassant[0] == 5 and self.colour == 'black') or (Pieces.enPassant[0] == 2 and self.colour == 'white'):
                            self.possibleMoves[0].append(
                                ['enpassant', (self.coord[0]+thing, self.coord[1]+1)])
                    else:
                        self.possibleMoves[0].append(['empty',
                                                    (self.coord[0]+thing, self.coord[1]+1)])

                # in front positions
                if 7 >= self.coord[0]+thing >= 0:
                    # first
                    if Board.storage[self.coord[0]+thing][self.coord[1]] is None:
                        self.possibleMoves[1].append(
                            ['forward1', (self.coord[0]+thing, self.coord[1])])    
                        # second
                        if self.firstMove and Board.storage[self.coord[0]+(thing*2)][self.coord[1]] is None:
                            self.possibleMoves[1].append(
                                ['forward2', (self.coord[0]+(thing*2), self.coord[1])])

        def BishopMoves():
            blocked = [0, 0, 0, 0]
            for turn in range(1, 8):
                # Towards top left
                if self.coord[0]-turn >= 0 and self.coord[1]-turn >= 0:
                    MovementLogic(-turn, -turn, blocked, 0)

                # Towards top right
                if self.coord[0]-turn >= 0 and self.coord[1]+turn <= 7:
                    MovementLogic(-turn, turn, blocked, 1)

                # Towards bottom left
                if self.coord[0]+turn <= 7 and self.coord[1]-turn >= 0:
                    MovementLogic(turn, -turn, blocked, 2)
                # Towards bottom right
                if self.coord[0]+turn <= 7 and self.coord[1]+turn <= 7:
                    MovementLogic(turn, turn, blocked, 3)

        def KnightMoves():
            # left 2 down 1
            if self.coord[0]+1 <= 7 and self.coord[1]-2 >= 0:
                MovementLogic(1, -2)
            # left 2 up 1 <= 7
            if self.coord[0]-1 >= 0 and self.coord[1]-2 >= 0:
                MovementLogic(-1, -2)

            # left 1 up 2
            if self.coord[0]-2 >= 0 and self.coord[1]-1 >= 0:
                MovementLogic(-2, -1)
            # right 1 up 2
            if self.coord[0]-2 >= 0 and self.coord[1]+1 <= 7:
                MovementLogic(-2, 1)

            # right 2 up 1
            if self.coord[0]-1 >= 0 and self.coord[1]+2 <= 7:
                MovementLogic(-1, 2)
            # right 2 down 1
            if self.coord[0]+1 <= 7 and self.coord[1]+2 <= 7:
                MovementLogic(1, 2)

            # right 1 down 2
            if self.coord[0]+2 <= 7 and self.coord[1]+1 <= 7:
                MovementLogic(2, 1)
            # left 1 down 2
            if self.coord[0]+2 <= 7 and self.coord[1]-1 >= 0:
                MovementLogic(2, -1)

        def RookMoves(isQueen=False):
            blocked = [0, 0, 0, 0]
            for turn in range(1, 8):
                # Towards top
                if self.coord[0]-turn >= 0:
                    MovementLogic(-turn, 0, blocked, 0, 4 if isQueen else 0)

                # Towards bottom
                if self.coord[0]+turn <= 7:
                    MovementLogic(turn, 0, blocked, 1, 4 if isQueen else 0)

                # Towards left
                if self.coord[1]-turn >= 0:
                    MovementLogic(0, -turn, blocked, 2, 4 if isQueen else 0)

                # Towards right
                if self.coord[1]+turn <= 7:
                    MovementLogic(0, turn, blocked, 3, 4 if isQueen else 0)

        def KingMovement():
            for x in range(-1, 2):
                for y in range(-1, 2):
                    if 7 >= self.coord[0]+x >= 0 and 7 >= self.coord[1]+y >= 0:
                        if Board.storage[self.coord[0]+x][self.coord[1]+y] is None:
                            self.possibleMoves.append(
                                [None, (self.coord[0]+x, self.coord[1]+y)])
                            self.MarkedSquare((self.coord[0]+x, self.coord[1]+y), kingy=True)
                        elif Board.storage[self.coord[0]+x][self.coord[1]+y].colour != self.colour:
                            self.possibleMoves.append(
                                ['enemy', (self.coord[0]+x, self.coord[1]+y)])
                        elif Board.storage[self.coord[0]+x][self.coord[1]+y].type != self.type:
                            self.possibleMoves.append(
                                ['friendly', (self.coord[0]+x, self.coord[1]+y)])

            # Castling
            if Pieces.check is None:
                # King side
                if Pieces.castlingControl[0 if self.colour == 'white' else 2] == True:
                    if Board.storage[self.coord[0]][self.coord[1]+1] is None and Board.storage[self.coord[0]][self.coord[1]+2] is None:
                        self.possibleMoves.append(
                            ['castleKingSide', (self.coord[0], self.coord[1]+2)])

                # Queen side
                if Pieces.castlingControl[1 if self.colour == 'white' else 3] == True:
                    if Board.storage[self.coord[0]][self.coord[1]-1] is None and Board.storage[self.coord[0]][self.coord[1]-2] is None and Board.storage[self.coord[0]][self.coord[1]-3] is None:
                        self.possibleMoves.append(
                            ['castleQueenSide', (self.coord[0], self.coord[1]-2)])

        self.possibleMoves = []
        self.AddPieceDirections()
        if self.type == 'pawn':
            PawnMoves(-1 if self.colour == 'white' else 1)
        elif self.type == 'bishop':
            BishopMoves()
        elif self.type == 'knight':
            KnightMoves()
        elif self.type == 'rook':
            RookMoves()
        elif self.type == 'queen':
            # Queen Moves
            # both rook and bishop move calculators are called as queens can be treated as a combination of them
            BishopMoves()
            RookMoves(isQueen=True)
        else:
            KingMovement()


    def MarkedSquare(self, _coord, kingy=False):
        # goes through every move of the opposite colour to the piece passed through
        # checks if any proper moves include the coordinate passed in 
        # this is used to check if a place a king is trying to moved to is being attacked
        for x in range(8):
            for y in range(8):
                if Board.storage[x][y] is not None and Board.storage[x][y].colour != self.colour:
                    moves = Board.storage[x][y].possibleMoves.copy()
                    if kingy and Board.storage[x][y].type == 'king':
                        for positionNum in range(len(moves)): 
                            if moves[positionNum][1] == _coord:
                                Board.storage[x][y].possibleMoves[positionNum][0] = 'kingBarrier'
                                self.possibleMoves[-1][0] = 'kingBarrier'
                    else:
                        if Board.storage[x][y].type in ('pawn', 'bishop', 'rook', 'queen'):
                            for directionNum in range(len(moves)):
                                for positionNum in range(len(moves[directionNum])):
                                    if moves[directionNum][positionNum][1] == _coord:
                                        if Board.storage[x][y].type == 'pawn':
                                            if directionNum != 1:
                                                return True
                                        else:
                                            return True
                        else:
                            for positionNum in range(len(moves)):
                                if moves[positionNum][1] == _coord:
                                    return True
        return False

    def EnpassantConversion(input):
        letterToYCoord = {'a': 0, 'b': 1, 'c': 2,
                          'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
        yCoordToLetter = {0: 'a', 1: 'b', 2: 'c',
                          3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}
        reverseNumber = [8, 7, 6, 5, 4, 3, 2, 1]
        ifInputIsNone = {'-': None, None: '-'}
        try:
            return ifInputIsNone[input]
        except:
            try:
                return (reverseNumber.index(int(input[1])), letterToYCoord[input[0]])
            except:
                return str(yCoordToLetter[input[1]]) + str(reverseNumber[input[0]])

    def EnpassantCheck(self, enCoord):
        # check is an En passant could occur in the board position
        # it also accounts for if the pawn attacking is pinned

        x = enCoord[0] + (1 if self.colour == 'black' else -1)
        possibleYCoords = [(enCoord[1] -1 if enCoord[1]-1 >= 0 else None), (enCoord[1] +1 if enCoord[1]+1 <= 7 else None)]
        for y in possibleYCoords:
            if y is not None:
                item = Board.storage[x][y]
                if item is not None and item.type == 'pawn' and item.colour != self.colour:
                    if item.pinned is not None:
                        thing = Pieces.TrigCalc(item.pinned[1], item.pinned[0], returnDirection=True)
                        if item.pinned[0][1] == item.pinned[1][1]:
                            #print('vertical')
                            return None
                        elif item.pinned[0][0] == item.pinned[1][0]:
                            #print('enpassant pin')
                            return None
                        elif enCoord not in thing[0] and thing[1] == 'positive': 
                            if item.colour == 'white' and possibleYCoords.index(y) == 1:
                                #print('white, positive, right')
                                return None
                            elif item.colour == 'black' and possibleYCoords.index(y) == 0:
                                #print('black, positive, left')
                                return None
                            else:
                                #print('allowed')
                                return enCoord
                        elif enCoord not in thing[0] and thing[1] == 'negative':
                            if item.colour == 'white' and possibleYCoords.index(y) == 0:
                                #print('white, negative, left')
                                return None
                            elif item.colour == 'black' and possibleYCoords.index(y) == 1:
                                #print('black, negative, right')
                                return None
                            else:
                                #print('allowed')
                                return enCoord
                        else:
                            #print('allowed')
                            return enCoord
                    else:
                        return enCoord
        return None


class Board: 
    storage = [[None, None, None, None, None, None, None, None],
               [None, None, None, None, None, None, None, None],
               [None, None, None, None, None, None, None, None],
               [None, None, None, None, None, None, None, None],
               [None, None, None, None, None, None, None, None],
               [None, None, None, None, None, None, None, None],
               [None, None, None, None, None, None, None, None],
               [None, None, None, None, None, None, None, None]]
    
    pieceSelected = False
    pieceSelectedCoord = None
    pieceSelectedCoord2 = None
    arrowSelectedCoord = None
    arrowStorage = []
    newMoveMade = False
    beingDragged = False
    clickPosition = None

    boardFlipped = False
    boardFlippedStorage = None
    autoBoardFlip = False

    piecesTaken = [[], []]
    whiteName = 'White'
    blackName = 'Black'
    soundQueue = []
    startingMoveNum = 0

    playerTurn = 'white'
    playerColour = None

    def init():
        Board.startingMoveNum = Pieces.numberOfMoves

    def SetBoard(fen, resetting=False, resetFlip = True, resetMove=True):
        # resets most variables to do with the board and sideScreen 
        # converts the FEN passed in into a board position while also assigning necessary variables from the FEN
        Board.pieceSelected = False
        Board.pieceSelectedCoord = None
        Board.pieceSelectedCoord2 = None
        Board.arrowSelectedCoord = None
        Board.arrowStorage = []

        if resetMove:
            Board.newMoveMade = True
        

        if not resetting:
            Board.storage = [[None, None, None, None, None, None, None, None],
                [None, None, None, None, None, None, None, None],
                [None, None, None, None, None, None, None, None],
                [None, None, None, None, None, None, None, None],
                [None, None, None, None, None, None, None, None],
                [None, None, None, None, None, None, None, None],
                [None, None, None, None, None, None, None, None],
                [None, None, None, None, None, None, None, None]]
        
            # when true pawnBeingUpgraded = [colour, pawn coord]
            Pieces.pawnBeingUpgraded = None
            Pieces.enPassant = None
            Pieces.checkmate = False
            Pieces.staleMate = False
            Pieces.halfMoves = 0
            Pieces.numberOfMoves = 0
            Board.playerTurn = 'white'
            Pieces.previousMove = None
            Window.changingFen = fen
            # castlingControl = [w kingSide, w queenSide, b kingSide, b queenSide]
            Pieces.castlingControl = [False, False, False, False]
            # if true check = [which king(either white or black), coords of king, coords of attacking pieces...]
            Pieces.check = None
            if resetFlip and Window.currentMode == 'player':
                Board.boardFlipped = False

            letterToPiece = {
                'P': (1, 'white', 'pawn'),
                'B': (2, 'white', 'bishop'),
                'N': (3, 'white', 'knight'),
                'R': (4, 'white', 'rook'),
                'Q': (5, 'white', 'queen'),
                'K': (6, 'white', 'king'),
                'p': (7, 'black', 'pawn'),
                'b': (8, 'black', 'bishop'),
                'n': (9, 'black', 'knight'),
                'r': (10, 'black', 'rook'),
                'q': (11, 'black', 'queen'),
                'k': (12, 'black', 'king')
            }
            fenParts = fen.split(' ')

            castlingLogic = {'K': 0, 'Q': 1, 'k': 2, 'q': 3, '-': None}
            if castlingLogic[fenParts[2][0]] is not None:
                for letter in fenParts[2]:
                    Pieces.castlingControl[castlingLogic[letter]] = True

            turn = 0
            freeSpaces = 0
            for x in range(8):
                for y in range(8):
                    if freeSpaces == 0:
                        try:
                            freeSpaces = int(fenParts[0][turn])
                            Board.storage[x][y] = None
                            freeSpaces -= 1
                        except:
                            info = letterToPiece[fenParts[0][turn]]
                            Board.storage[x][y] = Pieces(
                                (x, y), info[2], info[1], Pieces.pieceImages[info[0]-1])
                        turn += 1
                    else:
                        Board.storage[x][y] = None
                        freeSpaces -= 1
                    if x != 7 and fenParts[0][turn] == '/':
                        turn += 1

            Board.playerTurn = 'white' if fenParts[1] == 'w' else 'black'

            Pieces.enPassant = Pieces.EnpassantConversion(fenParts[3])

            Pieces.halfMoves = int(fenParts[4])

            Pieces.numberOfMoves = int(fenParts[5])

    def DrawPawnUpgrade(selection=False):
        # calls the local subroutine for each that can be selected
        # and checks whether it has been selected
        def Thing(pieceType, order):
            Surface = pygame.Surface((75, 75), pygame.SRCALPHA)
            pygame.draw.rect(
                Surface, Window.colours[4], pygame.Rect(0, 0, 75, 75))
            x = Pieces.pawnBeingUpgraded[1][1]*75
            y = 300 + (300-(order*75))*direction + adjustment
            _mousePos = Board.FlipCoord(mousePos, offset=1)
            if x <= _mousePos[0] <= x + 75 and y <= _mousePos[1] <= y + 75:
                _width = 0
                if selection:
                    Board.SetBoard('', resetting=True)
                    Board.soundQueue.append(4)
                    Board.piecesTaken[0 if Pieces.pawnBeingUpgraded[0] == 'white' else 1].append(pieceTypeConversion[pieceType])
                    Board.storage[Pieces.pawnBeingUpgraded[1][0]][Pieces.pawnBeingUpgraded[1][1]] = Pieces(
                        Pieces.pawnBeingUpgraded[1], pieceTypeConversion[pieceType], Pieces.pawnBeingUpgraded[0], Pieces.pieceImages[pieceType+(3*direction)])
                    Pieces.pawnBeingUpgraded = None
                    return True
            else:
                _width = 16
            pygame.draw.circle(Surface, (30, 30, 30), (37.5, 37.5), 53, _width)
            Surface.set_alpha(200)
            screen.blit(Surface, Surface.get_rect(
                center=Board.FlipCoord((x+36.5, y+36.5), offset=-1)))
            screen.blit(Pieces.pieceImages[pieceType+(3*direction)],
                        Board.FlipCoord((x-2, y-1), offset=-77))
            return False

        if Pieces.pawnBeingUpgraded[0] == 'white':
            direction = -1
            adjustment = 0
        else:
            direction = 1
            adjustment = -75

        pieceTypeConversion = {
            7: 'queen',
            5: 'knight',
            6: 'rook',
            4: 'bishop'
        }

        if Thing(7, 0):
            return
        if Thing(5, 1):
            return
        if Thing(6, 2):
            return
        if Thing(4, 3):
            return

    def CheckIfDragged(justChecking=False):
        # checks the distance between the centre of the selected piece and the current mouse position
        # if outside of the radius determined 10 then it is being dragged
        # and if justChecking is set to true then it will return whether it is being dragged or not  
        if Board.pieceSelectedCoord is not None and Board.pieceSelectedCoord2 is None and SideScreen.currentBoardPos == SideScreen.maxCurrentBoardPos and mousePos != Board.clickPosition:
            mouseDistanceFromPiece = math.sqrt(
                ((Board.pieceSelectedCoord[1]*75) + 37.5 - mousePos[0])**2 + ((Board.pieceSelectedCoord[0]*75) + 37.5 - mousePos[1])**2)
            if mouseDistanceFromPiece > 10 and Board.storage[Board.pieceSelectedCoord[0]][Board.pieceSelectedCoord[1]] is not None and (Board.storage[Board.pieceSelectedCoord[0]][Board.pieceSelectedCoord[1]].colour == Board.playerTurn or Window.currentMode == 'boardeditor'):
                if not justChecking:
                    Board.beingDragged = True
                    screen.blit(Board.storage[Board.pieceSelectedCoord[0]][Board.pieceSelectedCoord[1]].image,
                                (mousePos[0] - 37.5, mousePos[1] - 37.5))
                    return
                else:
                    return True
        if justChecking:
            return False
        else:
            Board.beingDragged = False

    def GetCo_Ords(ignoreFlip = False):
        # converts mouse position to corosponding board coordinate
        _mousePos = Board.FlipCoord(mousePos) if not ignoreFlip else mousePos
        for x in range(0, 599, 75):
            for y in range(0, 599, 75):
                if x <= _mousePos[0] < x+75 and y <= _mousePos[1] < y+75:
                    return (y // 75, x // 75)
        return None

    def BoardToFen(swapColour = False):
        def CastlingCheck():
            _controls = [False, False, False, False]
            if Board.storage[7][4] is not None and Board.storage[7][4].type == 'king' and Board.storage[7][4].colour == 'white':
                if Board.storage[7][7] is not None and Board.storage[7][7].type == 'rook' and Board.storage[7][7].colour == 'white':
                    _controls[0] = True
                if Board.storage[7][0] is not None and Board.storage[7][0].type == 'rook' and Board.storage[7][0].colour == 'white':
                    _controls[1] = True
            if Board.storage[0][4] is not None and Board.storage[0][4].type == 'king' and Board.storage[0][4].colour == 'black':
                if Board.storage[0][7] is not None and Board.storage[0][7].type == 'rook' and Board.storage[0][7].colour == 'black':
                    _controls[2] = True
                if Board.storage[0][0] is not None and Board.storage[0][0].type == 'rook' and Board.storage[0][0].colour == 'black':
                    _controls[3] = True
            return _controls
        pieceToLetter = {
            ('white', 'pawn'): 'P',
            ('white', 'bishop'): 'B',
            ('white', 'knight'): 'N',
            ('white', 'rook'): 'R',
            ('white', 'queen'): 'Q',
            ('white', 'king'): 'K',
            ('black', 'pawn'): 'p',
            ('black', 'bishop'): 'b',
            ('black', 'knight'): 'n',
            ('black', 'rook'): 'r',
            ('black', 'queen'): 'q',
            ('black', 'king'): 'k'
        }
        fenNotation = ''
        freeSpaces = 0
        for x in range(8):
            for y in range(8):
                item = Board.storage[x][y]
                if item == None:
                    freeSpaces += 1
                else:
                    if freeSpaces != 0:
                        fenNotation += str(freeSpaces)
                        freeSpaces = 0
                    fenNotation += pieceToLetter[(item.colour, item.type)]
            if freeSpaces != 0:
                fenNotation += str(freeSpaces)
                freeSpaces = 0
            if x != 7:
                fenNotation += '/'

        if not swapColour:
            fenNotation += ' w ' if Board.playerTurn == 'white' else ' b '
        else:
            fenNotation += ' b ' if Board.playerTurn == 'white' else ' w '

        castlingLogic = ('K', 'Q', 'k', 'q')
        castlingControls = CastlingCheck()
        for turn in range(4):
            if Pieces.castlingControl[turn] and castlingControls[turn]:
                fenNotation += castlingLogic[turn]
        if fenNotation[-1] == ' ':
            fenNotation += '-'

        if Pieces.enPassant is None:
            fenNotation += ' -'
        else:
            fenNotation += ' ' + Pieces.EnpassantConversion(Pieces.enPassant)
        
        fenNotation += ' ' + str(Pieces.halfMoves) + ' ' + str(Pieces.numberOfMoves)

        
        return fenNotation

    def DisplayBoard():
        def DrawBoard(width):
            pygame.draw.rect(screen, Window.colours[0], (0, 0, 600, 600))
            for x in range(0, 675-width, width*2):
                for y in range(0, 675-width, width*2):
                    pygame.draw.rect(
                        screen, Window.colours[1], pygame.Rect(x, y, width, width))
            for x in range(width, 675-width, width*2):
                for y in range(width, 675-width, width*2):
                    pygame.draw.rect(
                        screen, Window.colours[1], pygame.Rect(x, y, width, width))
        
        def DrawPieces(screen):
            for x in range(8):
                for y in range(8):
                    if Board.storage[x][y] is not None:
                        Board.storage[x][y].Update()
                        if not (Board.storage[x][y].type == 'pawn' and Pieces.pawnBeingUpgraded is not None and Pieces.pawnBeingUpgraded[1] == Board.storage[x][y].coord):
                            screen.blit(Board.storage[x][y].image,
                                        Board.FlipCoord(Board.storage[x][y].pos, doingPieces=True))

        def DrawPossibleMoves(position, isPawn=False):
            # determines whether the move is taking a piece or not
            # if not is draws a circle otherwise it draws highlights in the corner of that square
            surface = pygame.Surface((75, 75), pygame.SRCALPHA)
            if position[0] != 'friendly' and (not isPawn or isPawn and position[0] != 'empty') and position[0] != 'kingBarrier':
                if Board.storage[position[1][0]][position[1][1]] is None:
                    pygame.draw.circle(
                        surface, (30, 30, 30), (38.5, 38.5), 13)
                    surface.set_alpha(150)
                    screen.blit(surface, surface.get_rect(
                        center=Board.FlipCoord(((position[1][1]*75)+36.5, (position[1][0]*75)+36.5))))
                else:
                    pygame.draw.circle(
                        surface, (30, 30, 30), (37.5, 37.5), 54, 10)
                    surface.set_alpha(150)
                    screen.blit(surface, surface.get_rect(
                        center=Board.FlipCoord(((position[1][1]*75)+36.5, (position[1][0]*75)+36.5), offset=-1)))

        DrawBoard(75)

        # if true check = [which king(either white or black), coords of king, coords of attacking pieces...] otherwise = None
        if Pieces.check is not None:
            surface = pygame.Surface((75, 75), pygame.SRCALPHA)
            pygame.draw.circle(surface, (200, 0, 0), (37.5, 37.5), 35)
            surface.set_alpha(100)
            screen.blit(surface, surface.get_rect(
                center=Board.FlipCoord(((Pieces.check[1][1]*75)+37.5, (Pieces.check[1][0]*75)+37.5))))
        if SideScreen.currentBoardPos == SideScreen.maxCurrentBoardPos:
            # Drawing yellow highlight on piece selected
            for x in range(8):
                for y in range(8):
                    if Board.storage[x][y] is not None and Board.storage[x][y].selected:
                        Board.pieceSelected = True
                        surface = pygame.Surface((75, 75), pygame.SRCALPHA)
                        pygame.draw.rect(surface, (251, 236, 93), 
                                            pygame.Rect(0, 0, 75, 75))
                        surface.set_alpha(150)
                        screen.blit(surface, surface.get_rect(
                                center=Board.FlipCoord((y*75+37, x*75+37))))
                        if Board.CheckIfDragged(justChecking=True):
                            squarebeingDraggedOver = Board.storage[x][y].MoveFinder(Board.GetCo_Ords()) # change name
                            if squarebeingDraggedOver is not None:
                                screen.blit(surface, surface.get_rect(
                                            center=Board.FlipCoord((squarebeingDraggedOver[1][1]*75+37, squarebeingDraggedOver[1][0]*75+37))))
            
            # highlights previous position of piecie previously moved and the square it hass moved to
            if Pieces.previousMove is not None:
                surface = pygame.Surface((75, 75), pygame.SRCALPHA)
                pygame.draw.rect(surface, (251, 236, 93), 
                                    pygame.Rect(0, 0, 75, 75))
                surface.set_alpha(120)
                screen.blit(surface, surface.get_rect(
                        center=Board.FlipCoord((Pieces.previousMove[0][1]*75+37, Pieces.previousMove[0][0]*75+37))))
                screen.blit(surface, surface.get_rect(
                        center=Board.FlipCoord((Pieces.previousMove[1][1]*75+37, Pieces.previousMove[1][0]*75+37))))
                
        DrawPieces(screen)

        if SideScreen.currentBoardPos == SideScreen.maxCurrentBoardPos and Window.ShowingMoves:
            #######Displaying Possible Moves########
            for x in range(8):
                for y in range(8):
                    if Board.storage[x][y] is not None and Board.storage[x][y].selected:
                        moves = Board.storage[x][y].possibleMoves.copy()
                        if Board.storage[x][y].type in ('pawn', 'bishop', 'rook', 'queen'):
                            for directionNum in range(len(moves)):
                                for positionNum in range(len(moves[directionNum])):
                                    if Board.storage[x][y].type == 'pawn':
                                        DrawPossibleMoves(
                                            moves[directionNum][positionNum], isPawn=True)
                                    else:
                                        DrawPossibleMoves(
                                            moves[directionNum][positionNum])
                        else:
                            for positionNum in range(len(moves)):
                                DrawPossibleMoves(moves[positionNum])
        
        # Displaying arrows/circles
        for item in Board.arrowStorage:
            if type(item[0]) == int:
                Board.DrawArrow(circleCoord=item)
            else:
                Board.DrawArrow(item[0], item[1])

        # Displaying Coordinate Identifiers
        letters = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')
        numbers = ('1', '2', '3', '4', '5', '6', '7', '8')
        font = pygame.font.SysFont('freesansbold', 25, False)
        
        for turn in range(8):
            Window.DisplayText(25, letters[turn], Window.colours[(0 if not Board.boardFlipped else 1) if turn%2 == 1 else (1 if not Board.boardFlipped else 0)], (69 + turn*75, 590) if not Board.boardFlipped else ((594 - turn*75, 590)))
        for turn in range(8):#
            Window.DisplayText(25, numbers[7-turn], Window.colours[(0 if not Board.boardFlipped else 1) if turn%2 == 0 else (1 if not Board.boardFlipped else 0)], 
                              (7, 15+turn*75) if not Board.boardFlipped else (7, 540-turn*75))

        # draws the display for a pawn being upgraded
        if Pieces.pawnBeingUpgraded is not None and (Window.currentMode == 'player' or Pieces.pawnBeingUpgraded is not None and Board.playerColour != Board.playerTurn):
            Board.DrawPawnUpgrade()

        Board.CheckIfDragged()

    def DrawArrow(startingCoord=None, endingCoord=None, circleCoord=None):
        if circleCoord is not None:
            circleCoord = ((circleCoord[1]*75) + 37.5, (circleCoord[0]*75) + 37.5)
            surface = pygame.Surface((75, 75), pygame.SRCALPHA)
            pygame.draw.circle(surface, (34,139,34), (37.5, 37.5), 32, 5)
            surface.set_alpha(150)
            screen.blit(surface, surface.get_rect(
                center=circleCoord))
        else:
            # finds the angle between the x axis and the end coordinate going anti clockwise
            angle = -math.degrees(math.atan2(startingCoord[0]-endingCoord[0], startingCoord[1]-endingCoord[1])) + 180
            startingCoord = ((startingCoord[1]*75) + 37.5, (startingCoord[0]*75) + 37.5)
            endingCoord = ((endingCoord[1]*75) + 37.5, (endingCoord[0]*75) + 37.5)
            distance = math.sqrt(
                    (startingCoord[0] - endingCoord[0])**2 + (startingCoord[1] - endingCoord[1])**2)
            centerCoord = (startingCoord[0]+(endingCoord[0] - startingCoord[0])/2, startingCoord[1]+(endingCoord[1] - startingCoord[1])/2)
            distance -= 20
            rWidth = 14
            tWidth = 40
            tHeight = 27
            rLength = distance-tHeight

            surface = pygame.Surface((distance, tWidth), pygame.SRCALPHA)
            pygame.draw.rect(surface, (34,139,34), pygame.Rect(0, (tWidth-rWidth)/2, rLength, rWidth))
            pygame.draw.polygon(surface, (34,139,34), ((rLength, 0), (distance, tWidth/2), (rLength, tWidth)))
            surface.set_alpha(150)
            surface = pygame.transform.rotate(surface, angle)
            screen.blit(surface, surface.get_rect(
                    center=centerCoord))

    def VerifyFen(fen):
        # if the correct number of entries have been entered
        # whether the piece/empty spaces total equals 64 which is the number board sqaures
        splitFen = fen.split(' ')
        boardPosSplit = splitFen[0].split('/')
        total = 0
        for row in boardPosSplit:
            for item in row:
                try:
                    total += int(item)
                except:
                    total += 1
        
        if len(splitFen) == 6 and len(boardPosSplit) == 8 and total == 64 and splitFen[0].count('k') == 1 and splitFen[0].count('K') == 1:
            return True
        else:
            return False

    def LeftMouseDownLogic(EditorInUse=False):
        # determines whether a piece is being selected or wether it is selecting a position for
        # a selected piece to move too
        # It does this by storing the board position of where the mouse was previously pressed down and up
        # if the mouse was previously released then a piece was selected and now is selecting to be moved
        # if not then a piece piece is being dragged or nothing is occuring
        Board.clickPosition = mousePos
        if Pieces.pawnBeingUpgraded is None:
            Board.pieceSelectedCoord = Pieces.DetectPieceSelection(mousePos)
            if EditorInUse:
                return
            if Board.pieceSelectedCoord is not None:
                if Board.pieceSelectedCoord2 is not None:
                    if Board.storage[Board.pieceSelectedCoord[0]][Board.pieceSelectedCoord[1]].colour == Board.playerTurn:
                        if Board.storage[Board.pieceSelectedCoord[0]][Board.pieceSelectedCoord[1]].colour == Board.storage[Board.pieceSelectedCoord2[0]][Board.pieceSelectedCoord2[1]].colour and Board.storage[Board.pieceSelectedCoord[0]][Board.pieceSelectedCoord[1]] != Board.storage[Board.pieceSelectedCoord2[0]][Board.pieceSelectedCoord2[1]]:
                            #print('here0')
                            Board.storage[Board.pieceSelectedCoord2[0]
                                            ][Board.pieceSelectedCoord2[1]].selected = False
                            Board.storage[Board.pieceSelectedCoord[0]
                                            ][Board.pieceSelectedCoord[1]].selected = True
                            Board.pieceSelected = True
                            Board.pieceSelectedCoord2 = None
                        else:
                            Board.storage[Board.pieceSelectedCoord[0]
                                            ][Board.pieceSelectedCoord[1]].selected = True
                    elif Board.pieceSelected:
                        #print('here1')
                        Board.newMoveMade = Board.storage[Board.pieceSelectedCoord2[0]][Board.pieceSelectedCoord2[1]].Move(
                        )
                    else:
                        #print('here2')
                        Board.storage[Board.pieceSelectedCoord2[0]
                                        ][Board.pieceSelectedCoord2[1]].selected = False
                        Board.storage[Board.pieceSelectedCoord[0]
                                        ][Board.pieceSelectedCoord[1]].selected = False
                        Board.pieceSelected = False
                elif Board.storage[Board.pieceSelectedCoord[0]][Board.pieceSelectedCoord[1]].colour == Board.playerTurn:
                    #print('here3')
                    Board.storage[Board.pieceSelectedCoord[0]
                                    ][Board.pieceSelectedCoord[1]].selected = True
                    Board.pieceSelected = True
            else:
                for x in range(8):
                    for y in range(8):
                        if Board.storage[x][y] is not None and Board.storage[x][y].selected:
                            #print('here4')
                            Board.newMoveMade = Board.storage[x][y].Move(
                            )
                            Board.pieceSelectedCoord2 = None
        elif Window.currentMode == 'player' or Pieces.pawnBeingUpgraded is not None and Board.playerColour != Board.playerTurn:
            Board.DrawPawnUpgrade(True)

    def LeftMouseUpLogic(EditorInUse=False):
        # deals with whether a piece was being dragged and now is being placed or wether a piece is just being selected
        if Pieces.pawnBeingUpgraded is None and Board.pieceSelectedCoord is not None:
            Board.pieceSelectedCoord2 = Pieces.DetectPieceSelection(mousePos)
            if EditorInUse:
                if (mousePos[1]//75, mousePos[0]//75) != Board.pieceSelectedCoord:
                    Board.storage[Board.pieceSelectedCoord[0]][Board.pieceSelectedCoord[1]].coord = (mousePos[1]//75, mousePos[0]//75)
                    Board.storage[mousePos[1]//75][mousePos[0]//75] = Board.storage[Board.pieceSelectedCoord[0]][Board.pieceSelectedCoord[1]]
                    Board.storage[Board.pieceSelectedCoord[0]][Board.pieceSelectedCoord[1]] = None
                Board.pieceSelectedCoord = None
                Board.pieceSelectedCoord2 = None
                return

            if Board.pieceSelectedCoord2 is not None:
                if Board.storage[Board.pieceSelectedCoord[0]][Board.pieceSelectedCoord[1]].colour == Board.storage[Board.pieceSelectedCoord2[0]][Board.pieceSelectedCoord2[1]].colour:
                    if Board.storage[Board.pieceSelectedCoord[0]][Board.pieceSelectedCoord[1]] != Board.storage[Board.pieceSelectedCoord2[0]][Board.pieceSelectedCoord2[1]]:
                        Board.storage[Board.pieceSelectedCoord2[0]
                                        ][Board.pieceSelectedCoord2[1]].selected = False
                        Board.storage[Board.pieceSelectedCoord[0]
                                        ][Board.pieceSelectedCoord[1]].selected = False
                        Board.pieceSelectedCoord = None
                        #print('here5')
                    elif Board.storage[Board.pieceSelectedCoord[0]][Board.pieceSelectedCoord[1]].colour == Board.playerTurn:
                        if Board.beingDragged:
                            Board.storage[Board.pieceSelectedCoord[0]
                                            ][Board.pieceSelectedCoord[1]].selected = False
                            Board.pieceSelected = False
                            Board.pieceSelectedCoord = None
                            Board.pieceSelectedCoord2 = None
                        else:
                            Board.storage[Board.pieceSelectedCoord[0]
                                            ][Board.pieceSelectedCoord[1]].selected = True
                            Board.pieceSelected = True
                        #print('here6')
                else:
                    Board.newMoveMade = Board.storage[Board.pieceSelectedCoord[0]][Board.pieceSelectedCoord[1]].Move(
                    )
                    if not Board.newMoveMade:
                        Board.pieceSelectedCoord = None
                        Board.pieceSelectedCoord2 = None
                    #print('here7')
            else:
                # Movement
                Board.newMoveMade = Board.storage[Board.pieceSelectedCoord[0]][Board.pieceSelectedCoord[1]].Move(
                )
                if not Board.newMoveMade:
                    Board.pieceSelectedCoord = None
                    Board.pieceSelectedCoord2 = None
                #print('here8')
                # check if piece can be placed

    def ArrowLogic():
        # determines using the mouse position of when pressed and released 
        # if a circle or arrow should be added or removed if it already occurs
        if Board.arrowSelectedCoord is not None:
            arrowCoords = (Board.arrowSelectedCoord, Board.GetCo_Ords(ignoreFlip=True))
            if arrowCoords in Board.arrowStorage:
                Board.arrowStorage.remove(arrowCoords)
            elif Board.arrowSelectedCoord in Board.arrowStorage:
                Board.arrowStorage.remove(Board.arrowSelectedCoord)
            elif arrowCoords[0] == arrowCoords[1]:
                Board.arrowStorage.append(Board.arrowSelectedCoord)    
            else:
                Board.arrowStorage.append((Board.arrowSelectedCoord, Board.GetCo_Ords(ignoreFlip=True)))
            Board.arrowSelectedCoord = None

    def NewMoveLogic():
        # deals with calculating the new position
        # and deals with making the AI move if in that mode
        if Board.autoBoardFlip:
            Board.boardFlipped = not Board.boardFlippedStorage
            Board.boardFlippedStorage = not Board.boardFlippedStorage
        Board.newMoveMade = False
        Pieces.CalculateMoves()
        Window.PlaySounds()

        Ai.EvaluationCalc()
        Window.DisplayWindow()

        if SideScreen.currentBoardPos == SideScreen.maxCurrentBoardPos and Window.currentEvent == 'game':
            SideScreen.AddTime()
            if Window.currentMode == 'ai' and Board.playerColour is not None and Board.playerTurn != Board.playerColour and Pieces.pawnBeingUpgraded is None:
                moves = Ai.FormatMoves()
                aiSelector = {
                    0: Ai.SelectRandomMove(moves[0]),
                    1: Ai.ScoringSystem(moves[0]),
                    2: Ai.FortuneTeller()
                }
                move, x, y = aiSelector[Ai.mode]
                Ai.Move(move, x, y)

        elif Window.currentMode == 'tutorial':
            # puzzle logic
            if len(Tutorial.moveOrder) > 0 and Board.BoardToFen() != Tutorial.previousFen:
                if Board.BoardToFen() == Tutorial.moveOrder[0]:
                    Tutorial.previousFen = Tutorial.moveOrder[0]
                    Tutorial.moveOrder.pop(0)
                    if len(Tutorial.moveOrder) > 0:
                        print(Tutorial.movesNum)
                        Board.SetBoard(Tutorial.moveOrder[0])
                        Tutorial.previousFen = Tutorial.moveOrder[0]
                        Tutorial.moveOrder.pop(0)
                else:
                    Tutorial.movesNum += 1
                    Board.SetBoard(Tutorial.previousFen)
                    return
            Tutorial.movesNum -= 1
            
            if not Tutorial.playerSwitching:
                Board.playerTurn = Tutorial.playerTurn
            
    def FlipCoord(_coord, doingPieces=False, doingBoardCoord=False, offset=0):
        # flips either the board or mouse coordinate entered for when the board is flipped
        if Board.boardFlipped:
            if doingPieces:
                return (523-_coord[0], 525-_coord[1])
            elif doingBoardCoord:
                return (7-_coord[0], _coord[1])
            else:
                return (599-_coord[0] + offset, 599-_coord[1] + offset)
        else:
            return _coord


class SideScreen:
    xWidth = 35
    buttonStorage = (
        pygame.Rect(625, 150, xWidth, 35), pygame.Rect(625 + 2*xWidth, 150, xWidth, 35),
        pygame.Rect(625 + 4*xWidth, 150, xWidth, 35), pygame.Rect(625 + 6*xWidth+5, 150, xWidth, 35),
        pygame.Rect(625, 415, xWidth, 35), pygame.Rect(625 + 1*xWidth, 415, xWidth, 35),
        pygame.Rect(625 + 2*xWidth, 415, xWidth, 35), pygame.Rect(625 + 3*xWidth, 415, xWidth, 35),
        pygame.Rect(625 + 4*xWidth, 415, xWidth, 35), pygame.Rect(625 + 6*xWidth+5, 415, xWidth, 35),
        pygame.Rect(840, 600, 60, 60), pygame.Rect(860, 0, 40, 40), pygame.Rect(536, 621, 18, 18),
        pygame.Rect(625 + 5*xWidth, 415, xWidth+5, 35), pygame.Rect(625 + 5*xWidth, 150, xWidth+5, 35),
        pygame.Rect(625 + 1*xWidth, 150, xWidth, 35), pygame.Rect(625 + 3*xWidth, 150, xWidth, 35))
    
    # each move stored as ((whitemove, fen), (blackmove, fen)) 
    movesMade = [Board.BoardToFen()] #where each move = piecetype + if a piece was taken + coord it moved too
    movesRectStorage = []
    scrollingIndex = 8
    maxCurrentBoardPos = [0, 1]
    currentBoardPos = [0, 1] #(move set, black or white move)

    timeWhite = None
    timeBlack = None
    timeControl = None
    waiting = None
   
    def Resetting(resettingTime=True):
        SideScreen.movesMade = [Board.BoardToFen()] 
        SideScreen.movesRectStorage = []
        SideScreen.scrollingIndex = 8
        SideScreen.maxCurrentBoardPos = [0, 1]
        SideScreen.currentBoardPos = [0, 1]
        if resettingTime:
            SideScreen.timeWhite = None
            SideScreen.timeBlack = None
            SideScreen.timeControl = None
            SideScreen.waiting = None
            Popups.displayingTime = False

    def Display():
        def CalculatePieceAdvantage():
            #counts the number of pieces for each colour
            #displays the letter representation of the piece if that colour has it and the other doesn't
            #display the difference in the capture score
            strings = ['', '']
            points = [0, 0]
            typeConverter = {
                'pawn': 'P1',
                'knight': 'N3',
                'bishop': 'B3',
                'rook': 'R5',
                'queen': 'Q9',
                'king': ' 0'
                }
            
            pieceCount = [[], []]
            for x in range(8):
                for y in range(8):
                    item = Board.storage[x][y] 
                    if item is not None:
                        if item.colour == 'white':
                            pieceCount[0].append(item.type)
                        else:
                            pieceCount[1].append(item.type)

            
            for turn in range(2):
                for pieceTaken in pieceCount[turn]:
                    strings[turn] += typeConverter[pieceTaken][0]
                    points[turn] += int(typeConverter[pieceTaken][1])

            # removing pieces that are in both sets
            stringsCopy = [[*strings[0]], [*strings[1]]]
            for letter in strings[0]:
                if letter in stringsCopy[1]:
                    stringsCopy[0].remove(letter)
                    stringsCopy[1].remove(letter)
            strings = ['', '']
            for letter in stringsCopy[0]:
                strings[0] += letter
            for letter in stringsCopy[1]:
                strings[1] += letter

            pieceSorter = {
                'Q': 0,
                'R': 1,
                'B': 2,
                'N': 3,
                'P': 4
            }
            seperatedString = [['', '', '', '', ''], ['', '', '', '', '']]
            for character in strings[0]:
                seperatedString[0][pieceSorter[character]] += character
            for character in strings[1]:
                seperatedString[1][pieceSorter[character]] += character
            strings = ['', '']
            for turn in range(5):
                strings[0] += seperatedString[0][turn]
                strings[1] += seperatedString[1][turn]

            return strings, points
        
        def DrawMoves():
            # draws the moves and the move notations in the sidescreen box
            movesMadeLen = len(SideScreen.movesMade)
            pygame.draw.rect(screen, Window.colours[2], (855, 184, 3, 232))
            length = 227*(7/(movesMadeLen-1 if movesMadeLen > 8 else 7))
            yStart = 186 + ((((SideScreen.scrollingIndex-8)/(movesMadeLen-1))*227) if movesMadeLen > 8 else 0) #(movesMadeLen-7/movesMadeLen*227) if movesMadeLen > 8 else 0 #*((SideScreen.scrollingIndex-8)/(len(SideScreen.movesMade)-8)) if (len(SideScreen.movesMade)-8) else -0.0
            pygame.draw.rect(screen, Window.colours[5], (858, yStart, 15, length))#
            #(627, 186, 227, 227) rect of circle area
            startCoord = (632, 194)
            wGap = 40
            bGap = 130
            yGap = 32.45
            #pygame.draw.rect(screen, Window.colours[3], (627, 186, 43, 33))#36
            for moveSet, turn in zip(SideScreen.movesMade[SideScreen.scrollingIndex-7:SideScreen.scrollingIndex], range(len(SideScreen.movesMade))):#

                pygame.draw.rect(screen, Window.colours[4], (627, 186 + turn*yGap, 36, 33))
                
                Window.DisplayText(25, str(turn+1 + SideScreen.scrollingIndex-8 + Board.startingMoveNum) + '.', Window.colours[2], startCoord, topLeft=True)
                if moveSet[0] is not None:
                    if pygame.Rect(663.5, 186 + turn*yGap, 94, 33) not in SideScreen.movesRectStorage:
                        SideScreen.movesRectStorage.append(pygame.Rect(663.5, 186 + turn*yGap, 94, 33))

                    if pygame.Rect(663.5, 186 + turn*yGap, 94, 33).collidepoint(mousePos) and Window.currentEvent == 'game':
                        pygame.draw.rect(screen, (83, 124, 35), (663.5, 186 + turn*yGap, 94, 33))
                    Window.DisplayText(25, moveSet[0][0], Window.colours[Window.TextColourIndex], (startCoord[0] + wGap, startCoord[1]), topLeft=True)
                if moveSet[1] is not None:
                    if pygame.Rect(757, 186 + turn*yGap, 97.5, 33) not in SideScreen.movesRectStorage:
                        SideScreen.movesRectStorage.append(pygame.Rect(757, 186 + turn*yGap, 97.5, 33))

                    if pygame.Rect(757, 186 + turn*yGap, 97.5, 33).collidepoint(mousePos):
                        pygame.draw.rect(screen, (83, 124, 35), (757, 186 + turn*yGap, 97.5, 33))
                    Window.DisplayText(25, moveSet[1][0], Window.colours[Window.TextColourIndex], (startCoord[0] + bGap, startCoord[1]), topLeft=True)
                
                startCoord = (startCoord[0], startCoord[1] + yGap)
        
        def DrawTimeControl():
            def CalcTime(time):
                minutes = time//60
                seconds = time%60
                return (str(minutes) if minutes >= 10 else '0' + str(minutes)) + ':' + (str(seconds) if seconds >= 10 else '0' + str(seconds))
            pygame.draw.rect(screen, Window.colours[0], (624, 82, 100, 36))
            pygame.draw.rect(screen, Window.colours[0], (624, 482, 100, 36))
            pygame.draw.rect(screen, Window.colours[2], (624, 82, 100, 36), 2)
            pygame.draw.rect(screen, Window.colours[2], (624, 482, 100, 36), 2)
            Window.DisplayText(30, CalcTime(SideScreen.timeBlack), Window.colours[2], (690, 100  if not Board.boardFlipped else 500), topRight=True)
            Window.DisplayText(30, CalcTime(SideScreen.timeWhite), Window.colours[2], (690, 500  if not Board.boardFlipped else 100), topRight=True)
            
        # Side screen fillers
        if Window.fillChoice: # filling the whole thing
            pygame.draw.rect(screen, Window.colours[0], pygame.Rect(624, 116, 252, 368))
        else: # leaving middle area empty
            pygame.draw.rect(screen, Window.colours[0], pygame.Rect(624, 116, 252, 70))
            pygame.draw.rect(screen, Window.colours[0], pygame.Rect(624, 414, 252, 70))

        pygame.draw.rect(screen, Window.colours[0], pygame.Rect(840, 600, 60, 60))
        pygame.draw.rect(screen, Window.colours[0], pygame.Rect(860, 0, 40, 40))
        pygame.draw.rect(screen, Window.colours[0], pygame.Rect(75, 615, 450, 30))

        # drawing buttons outline and icon and showing if buttons are being hovered over
        iconNums = (0, (15 if Window.currentMode == 'ai' else (1 if Board.autoBoardFlip else 2)), (15 if Window.currentMode == 'ai' else 3), 6, 5, 4, 8, 9, 3, 10, 14, 7, 13)
        for buttonRect, iconnum in zip(SideScreen.buttonStorage, iconNums):
            if Window.currentMode == 'ai' and iconnum == 15:
                continue
            if buttonRect.collidepoint(mousePos) and Window.currentEvent == 'game':
                if iconnum != 13:
                    pygame.draw.rect(screen, Window.colours[6], buttonRect)
                else:
                    pygame.draw.rect(screen, Window.colours[3], (539, 624, 12, 12))
            if iconnum in (8, 9, 10):
                screen.blit(pygame.transform.rotate(Window.sideScreenIcons[iconnum-4], 180), buttonRect)
            elif iconnum not in (13, 14):
                screen.blit(Window.sideScreenIcons[iconnum], buttonRect)
            elif iconnum == 14:
                Window.DisplayText(25, 'Menu', Window.colours[2], (870, 630))
            pygame.draw.rect(screen, Window.colours[2], buttonRect, 1)

        
        # board outline
        pygame.draw.rect(screen, Window.colours[2], pygame.Rect(600, 0, 3, 603))
        pygame.draw.rect(screen, Window.colours[2], pygame.Rect(0, 600, 600, 3))

        # side box outlines
        pygame.draw.rect(screen, Window.colours[2], pygame.Rect(625, 184, 250, 232), 2)
        pygame.draw.rect(screen, Window.colours[2], pygame.Rect(624, 149, 252, 302), 2)

        # name boxes
        pygame.draw.rect(screen, Window.colours[2], pygame.Rect(624, 116, 252, 35), 2)
        pygame.draw.rect(screen, Window.colours[2], pygame.Rect(624, 449, 252, 35), 2)

        # whos move it is outline
        pygame.draw.circle(screen, Window.colours[4], (641, 133), 10, 2)
        pygame.draw.circle(screen, Window.colours[4], (641, 466), 10, 2)

        #Drawing whos move it is
        if (Board.playerTurn == 'white' and not Board.boardFlipped) or (Board.playerTurn != 'white' and Board.boardFlipped):
            pygame.draw.circle(screen, (0, 150, 0) if SideScreen.currentBoardPos == SideScreen.maxCurrentBoardPos else (148,0,211), (641, 466), 8)
        else:
            pygame.draw.circle(screen, (0, 150, 0) if SideScreen.currentBoardPos == SideScreen.maxCurrentBoardPos else (148,0,211), (641, 133), 8)
        
        # Displaying names
        Window.DisplayText(25, Board.whiteName, Window.colours[2], (661, 458 if not Board.boardFlipped else 125), topLeft=True)
        Window.DisplayText(25, Board.blackName, Window.colours[2], (661, 125 if not Board.boardFlipped else 458), topLeft=True)


        strings, points = CalculatePieceAdvantage()
        # pieces taken names display
        Window.DisplayText(20, strings[0], Window.colours[Window.TextColourIndex], Board.FlipCoord((626, 488), offset=-14), topLeft=True)
        Window.DisplayText(20, strings[1], Window.colours[Window.TextColourIndex], Board.FlipCoord((626, 97), offset=-14), topLeft=True)

        # points advantage display
        if points[0]-points[1] > 0:
            Window.DisplayText(20, '+' + str(points[0]-points[1]), Window.colours[Window.TextColourIndex], Board.FlipCoord((626, 505), offset=-14), topLeft=True)
        if points[1]-points[0] > 0: 
            Window.DisplayText(20, '+' + str(points[1]-points[0]), Window.colours[Window.TextColourIndex], Board.FlipCoord((626, 80), offset=-14), topLeft=True)

        # fen box/button
        pygame.draw.rect(screen, Window.colours[2], (75, 615, 450, 30), 2)
        Window.DisplayText(15, Board.BoardToFen(), Window.colours[2], (80, 623), topLeft=True)
        pygame.draw.rect(screen, Window.colours[2], (536, 621, 18, 18), 3)
        if Window.showingText[0] > 0 and Window.showingText[1] == 'fen copied2':
            Window.DisplayText(18, 'Fen copied', Window.colours[Window.TextColourIndex], (535, 606), topLeft=True)
            Window.showingText[0] -= 1

        DrawMoves()

        if SideScreen.timeWhite is not None:
            DrawTimeControl()

        Window.DisplayText(30, str(Ai.evaluation * 0.1)[0 : 5], Window.colours[Window.TextColourIndex], (620, 630))

    def Buttons():
        # cycles through the rects of the buttons on the sidescreen and stops when it reaches the one if any has been pressed
        for turn in range(13):
            if Window.currentMode == 'ai' and turn in (1, 2):
                continue
            if SideScreen.buttonStorage[turn].collidepoint(mousePos):
                break
            elif turn == 12:
                turn += 1
                
        if turn == 2 and Board.boardFlipped:
            turn = 8
        elif turn == 8 and Board.boardFlipped:
            turn = 2
            

        if turn == 0:
            #flipboard
            Board.boardFlipped = not Board.boardFlipped
        elif turn == 1:
            #autoflip
            Board.boardFlipped = False if Board.playerTurn == 'white' else True
            Board.boardFlippedStorage = Board.boardFlipped
            Board.autoBoardFlip = not Board.autoBoardFlip
        elif turn == 2 and Pieces.numberOfMoves >= 2:
            #player2 Resigns
            Pieces.checkmate = True
            Window.currentEvent = 'blackResigns'
            Window.changingFen = Board.BoardToFen()
            SideScreen.Resetting()
        elif turn == 3 and len(SideScreen.movesMade) > 8 and SideScreen.scrollingIndex > 8:
            #moves screen up
            if SideScreen.scrollingIndex - 7 <= 8:
                SideScreen.scrollingIndex = 8
            else:
                SideScreen.scrollingIndex -= 7

        elif turn == 8 and Pieces.numberOfMoves >= 2:
            #player 1 resigns
            Pieces.checkmate = True
            Window.currentEvent = 'whiteResigns'
            Window.changingFen = Board.BoardToFen()
            SideScreen.Resetting()
        elif turn == 9 and len(SideScreen.movesMade) > 8 and SideScreen.scrollingIndex >= 8:
            #moves screen down
            if SideScreen.scrollingIndex + 7 >= len(SideScreen.movesMade):
                SideScreen.scrollingIndex = len(SideScreen.movesMade)
            else:
                SideScreen.scrollingIndex += 7
        elif turn == 10:
            #menu
            Window.currentMode = 'menu'
            Window.currentEvent = None
        elif turn == 11:
            #settings
            Window.currentEvent = 'settings'
        elif turn == 12:
            # copy fen
            cb.copy(Board.BoardToFen())
            Window.showingText = [100, 'fen copied2']
        # Moving Back/Forward Moves
        elif len(SideScreen.movesMade) > 1 and turn != 12:# and SideScreen.currentBoardPos[0] != 0 and SideScreen.currentBoardPos != SideScreen.maxCurrentBoardPos
            if turn == 4 and SideScreen.currentBoardPos[0] > 0:
                #ultra Left
                Board.SetBoard(SideScreen.movesMade[0], resetFlip=False)
                SideScreen.currentBoardPos = [0, 1]
            elif turn == 5 and SideScreen.currentBoardPos[0] > 0:
                #left
                
                if SideScreen.currentBoardPos[1] == 1:
                    if SideScreen.movesMade[SideScreen.currentBoardPos[0]][0] is None and type(SideScreen.movesMade[SideScreen.currentBoardPos[0]-1]) == str:
                        SideScreen.currentBoardPos = [0, 1]
                    else:
                        SideScreen.currentBoardPos = [SideScreen.currentBoardPos[0], 0]
                elif SideScreen.currentBoardPos[0] >= 1 and SideScreen.currentBoardPos[1] == 0:
                    SideScreen.currentBoardPos = [SideScreen.currentBoardPos[0] -1, 1]
                    
                if SideScreen.currentBoardPos[0] == 0:
                    Board.SetBoard(SideScreen.movesMade[SideScreen.currentBoardPos[0]], resetFlip=False)
                elif SideScreen.movesMade[SideScreen.currentBoardPos[0]][SideScreen.currentBoardPos[1]] is not None:
                    Board.SetBoard(SideScreen.movesMade[SideScreen.currentBoardPos[0]][SideScreen.currentBoardPos[1]][1], resetFlip=False)
            elif SideScreen.currentBoardPos != SideScreen.maxCurrentBoardPos:
                if turn == 6 and (SideScreen.currentBoardPos[0] < len(SideScreen.movesMade) or SideScreen.currentBoardPos[1] == SideScreen.maxCurrentBoardPos[1]-1):
                    #right
                    
                    if SideScreen.currentBoardPos[0] == SideScreen.maxCurrentBoardPos[0] and SideScreen.maxCurrentBoardPos[1] == 1:
                        SideScreen.currentBoardPos[1] = 1
                    elif SideScreen.currentBoardPos[1] == 0:
                        SideScreen.currentBoardPos[1] = 1
                    elif SideScreen.currentBoardPos[0] < len(SideScreen.movesMade):
                        SideScreen.currentBoardPos = [SideScreen.currentBoardPos[0] + 1, 0]
                        if SideScreen.movesMade[SideScreen.currentBoardPos[0]][0] is None and type(SideScreen.movesMade[SideScreen.currentBoardPos[0]-1]) == str:
                            SideScreen.currentBoardPos = [SideScreen.currentBoardPos[0], 1]
                        

                    if SideScreen.currentBoardPos[0] == 0:
                        Board.SetBoard(SideScreen.movesMade[SideScreen.currentBoardPos[0]], resetMove=False, resetFlip=False)
                    elif SideScreen.movesMade[SideScreen.currentBoardPos[0]][SideScreen.currentBoardPos[1]] is not None:
                        Board.SetBoard(SideScreen.movesMade[SideScreen.currentBoardPos[0]][SideScreen.currentBoardPos[1]][1], resetFlip=False)
                elif turn == 7:
                    #ultra right
                    
                    SideScreen.currentBoardPos = SideScreen.maxCurrentBoardPos
                    Board.SetBoard(SideScreen.movesMade[SideScreen.currentBoardPos[0]][SideScreen.currentBoardPos[1]][1], resetFlip=False)
            
        turn2 = None
        for turn2 in range(len(SideScreen.movesRectStorage)):
            if SideScreen.movesRectStorage[turn2].collidepoint(mousePos):
                break
            elif turn2 == len(SideScreen.movesRectStorage)-1:
                turn2 = None

        if turn2 is not None:
            if SideScreen.movesMade[0].split(' ')[1] == 'b':
                turn2 += 1
            turn2 += (SideScreen.scrollingIndex-8)*2
            SideScreen.currentBoardPos = [(turn2 // 2)+1, turn2 % 2]
            Board.SetBoard(SideScreen.movesMade[SideScreen.currentBoardPos[0]][SideScreen.currentBoardPos[1]][1])
    
    def AddMove(coord, type, colour, pawnXCoord, pieceTaken, castled=0):
        # adds the moves made by each player to storage
        typeConversion = {
            'pawn': Pieces.EnpassantConversion(pawnXCoord)[0],
            'bishop': 'B',
            'knight': 'N',
            'rook': 'R',
            'queen': 'Q',
            'king': 'K'
        }

        if castled:
            castlingString = 'O-O' if castled == 1 else 'O-O-O'
            move = [castlingString, Board.BoardToFen(swapColour=True)]
        else:
            move = [(typeConversion[type] if type != 'pawn' else '') + ('x' if pieceTaken else '') +  Pieces.EnpassantConversion(coord), Board.BoardToFen(swapColour=True)]
        #print(Board.BoardToFen(True))
        if colour == 'white':
            SideScreen.movesMade.append([move, None])
            SideScreen.maxCurrentBoardPos = [SideScreen.maxCurrentBoardPos[0]+1, 0]
            if len(SideScreen.movesMade) > 8:
                    SideScreen.scrollingIndex += 1
        else:
            if len(SideScreen.movesMade) == 1:
                SideScreen.movesMade.append([None, move])
                SideScreen.maxCurrentBoardPos = [SideScreen.maxCurrentBoardPos[0]+1, 1]
                if len(SideScreen.movesMade) > 8:
                    SideScreen.scrollingIndex += 1
            elif SideScreen.movesMade[-1][1] is None:
                SideScreen.movesMade[-1][1] = move
                SideScreen.maxCurrentBoardPos[1] = 1

        SideScreen.currentBoardPos = SideScreen.maxCurrentBoardPos

    def TimeTick():
        # deals with reducing the time for the player that has its current move
        # and checks if time runs out to declare a winner
        if SideScreen.timeWhite is not None:
            if Board.playerTurn == 'white' and SideScreen.timeWhite > 0:
                SideScreen.timeWhite -= 1
            elif SideScreen.timeBlack > 0:
                SideScreen.timeBlack -= 1

            if SideScreen.timeWhite == 0:
                Pieces.checkmate = True
                print('Black Wins! White out of time')
                Window.currentEvent = 'checkmateblack'
                Window.changingFen = Board.BoardToFen()
            elif SideScreen.timeBlack == 0:
                Pieces.checkmate = True
                print('White Wins! Black out of time')
                Window.currentEvent = 'checkmatewhite'
                Window.changingFen = Board.BoardToFen()

    def AddTime():
        # sets the time when first starting and deals with incrementing the time when a move is made
        if SideScreen.timeWhite is not None:
            if len(SideScreen.movesMade) == 1:
                pygame.time.set_timer(777, 1000)
                if Board.playerTurn == 'white':
                    SideScreen.timeWhite += 10
                    SideScreen.waiting = 'white'
                else:
                    SideScreen.timeBlack += 10
                    SideScreen.waiting = 'black'
            elif SideScreen.waiting:
                if SideScreen.waiting == 'white' and SideScreen.timeWhite > SideScreen.timeControl:
                    SideScreen.timeWhite = SideScreen.timeControl
                elif SideScreen.waiting == 'black' and SideScreen.timeBlack > SideScreen.timeControl:
                    SideScreen.timeBlack = SideScreen.timeControl
                SideScreen.waiting = None
            if Board.playerTurn == 'white':
                SideScreen.timeBlack += 1
            else:
                SideScreen.timeWhite += 1


class Popups:
    timeControlRects = [(375, 220, 137, 20), (375, 238, 137, 20), (375, 256, 137, 20), (375, 274, 137, 20), (375, 292, 137, 20), (375, 310, 137, 20)]
    timeControlStrings = ['None', '1 +1', '3 +1', '5 +1', '10 +1', '30 +1']

    displayingTime = False

    def Display():
        def SettingsDisplay():
            # drawing surface
            pygame.draw.rect(screen, Window.colours[0], (200, 130, 500, 400))
            pygame.draw.rect(screen, Window.colours[2], (200, 130, 500, 400), 3)

            # exit button
            if pygame.Rect((673, 133, 24, 24)).collidepoint(mousePos):
                pygame.draw.rect(screen, Window.colours[6], (670, 130, 30, 30))
            pygame.draw.rect(screen, Window.colours[2], (670, 130, 30, 30), 3)
            Window.DisplayText(35, 'X', Window.colours[9], (685, 145))

            # displaying background
            pygame.draw.rect(screen, Window.colours[2], (220, 150, 150, 120), 2)
            screen.blit(pygame.transform.scale(Window.backGroundImages[Window.backGroundChoice][0], (146, 116)), (222, 152))

            # displaying background buttons
            if pygame.Rect((375, 175, 30, 30)).collidepoint(mousePos) and Window.backGroundChoice-1 >= 0:
                pygame.draw.rect(screen, Window.colours[6], (375, 175, 30, 30))
            pygame.draw.rect(screen, Window.colours[2], (375, 175, 30, 30), 2)

            if pygame.Rect((375, 215, 30, 30)).collidepoint(mousePos) and Window.backGroundChoice+1 <= len(Window.backGroundImages)-1:
                pygame.draw.rect(screen, Window.colours[6], (375, 215, 30, 30))
            pygame.draw.rect(screen, Window.colours[2], (375, 215, 30, 30), 2)

            screen.blit(pygame.transform.scale(pygame.transform.rotate(Window.sideScreenIcons[4], -90), (25, 30)), (377.5, 175))
            screen.blit(pygame.transform.scale(pygame.transform.rotate(Window.sideScreenIcons[4], 90), (25, 30)), (377.5, 215))

            # showing moves
            Window.DisplayText(25, 'Show Possible Moves', Window.colours[2], (540, 170))
            if pygame.Rect((495, 190, 90, 40)).collidepoint(mousePos):
                pygame.draw.rect(screen, Window.colours[6], (495, 190, 90, 40))
            pygame.draw.rect(screen, Window.colours[2], (495, 190, 90, 40), 2)
            Window.DisplayText(25, ('True' if Window.ShowingMoves else 'False'), Window.colours[2], (540, 210))

            # filling sidescreen moves area
            Window.DisplayText(25, 'Fill Moves Area', Window.colours[2], (300, 300))
            if pygame.Rect((260, 320, 90, 40)).collidepoint(mousePos):
                pygame.draw.rect(screen, Window.colours[6], (260, 320, 90, 40))
            pygame.draw.rect(screen, Window.colours[2], (260, 320, 90, 40), 2)
            Window.DisplayText(25, ('True' if Window.fillChoice else 'False'), Window.colours[2], (305, 340))

        def AiAndPlayerDisplay ():
            # drawing box
            pygame.draw.rect(screen, Window.colours[0], (300, 100, 300, 460))
            pygame.draw.rect(screen, Window.colours[8], (300, 100, 300, 460), 3)

            # drawing state of game
            textExchanger = {
                'whiteResigns': 'Black Wins',
                'blackResigns': 'White Wins',
                'stalemate': 'Stalemate',
                'checkmateblack': 'Black Wins',
                'checkmatewhite': 'White Wins',
                'start': 'Start Game',
            }
            text = textExchanger.get(Window.currentEvent, 'Error')
            Window.DisplayText(60, text, Window.colours[8], (450, 150), bold= True)

            # drawing fen input
            if len(Window.changingFen) <= 60:
                pygame.draw.rect(screen, Window.colours[2], (315, 518, 270, 24), 2)
                Window.DisplayText(13, Window.changingFen, Window.colours[2], (320, 523), topLeft=True)
            else:
                fenSplit = Window.changingFen.split(' ')
                pygame.draw.rect(screen, Window.colours[2], (315, 518, 270, 28), 2)
                Window.DisplayText(13, fenSplit[0], Window.colours[2], (320, 523), topLeft=True)
                Window.DisplayText(13, ' '.join(fenSplit[1::]), Window.colours[2], (450, 535))

            #Menu button
            if pygame.Rect((505, 380, 80, 80)).collidepoint(mousePos):
                pygame.draw.rect(screen ,Window.colours[6], (505, 380, 80, 80))
            pygame.draw.rect(screen, Window.colours[2], (505, 380, 80, 80), 2)
            Window.DisplayText(40, 'Menu', Window.colours[8], (545, 420))

            # copy fen button
            if pygame.Rect((570, 495, 15, 15)).collidepoint(mousePos):
                pygame.draw.rect(screen ,Window.colours[3], (570, 495, 15, 15))
            pygame.draw.rect(screen, Window.colours[2], (570, 495, 15, 15), 2)

            # reset Fen Button
            if pygame.Rect((315, 490, 50, 25)).collidepoint(mousePos):
                pygame.draw.rect(screen ,Window.colours[6], (315, 490, 50, 25))
            pygame.draw.rect(screen, Window.colours[2], (315, 490, 50, 25), 2)
            Window.DisplayText(20, 'Reset', Window.colours[2], (320, 495), topLeft=True)

            if Window.currentMode == 'ai':
                # white start button
                if pygame.Rect((315, 230, 80, 80)).collidepoint(mousePos):
                    pygame.draw.rect(screen ,Window.colours[6], (315, 230, 80, 80))
                pygame.draw.rect(screen, Window.colours[2], (315, 230, 80, 80), 2)
                Window.DisplayText(30, 'White', Window.colours[2], (355, 270))

                # random start button
                if pygame.Rect((410, 230, 80, 80)).collidepoint(mousePos):
                    pygame.draw.rect(screen ,Window.colours[6], (410, 230, 80, 80))
                pygame.draw.rect(screen, Window.colours[2], (410, 230, 80, 80), 2)
                Window.DisplayText(25, 'Random', Window.colours[2], (450, 270))

                # black start button
                if pygame.Rect((505, 230, 80, 80)).collidepoint(mousePos):
                    pygame.draw.rect(screen ,Window.colours[6], (505, 230, 80, 80))
                pygame.draw.rect(screen, Window.colours[2], (505, 230, 80, 80), 2)
                Window.DisplayText(30, 'Black', Window.colours[2], (545, 270))

                # AI depth buttons
                for turn in range(1, 6):
                    newX = 325 + (turn-1)*35
                    if pygame.Rect((newX, 350, 25, 25)).collidepoint(mousePos):
                        pygame.draw.rect(screen ,Window.colours[6], (newX, 350, 25, 25))
                    if turn == Ai.depth:
                        pygame.draw.rect(screen, Window.colours[3], (newX, 350, 25, 25))
                    pygame.draw.rect(screen, Window.colours[2], (newX, 350, 25, 25), 2)
                    Window.DisplayText(30, str(turn), Window.colours[2], (newX+12, 363))
            elif Window.currentMode == 'player':
                #start button
                if pygame.Rect((315, 380, 80, 80)).collidepoint(mousePos):
                    pygame.draw.rect(screen ,Window.colours[6], (315, 380, 80, 80))
                pygame.draw.rect(screen, Window.colours[2], (315, 380, 80, 80), 2)
                Window.DisplayText(40, 'Start', Window.colours[8], (355, 420))

                # time control main display
                Window.DisplayText(25, 'Time Control', Window.colours[2], (450, 200))
                if pygame.Rect((512, 220, 15, 20)).collidepoint(mousePos):
                    pygame.draw.rect(screen ,Window.colours[3], (510, 220, 15, 20))
                pygame.draw.rect(screen, Window.colours[2], (510, 220, 15, 20), 2)
                Window.DisplayText(20, 'None', Window.colours[2], (443, 230))

                # each time control length option
                for turn in range(0, 6):
                    if not Popups.displayingTime and turn > 0:
                        break
                    if pygame.Rect(Popups.timeControlRects[turn]).collidepoint(mousePos):
                        pygame.draw.rect(screen, Window.colours[6], Popups.timeControlRects[turn])
                    pygame.draw.rect(screen, Window.colours[2], Popups.timeControlRects[turn], 2)
                    Window.DisplayText(20, Popups.timeControlStrings[turn], Window.colours[2], (443, 230 + 18*(turn)))

            # displaying notification for if fen is copied or if incorrect fen is pasted
            if Window.showingText[0] > 0:
                if Window.showingText[1] == 'error':
                    Window.DisplayText(15, 'Error! Invalid Fen pasted', Window.colours[9], (380, 500), topLeft=True)
                elif Window.showingText[1] == 'fen copied1':
                    Window.DisplayText(15, 'Fen copied', Window.colours[2], (525, 480), topLeft=True)
                Window.showingText[0] -= 1

        surface = pygame.Surface((900, 660), pygame.SRCALPHA)
        pygame.draw.rect(surface, Window.colours[2], (0, 0, 900, 660))
        surface.set_alpha(150)
        screen.blit(surface, surface.get_rect())
        if Window.currentEvent == 'settings':
            SettingsDisplay()

        elif Window.currentEvent in ('start', 'whiteResigns', 'blackResigns', 'stalemate', 'checkmateblack', 'checkmatewhite'):
            AiAndPlayerDisplay()
          
    def Buttons():
        if Window.currentEvent == 'settings':
            if pygame.Rect((673, 133, 24, 24)).collidepoint(mousePos): # exit settings
                if Window.currentMode in ('menu', 'boardeditor'):
                    Window.currentEvent = None
                else:
                    Window.currentEvent = 'game'
            else:
                if pygame.Rect((375, 175, 30, 30)).collidepoint(mousePos) and Window.backGroundChoice-1 >= 0:
                    Window.backGroundChoice -= 1

                elif pygame.Rect((375, 215, 30, 30)).collidepoint(mousePos) and Window.backGroundChoice+1 <= len(Window.backGroundImages)-1:
                    Window.backGroundChoice += 1
                
                elif pygame.Rect((495, 190, 90, 40)).collidepoint(mousePos):
                    Window.ShowingMoves = not Window.ShowingMoves

                elif pygame.Rect((260, 320, 90, 40)).collidepoint(mousePos):
                    Window.fillChoice = not Window.fillChoice
                
                with open('Settings.txt', 'w') as file:
                    file.writelines(str(Window.backGroundChoice) + '#' + str(int(Window.ShowingMoves)) + '#' + str(int(Window.fillChoice)))

        elif Window.currentMode in ('ai', 'player'):
            if pygame.Rect((505, 380, 80, 80)).collidepoint(mousePos):
                Window.currentMode = 'menu'
                Window.currentEvent = None

            elif pygame.Rect((570, 495, 15, 15)).collidepoint(mousePos):
                # fen copied
                cb.copy(Board.BoardToFen())
                Window.showingText = [100, 'fen copied1']
            elif pygame.Rect((315, 490, 50, 25)).collidepoint(mousePos):
                Window.changingFen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 0'

            if Window.currentMode == 'ai':
                clicked = False
                if pygame.Rect((315, 230, 80, 80)).collidepoint(mousePos):
                    Board.playerColour = 'white'
                    clicked = True
                elif pygame.Rect((410, 230, 80, 80)).collidepoint(mousePos): 
                    Board.playerColour = 'white' if random.randint(0, 1) else 'black'
                    clicked = True
                elif pygame.Rect((505, 230, 80, 80)).collidepoint(mousePos):
                    Board.playerColour = 'black'
                    clicked = True

                
                if clicked:
                    Board.whiteName = 'Player' if Board.playerColour == 'white' else 'Ai'
                    Board.blackName = 'Player' if Board.playerColour == 'black' else 'Ai'
                    if Board.playerColour != 'white':
                        Board.boardFlipped = True
                    else:
                        Board.boardFlipped = False
                    if Window.currentEvent not in ('start', 'blackResigns', 'whiteResigns'):
                        Window.changingFen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 0'
                    Board.SetBoard(Window.changingFen, resetFlip=False)
                    Window.currentEvent = 'game'
                    Popups.displayingTime = False
                else:
                    for turn in range(1, 6):
                        newX = 325 + (turn-1)*35
                        if pygame.Rect((newX, 350, 25, 25)).collidepoint(mousePos):
                            Ai.depth = turn
                            break
            elif Window.currentMode == 'player':
                if pygame.Rect((315, 380, 80, 80)).collidepoint(mousePos):
                    if Window.currentEvent not in ('start', 'blackResigns', 'whiteResigns'):
                        Window.changingFen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 0'
                    Board.SetBoard(Window.changingFen)
                    SideScreen.Resetting(resettingTime=False)
                    Window.currentEvent = 'game'

                if pygame.Rect((512, 220, 15, 20)).collidepoint(mousePos):
                    Popups.displayingTime = not Popups.displayingTime
                timeConverter = {'None': None, '1 +1': 60, '3 +1': 180, '5 +1': 300, '10 +1': 600, '30 +1': 1800}

                for turn in range(0, 6):
                    if not Popups.displayingTime and turn > 0:
                        break
                    if pygame.Rect(Popups.timeControlRects[turn]).collidepoint(mousePos):
                        SideScreen.timeWhite = timeConverter[Popups.timeControlStrings[turn]]
                        SideScreen.timeBlack = timeConverter[Popups.timeControlStrings[turn]]
                        SideScreen.timeControl = timeConverter[Popups.timeControlStrings[turn]]


class Menu:

    def Display():
        Window.DisplayText(70, 'Chess.co.uk', Window.colours[Window.TextColourIndex], (450, 100))

        #Player VS Player
        if pygame.Rect((100, 350, 200, 200)).collidepoint(mousePos):
            surface = pygame.Surface((200, 200), pygame.SRCALPHA)
            pygame.draw.rect(surface, Window.colours[3], (0, 0, 200, 200))
            surface.set_alpha(100)
            screen.blit(surface, (100, 350, 200, 200))
        pygame.draw.rect(screen, Window.colours[Window.backGroundChoice], (100, 350, 200, 200), 4)
        Window.DisplayText(35, 'Player VS Player', Window.colours[Window.TextColourIndex], (200, 450))

        #Player VS Ai
        if pygame.Rect((350, 350, 200, 200)).collidepoint(mousePos):
            surface = pygame.Surface((200, 200), pygame.SRCALPHA)
            pygame.draw.rect(surface, Window.colours[3], (0, 0, 200, 200))
            surface.set_alpha(100)
            screen.blit(surface, (350, 350, 200, 200))
        pygame.draw.rect(screen, Window.colours[Window.backGroundChoice], (350, 350, 200, 200), 4)
        Window.DisplayText(40, 'Player VS Ai', Window.colours[Window.TextColourIndex], (450, 450))

        #Tutorial
        if pygame.Rect((600, 350, 200, 200)).collidepoint(mousePos):
            surface = pygame.Surface((200, 200), pygame.SRCALPHA)
            pygame.draw.rect(surface, Window.colours[3], (0, 0, 200, 200))
            surface.set_alpha(100)
            screen.blit(surface, (600, 350, 200, 200))
        pygame.draw.rect(screen, Window.colours[Window.backGroundChoice], (600, 350, 200, 200), 4)
        Window.DisplayText(40, 'Tutorial', Window.colours[Window.TextColourIndex], (700, 450))
        
        #Board Editor
        if pygame.Rect((0, 0, 100, 100)).collidepoint(mousePos):
            surface = pygame.Surface((100, 100), pygame.SRCALPHA)
            pygame.draw.rect(surface, Window.colours[3], (0, 0, 100, 100))
            surface.set_alpha(100)
            screen.blit(surface, (0, 0, 100, 100))
        pygame.draw.rect(screen, Window.colours[Window.backGroundChoice], (0, 0, 100, 100), 4)
        Window.DisplayText(30, 'Board', Window.colours[Window.TextColourIndex], (50, 35))
        Window.DisplayText(30, 'Editor', Window.colours[Window.TextColourIndex], (50, 65))

        #Settings
        if pygame.Rect((825, 585, 75, 75)).collidepoint(mousePos):
            surface = pygame.Surface((100, 100), pygame.SRCALPHA)
            pygame.draw.rect(surface, Window.colours[3], (0, 0, 75, 75))
            surface.set_alpha(100)
            screen.blit(surface, (825, 585, 75, 75))
        pygame.draw.rect(screen, Window.colours[Window.backGroundChoice], (825, 585, 75, 75), 4)
        Window.DisplayText(23, 'Settings', Window.colours[Window.TextColourIndex], (862, 622))

    def Buttons():
        #Player vs Player
        if pygame.Rect((100, 350, 200, 200)).collidepoint(mousePos):
            Board.SetBoard('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 0')
            Window.currentEvent = 'start'
            Window.currentMode = 'player'
            Board.newMoveMade = True
            Board.whiteName = 'White'
            Board.blackName = 'Black'
            SideScreen.Resetting()
        # AI mode
        elif pygame.Rect((350, 350, 200, 200)).collidepoint(mousePos):
            Board.SetBoard('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 0')
            Window.currentEvent = 'start'
            Window.currentMode = 'ai'
            Board.newMoveMade = True
            Board.whiteName = 'White'
            Board.blackName = 'Ai'
            SideScreen.Resetting()
        #Tutorial
        elif pygame.Rect((600, 350, 200, 200)).collidepoint(mousePos):
            Window.currentMode = 'tutorial'
            Tutorial.level = Tutorial.startingLevel
            Tutorial.LevelOrganiser()
            Window.ShowingMoves = True
        #Board Editor
        elif pygame.Rect((0, 0, 100, 100)).collidepoint(mousePos):
            Board.SetBoard('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 0')
            Window.currentMode = 'boardeditor'
        #Settings
        elif pygame.Rect((825, 585, 75, 75)).collidepoint(mousePos):
            Window.currentEvent = 'settings'


class Window:
    colours = [(181, 136, 99), (240, 217, 181), (0, 0, 0),
            (255, 255, 255), (163, 163, 163), (188, 123, 73), (201, 156, 119), (206, 10, 202), (145, 179, 80), (255, 0, 0)]
    backGroundImages = None
    sideScreenIcons = None

    backGroundChoice = 3
    fillChoice = 0
    TextColourIndex = 2
    ShowingMoves = True

    currentEvent = None
    currentMode = 'menu'
    showingText = [0, '']
    changingFen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 0'

    def init():
        #loads icons and sound files
        Window.LoadContent()
        # loads ai location evaluation tables
        Ai.LoadLocationScores()

        try:
            with open('Settings.txt', 'r') as file:
                lineSplit = file.readlines()[0].split('#')
                Window.backGroundChoice = int(lineSplit[0])
                Window.ShowingMoves = bool(int(lineSplit[1]))
                Window.fillChoice = bool(int(lineSplit[2]))
        except:
            with open('Settings.txt', 'w') as file:
                file.writelines(str(Window.backGroundChoice) + '#' + str(int(Window.ShowingMoves)) + '#' + str(int(Window.fillChoice)))

    def LoadContent():
        path = os.getcwd() + "\\"
        iconNames = ('Flip', 'ActivatedAutoFlip', 'EmptyAutoFlip', 'flag', 'MoveOnce', 'UltraMove', 'MoveScreen', 'settings')
        Window.sideScreenIcons = []
        # loading button icons
        for iconname in iconNames:
            Window.sideScreenIcons.append(pygame.transform.scale(pygame.image.load(
                        path + 'ButtonIcons\\'+ iconname +'Icon.png'), (70, 70) if iconname == 'Menu' else (40, 40) if iconname == 'settings' else (35, 35)))
        # loading background images
        backGroundNames = ((0, 2), (4, 2), ('geometric', 7), ('mountainLake', 0))
        Window.backGroundImages = []
        for backGroundName in backGroundNames:
            if type(backGroundName[0]) == int:
                surface = pygame.Surface((900, 660), pygame.SRCALPHA)
                surface.fill(Window.colours[backGroundName[0]])
                Window.backGroundImages.append((surface, backGroundName[1]))
                continue
            Window.backGroundImages.append((pygame.transform.scale(pygame.image.load(
                        path + 'Backgrounds\\'+ backGroundName[0] +'_background.jpg'), (900, 660)), backGroundName[1]))

        # loading piece icons
        pieceLetter = ['p', 'b', 'n', 'r', 'q', 'k']
        colourLetter = ('l', 'd')
        Pieces.pieceImages = []
        for colourIndex in colourLetter:
            for pieceIndex in pieceLetter:
                Pieces.pieceImages.append(pygame.transform.scale(pygame.image.load(
                    path + 'Pieces\Chess_'+pieceIndex+colourIndex+'t60.png'), (75, 75)))

        # loading sound files
        pieceSoundType = ('move-self', 'capture', 'castle',
                          'move-check', 'promote', 'game-end')
        for soundtype in pieceSoundType:
            Pieces.pieceSounds.append(mixer.Sound(
                path + 'Sounds\\' + soundtype + '.mp3'))
              
    def DisplayText(fontSize, text, colour, position, topLeft=False, bold=False, topRight=False):
        font = pygame.font.SysFont('freesansbold', fontSize, bold)
        text = font.render(text, True, colour)
        if not topLeft:
            textrect = text.get_rect(center=position)
        elif topLeft:
            textrect = text.get_rect(topleft=position)
        elif topRight:
            textrect = text.get_rect(topright=position)
        screen.blit(text, textrect)

    def DisplayWindow():
        if Window.currentMode == 'tutorial':
            screen.fill((38, 36, 33))
            Tutorial.Display()
            pygame.display.update()
            return

        screen.blit(Window.backGroundImages[Window.backGroundChoice][0], (0, 0))
        Window.TextColourIndex = Window.backGroundImages[Window.backGroundChoice][1]
        
        if Window.currentMode == 'menu':
            Menu.Display()
        elif Window.currentMode in ('player', 'ai'):
            SideScreen.Display()

            Board.DisplayBoard()
        elif Window.currentMode == 'boardeditor':
            BoardEditor.Display()
            

        if (Window.currentMode in ('player', 'ai') and Window.currentEvent != 'game') or (Window.currentMode in ('menu', 'boardeditor') and Window.currentEvent is not None): 
            Popups.Display()

        pygame.display.update()

    def EventLogic(event):
        typeConverter = {
            0: ('white', 'pawn'),
            1: ('white', 'bishop'),
            2: ('white', 'knight'),
            3: ('white', 'rook'),
            4: ('white', 'queen'),
            5: ('white', 'king'),
            6: ('black', 'pawn'),
            7: ('black', 'bishop'),
            8: ('black', 'knight'),
            9: ('black', 'rook'),
            10: ('black', 'queen'),
            11: ('black', 'king')
        }
        if event.type == pygame.QUIT:
            if Window.currentMode != 'menu':
                print(Board.BoardToFen())
            return False
        
        elif Window.currentEvent == 'game':
            # clock- second
            if event.type == 777 and SideScreen.currentBoardPos == SideScreen.maxCurrentBoardPos:
                SideScreen.TimeTick()
            #scrolling moves
            elif event.type == pygame.MOUSEWHEEL:
                if 8 <= SideScreen.scrollingIndex - event.y <= len(SideScreen.movesMade) and pygame.Rect(625, 184, 250, 232).collidepoint(mousePos):
                    SideScreen.scrollingIndex -= event.y
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if mousePos[0] < 600 and mousePos[1] < 600 and (Window.currentMode != 'ai' or Board.playerColour == Board.playerTurn or Pieces.pawnBeingUpgraded is not None):
                        Board.arrowStorage = []
                        Board.LeftMouseDownLogic()
                    else:
                        SideScreen.Buttons()
                elif event.button == 3 and Board.arrowSelectedCoord is None:
                    Board.arrowSelectedCoord = Board.GetCo_Ords(ignoreFlip=True)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and mousePos[0] < 600 and mousePos[1] < 600:
                    Board.LeftMouseUpLogic()
                #drawing arrows
                elif event.button == 3:
                    Board.ArrowLogic()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if Window.currentMode == 'menu':
                if Window.currentEvent is not None:
                    Popups.Buttons()
                else:
                    Menu.Buttons()
            elif Window.currentMode == 'boardeditor':
                if Window.currentEvent is not None:
                    Popups.Buttons()
                elif mousePos[0] < 600 and mousePos[1] < 600:
                    if BoardEditor.selectionIndex is not None:
                        if BoardEditor.selectionIndex != 12:
                            _pos = Board.GetCo_Ords()
                            info = typeConverter[BoardEditor.selectionIndex]
                            if Board.storage[_pos[0]][_pos[1]] is not None and Board.storage[_pos[0]][_pos[1]].type == info[1] and Board.storage[_pos[0]][_pos[1]].colour == info[0]:
                                Board.storage[_pos[0]][_pos[1]] = None
                            else:
                                BoardEditor.clicked = True
                        else:
                            BoardEditor.clicked = True
                    else:
                        Board.LeftMouseDownLogic(EditorInUse=True)
                else:
                    BoardEditor.Buttons()
            elif Window.currentMode == 'tutorial':
                Tutorial.Buttons()
                if not Tutorial.blocked:
                    Board.LeftMouseDownLogic()
            else:
                Popups.Buttons()
        elif event.type == pygame.MOUSEBUTTONUP:
            if Window.currentMode == 'boardeditor':
                if BoardEditor.selectionIndex is None:
                    Board.LeftMouseUpLogic(EditorInUse=True)
                else:
                    BoardEditor.clicked = False
            elif Window.currentMode == 'tutorial' and not Tutorial.blocked:
                Board.LeftMouseUpLogic()
            
        elif event.type == pygame.KEYDOWN and event.type in (768, 769) and event.key == 118:
            if Board.VerifyFen(cb.paste()):
                Window.changingFen = cb.paste() 
            else:
                Window.showingText = [100, 'error']
        return True

    def PlaySounds():
        # stores sounds to be played in a queue and filters through
        if len(Board.soundQueue) == 2:
            if Board.soundQueue[1] == 3:
                Board.soundQueue.pop(0)
            elif Board.soundQueue[1] == 0:
                Board.soundQueue.pop(1)
        if len(Board.soundQueue) == 3 and Board.soundQueue[-1] == 5:
            Board.soundQueue = [5]
            
        for turn in range(len(Board.soundQueue)):
            if not pygame.mixer.get_busy():
                Pieces.pieceSounds[Board.soundQueue[0]].play()
                Board.soundQueue.pop(0)
            else:
                break


class Ai:
    # [pawn, knight, bishop, rook, queen, king]
    locationScores = []
    evaluation = 0
    mode = 2

    movesTree = []

    depth = 4

    def LoadLocationScores(colour='white'):
        with open('LocationScores.txt', 'r') as file:
            sets = [[], [], [], [], [], []]
            setNum = 0
            lineNum = 1
            for line in file.readlines():
                splitLine = line.split(', ')
                splitLine[-1] = splitLine[-1].strip()
                if splitLine != ['']:
                    for turn in range(8):
                        splitLine[turn] = float(splitLine[turn])
                    sets[setNum].append(splitLine)
                else:
                    continue

                if lineNum == 8:
                    lineNum = 1
                    setNum += 1
                else:
                    lineNum += 1

                if setNum == 6:
                    break

            if colour == 'white':
                Ai.locationScores = sets
            else:
                setCopy = [[], [], [], [], [], []]
                # for if ai is black
                for setIndex in range(6):
                    for lineIndex in range(len(sets[setIndex])-1, -1, -1):
                        setCopy[setIndex].append(sets[setIndex][lineIndex])
                Ai.locationScores = setCopy

    def EvaluationCalc(returning=False):
        # uses method of which the best score for black is -infinity the best for white is +infinity
        # adds scores from having pieces
        # then the scores for the position of those pieces
        scores = [0, 0]

        pieceScore = {
            'pawn': 10,
            'knight': 30, 
            'bishop': 30,
            'rook': 50,
            'queen': 90,
            'king': 0
        }
        indexConversion = ['pawn', 'knight', 'bishop', 'rook', 'queen', 'king']
        positionConversion = [7, 6, 5, 4, 3, 2, 1, 0]
        for x in range(8):
            for y in range(8):
                if Board.storage[x][y] is not None:
                    num = 0 if Board.storage[x][y].colour == 'white' else 1
                    scores[num] += (-1 if num == 1 else 1) * pieceScore[Board.storage[x][y].type]
                    scores[num] += (-1 if num == 1 else 1) * Ai.locationScores[indexConversion.index(Board.storage[x][y].type)][x if Board.storage[x][y].colour == 'white' else positionConversion[x]][y]

        if not returning:
            Ai.evaluation = scores[0] + scores[1]
        else:
            return scores[0] + scores[1]

    def FormatMoves():   
        # takes all the possible moves each piece of a each colour can do and puts them in a single list
        # as well as remove moves that aren't proper moves such as those which are place holders 
        def addMoves(colourIndex, _x, _y):
            if Board.storage[_x][_y].type in ('knight', 'king'):
                for move in Board.storage[_x][_y].possibleMoves:
                    if move[0] not in ('kingBarrier', 'friendly'):
                        if move[0] == 'enemy':
                            possibleMoves[colourIndex].insert(0, [(_x, _y), move])
                        else:
                            possibleMoves[colourIndex].append([(_x, _y), move])

            else:
                for directionNum in range(len(Board.storage[_x][_y].possibleMoves)):
                    for positionNum in range(len(Board.storage[_x][_y].possibleMoves[directionNum])):
                        if Board.storage[_x][_y].type == 'pawn':
                            if directionNum != 1 and Board.storage[_x][_y].possibleMoves[directionNum][positionNum][0] not in ('friendly', 'empty'):
                                if Board.storage[_x][_y].possibleMoves[directionNum][positionNum][0] == 'enemy':
                                    possibleMoves[colourIndex].insert(0, [(_x, _y), Board.storage[_x][_y].possibleMoves[directionNum][positionNum]])
                                else:
                                    possibleMoves[colourIndex].append([(_x, _y), Board.storage[_x][_y].possibleMoves[directionNum][positionNum]])
                            elif directionNum == 1:
                                if Board.storage[_x][_y].possibleMoves[1][0][1][0] == 7 and Board.playerColour == 'white' or Board.storage[_x][_y].possibleMoves[1][0][1][0] == 0 and Board.playerColour == 'black':
                                    possibleMoves[colourIndex].append([(_x, _y), ['upgradequeen', Board.storage[_x][_y].possibleMoves[1][0][1]]])
                                    possibleMoves[colourIndex].append([(_x, _y), ['upgradeknight', Board.storage[_x][_y].possibleMoves[1][0][1]]])
                                    possibleMoves[colourIndex].append([(_x, _y), ['upgradebishop', Board.storage[_x][_y].possibleMoves[1][0][1]]])
                                    possibleMoves[colourIndex].append([(_x, _y), ['upgraderook', Board.storage[_x][_y].possibleMoves[1][0][1]]])
                                else:
                                    possibleMoves[colourIndex].append([(_x, _y), Board.storage[_x][_y].possibleMoves[directionNum][positionNum]])
                        elif Board.storage[_x][_y].possibleMoves[directionNum][positionNum][0] != 'friendly':
                            if Board.storage[_x][_y].possibleMoves[directionNum][positionNum][0] == 'enemy':
                                possibleMoves[colourIndex].insert(0, [(_x, _y), Board.storage[_x][_y].possibleMoves[directionNum][positionNum]])
                            else:
                                possibleMoves[colourIndex].append([(_x, _y), Board.storage[_x][_y].possibleMoves[directionNum][positionNum]])
        possibleMoves = [[], []]
        for x in range(8):
            for y in range(8):
                if Board.storage[x][y] is not None:
                    if Board.storage[x][y].colour != Board.playerColour:
                        addMoves(0, x, y)
                    else:
                        addMoves(1, x, y) 
                   
        return possibleMoves

    def SelectRandomMove(moves):
        randNum = random.randint(0, len(moves)-1)
        return moves[randNum][1], moves[randNum][0][0], moves[randNum][0][1]
    
    def ScoringSystem(moves):
        # selects a move based soley of of which move corrosponds to the best position evaluation only looks one move ahead
        captureScore = {
            'pawn': 10,
            'knight': 30, 
            'bishop': 30,
            'rook': 50,
            'queen': 90,
        }
        num = 0 if Board.playerColour != 'white' else 1
        scores = []
        for turn in range(len(moves)):
            if moves[turn][1][0] == 'enemy':
                scores.append((-1 if num == 1 else 1) * captureScore[Board.storage[moves[turn][1][1][0]][moves[turn][1][1][1]].type])
            else:
                scores.append(0)

        indexConversion = ['pawn', 'knight', 'bishop', 'rook', 'queen', 'king']
        positionConversion = [7, 6, 5, 4, 3, 2, 1, 0]
        for turn in range(len(moves)):
            coord = moves[turn][1][1]
            scores[turn] += (-1 if num == 1 else 1) * Ai.locationScores[indexConversion.index(Board.storage[moves[turn][0][0]][moves[turn][0][1]].type)][coord[0] if Board.playerColour != 'white' else positionConversion[coord[0]]][coord[1]]   

        bestNum = min(scores) if Board.playerColour == 'white' else max(scores)
        maxScoreIndexes = []
        for turn in range(len(scores)):
            if scores[turn] == bestNum:
                maxScoreIndexes.append(turn)
        index = maxScoreIndexes[random.randint(0, len(maxScoreIndexes)-1)]
        
        return moves[index][1], moves[index][0][0], moves[index][0][1]
        
    def Move(move, x, y, real=True):
        # makes the move that the AI mode selects 
        # had to be converted from player make move function to work with Ai move format
        def MakeMove(castleNum=None, enpassant=None):
            if Board.playerTurn == 'black':
                Pieces.numberOfMoves += 1
            castleFixer = {  
                    (7, 7): 0,
                    (7, 0): 1,
                    (0, 7): 2,
                    (0, 0): 3
                }
                
            if castleFixer.get(move[1], None) is not None:
                Pieces.castlingControl[castleFixer[move[1]]] = False
                Board.storage[x][y].firstMove = False

            pieceTaken = False
            oldCoord = Board.storage[x][y].coord
            Pieces.previousMove = [oldCoord, move[1]]
            if castleNum is None and enpassant is None:
                Board.storage[x][y].coord = move[1]
                Board.storage[x][y].Update()
                pieceBeingTaken = Board.storage[move[1][0]][move[1][1]]
                if pieceBeingTaken is None:
                    Board.soundQueue.append(0)
                    if Board.storage[x][y].type == 'pawn':
                        Pieces.halfMoves = 0
                    else:
                        Pieces.halfMoves += 1
                else:
                    Board.soundQueue.append(1)
                    pieceTaken = True
                    Pieces.halfMoves = 0
                Board.storage[move[1][0]][move[1][1]
                                                ] = Board.storage[oldCoord[0]][oldCoord[1]]
                Board.storage[oldCoord[0]][oldCoord[1]] = None
            elif castleNum is not None:
                Pieces.halfMoves += 1
                Pieces.previousMove[1] = (oldCoord[0], oldCoord[1] + castleNum)
                newY = y + castleNum
                Board.storage[x][y].coord = (oldCoord[0], oldCoord[1] + castleNum)
                Board.storage[x][y].Update()
                Board.storage[x][newY] = Board.storage[oldCoord[0]][oldCoord[1]]
                Board.storage[oldCoord[0]][oldCoord[1]] = None
                Board.storage[oldCoord[0]][7 if castleNum == 2 else 0].coord = (x, newY - (castleNum//2))
                Board.storage[oldCoord[0]][7 if castleNum == 2 else 0].Update()
                Board.storage[x][newY - (castleNum//2)] = Board.storage[oldCoord[0]][7 if castleNum == 2 else 0]
                Board.storage[oldCoord[0]][7 if castleNum == 2 else 0] = None
                if real:
                    SideScreen.AddMove(Pieces.previousMove[1], '', Board.storage[x][newY].colour, None, False, 1 if cNum == 2 else 2)
                    Board.SetBoard('', resetting=True, resetFlip=False)
                return
            elif enpassant:
                Pieces.halfMoves = 0
                Board.storage[x][y].coord = move[1]
                Board.storage[x][y].Update()
                Board.soundQueue.append(1)
                pieceTaken = True
                Board.storage[move[1][0]][move[1][1]
                                                ] = Board.storage[oldCoord[0]][oldCoord[1]]
                Board.storage[oldCoord[0]][oldCoord[1]] = None
                Board.storage[oldCoord[0]][enpassant[1]] = None
            if real:
                SideScreen.AddMove(Pieces.previousMove[1], Board.storage[move[1][0]][move[1][1]].type, Board.storage[move[1][0]][move[1][1]].colour, Pieces.previousMove[0] if Board.storage[move[1][0]][move[1][1]].type == 'pawn' else None, pieceTaken)
                Board.SetBoard('', resetting=True, resetFlip=False)

        playerTurnReverser = {
            'white': 'black',
            'black': 'white'
        }
        promotionConverter ={
            'upgradequeen':7, 
            'upgradeknight':5,
            'upgradebishop':4,
            'upgraderook':6
        }
        # move = [movementname, pos to move to]
        if promotionConverter.get(move[0], None) is not None:
            Board.SetBoard('', resetting=True)
            Board.soundQueue.append(4)
            Board.piecesTaken[0 if Board.storage[x][y].colour == 'white' else 1].append(Board.storage[x][y].type)
            Board.storage[move[1][0]][move[1][1]] = Pieces(
                move[1], move[0][7::], Board.storage[x][y].colour, Pieces.pieceImages[promotionConverter[move[0]]+(3*(-1 if Board.storage[x][y].colour == 'white' else 1))])
            Board.playerTurn = playerTurnReverser[Board.playerTurn]
            Board.storage[x][y] = None
            return
        else:
            # move = [positionInfo ((None, 'enemy', 'forward1/2', 'castle'), (coord)), coord]
            if Board.storage[x][y].type == 'pawn':
                Board.storage[x][y].firstMove = False
                if move[0] == 'forward2':
                    Pieces.enPassant = Board.storage[x][y].EnpassantCheck((move[1][0] + (-1 if Board.storage[x][y].colour == 'black' else 1), move[1][0]))
                    MakeMove()
                    Board.playerTurn = playerTurnReverser[Board.playerTurn]
                    return
                else:
                    if move[0] == 'enpassant':
                        MakeMove(enpassant=Pieces.enPassant)
                        Board.playerTurn = playerTurnReverser[Board.playerTurn]
                        Pieces.enPassant = None
                        return
                    Pieces.enPassant = None

            elif Board.storage[x][y].type == 'king':
                cNum = None
                if move[0] == 'castleKingSide':
                    Board.soundQueue.append(2)
                    cNum = 2
                elif move[0] == 'castleQueenSide':
                    Board.soundQueue.append(2)
                    cNum = -2
                    
                if Board.storage[x][y].colour == 'white':
                    Pieces.castlingControl = [
                        False, False, Pieces.castlingControl[2], Pieces.castlingControl[3]]
                else:
                    Pieces.castlingControl = [
                        Pieces.castlingControl[0], Pieces.castlingControl[1], False, False]
                MakeMove(castleNum=cNum)
                Board.playerTurn = playerTurnReverser[Board.playerTurn]
                Board.soundQueue.append(0)
                
                Pieces.enPassant = None
                return

            elif Board.storage[x][y].type == 'rook' and Board.storage[x][y].firstMove:
                castleFixer = {  # change name
                    (7, 7): 0,
                    (7, 0): 1,
                    (0, 7): 2,
                    (0, 0): 3
                }
                try:
                    Pieces.castlingControl[castleFixer[Board.storage[x][y].coord]] = False
                except:
                    print(Board.storage[x][y].type, Board.storage[x][y].colour, Board.storage[x][y].coord)
                Board.storage[x][y].firstMove = False
            MakeMove()
            Board.playerTurn = playerTurnReverser[Board.playerTurn]
            Pieces.enPassant = None
            return

    def FortuneTeller():
        # uses a recursive algorithm to explore all possible moves to a given depth
        # uses a min max algorithm to select the best move
        # uses the alpha beta pruning and move ordering techniques to reduce time complexity
        def SeeInFuture(moves, fen, count, maximising, alpha, beta): # re-write this to work around evaluation
            pygame.event.pump() # to prevent crashing
            scores = []
            bestEval = math.inf * (1 if maximising else -1)

            for moveNum in range(len(moves)):
                Board.SetBoard(fen)
                Ai.Move(moves[moveNum][1], moves[moveNum][0][0], moves[moveNum][0][1], real=False)
                
                if False:
                    Window.DisplayWindow()
                    pygame.time.delay(300)
                
                Pieces.CalculateMoves(simulation=True)
                if Window.currentEvent != 'game':
                    if Window.currentEvent == 'checkmatewhite':
                        scores.append(max(900/(count+1), 200))
                    elif Window.currentEvent == 'checkmateblack':
                        scores.append(min(-900/(count+1), -200))
                    else:
                        scores.append(0)
                    Window.currentEvent = 'game'
                    continue
                elif count != Ai.depth-1:    
                    futureMoves = Ai.FormatMoves()[(count+1)%2]
                    eval = SeeInFuture(futureMoves, Board.BoardToFen(), count+1, not maximising, alpha, beta)
                    scores.append(eval)
                    if maximising:
                        bestEval = max(bestEval, eval)
                        alpha = max(alpha, eval)
                    else:
                        bestEval = min(bestEval, eval)
                        beta = min(beta, eval)
                    if beta <= alpha and True:
                        break
                else:
                    scores.append(Ai.EvaluationCalc(returning=True))

            if count != 0:
                _best = max(scores) if maximising else min(scores)
                return _best
            else:
                return scores

        def DetermineTheFuture(originalMoves, originalFen, maximising):
            scores = SeeInFuture(originalMoves, Board.BoardToFen(), 0, maximising, -math.inf, math.inf)
            
            Window.currentEvent = 'game'
            Board.SetBoard(originalFen)
            Pieces.CalculateMoves()

            best = max(scores) if maximising else min(scores)
            indexes = []
            for itemNum in range(len(scores)):
                if scores[itemNum] == best:
                    indexes.append(itemNum)   

            index = indexes[random.randint(0, len(indexes)-1)]
            return index    

        originalFen = Board.BoardToFen()
        
        #x = time.time()
        moveIndex = DetermineTheFuture(Ai.FormatMoves()[0], originalFen, maximising=(True if Board.playerColour == 'black' else False))
        Board.soundQueue = []
        #print(round(time.time()-x, 2))

        moveSelected = Ai.FormatMoves()[0][moveIndex]
        return moveSelected[1], moveSelected[0][0], moveSelected[0][1]


class BoardEditor:
    selectionIndex = None
    selectedEnPassant = None
    clicked = False
    enPassants = []
    
    ButtonRects = ((625, 110, 250, 450), (625, 30, 70, 70), # main big thing, player, ai, menu, settings, copy fen
                    (715, 30, 70, 70), (805, 30, 70, 70),
                    (855, 615, 45, 45), (640, 620, 80, 30),
                    (635, 480, 80, 70), (730, 480, 80, 70), # clear, starting pos, flip, W king side
                    (825, 480, 40, 70), (750, 242, 17, 17),
                    (850, 242, 17, 17), (750, 272, 17, 17),# W queen side, B king side, B queen side
                    (850, 272, 17, 17), (640, 150, 90, 40),
                    (760, 150, 90, 40), (650, 340, 90, 40),
                    (770, 340, 90, 40), (650, 400, 90, 40),
                    (770, 400, 90, 40))
    
    def Display():
        def DisplaySideScreen():
            def Enpassant():
                BoardEditor.enPassants = []
                for x in range(8):
                    for y in range(8):
                        if Board.storage[x][y] is not None and Board.storage[x][y].colour == Board.playerTurn and Board.storage[x][y].type == 'pawn':
                            if Board.storage[x][y].colour == 'white' and Board.storage[x][y].coord[0] == 3:
                                if y > 1 and Board.storage[x][y-1] is not None and Board.storage[x][y-1].type == 'pawn' and Board.storage[x][y-1].colour != Board.playerTurn:
                                    coord = Pieces.EnpassantConversion((x-1, y-1))
                                    if coord not in BoardEditor.enPassants:
                                        BoardEditor.enPassants.append(coord)
                                if y < 7 and Board.storage[x][y+1] is not None and Board.storage[x][y+1].type == 'pawn' and Board.storage[x][y+1].colour != Board.playerTurn:
                                    coord = Pieces.EnpassantConversion((x-1, y+1))
                                    if coord not in BoardEditor.enPassants:
                                        BoardEditor.enPassants.append(coord)
                            elif Board.storage[x][y].colour == 'black' and Board.storage[x][y].coord[0] == 4:
                                if y > 1 and Board.storage[x][y-1] is not None and Board.storage[x][y-1].type == 'pawn' and Board.storage[x][y-1].colour != Board.playerTurn:
                                    coord = Pieces.EnpassantConversion((x+1, y-1))
                                    if coord not in BoardEditor.enPassants:
                                        BoardEditor.enPassants.append(coord)
                                if y < 7 and Board.storage[x][y+1] is not None and Board.storage[x][y+1].type == 'pawn' and Board.storage[x][y+1].colour != Board.playerTurn:
                                    coord = Pieces.EnpassantConversion((x+1, y+1))
                                    if coord not in BoardEditor.enPassants:
                                        BoardEditor.enPassants.append(coord)
                            

            colour = Window.colours[7 if Window.TextColourIndex == 7 else 0]
            for rectIndex in range(len(BoardEditor.ButtonRects)):
                if rectIndex in (9 , 10, 11, 12) and Pieces.castlingControl[rectIndex-9]:# clear, starting pos, flip, W king side
                    if pygame.Rect(BoardEditor.ButtonRects[rectIndex]).collidepoint(mousePos):
                        pygame.draw.rect(screen, (165, 199, 100), BoardEditor.ButtonRects[rectIndex])
                    else:
                        pygame.draw.rect(screen, Window.colours[8], BoardEditor.ButtonRects[rectIndex])
                    pygame.draw.rect(screen, (50, 50, 50),BoardEditor.ButtonRects[rectIndex], 2)
                elif rectIndex in (15, 16, 17, 18):
                    if 0 < len(BoardEditor.enPassants) > rectIndex-15:
                        if BoardEditor.selectedEnPassant is None:
                            Window.DisplayText(25, 'Available', colour, (780, 325))

                        if pygame.Rect(BoardEditor.ButtonRects[rectIndex]).collidepoint(mousePos):
                            pygame.draw.rect(screen, (50, 50, 50), BoardEditor.ButtonRects[rectIndex])
                        if BoardEditor.enPassants[rectIndex-15] == BoardEditor.selectedEnPassant:
                            pygame.draw.rect(screen, (165, 199, 100),BoardEditor.ButtonRects[rectIndex], 2)
                        else:
                            pygame.draw.rect(screen, (50, 50, 50),BoardEditor.ButtonRects[rectIndex], 2)
                        Window.DisplayText(25, BoardEditor.enPassants[rectIndex-15], colour, (BoardEditor.ButtonRects[rectIndex][0]+45, BoardEditor.ButtonRects[rectIndex][1]+20))
                    continue
                elif pygame.Rect(BoardEditor.ButtonRects[rectIndex]).collidepoint(mousePos) and rectIndex != 0:# main big thing, player, ai, menu, settings, copy fen
                    pygame.draw.rect(screen, (50, 50, 50), BoardEditor.ButtonRects[rectIndex])
                else:
                    pygame.draw.rect(screen, (38, 36, 33), BoardEditor.ButtonRects[rectIndex])
                    pygame.draw.rect(screen, (50, 50, 50),BoardEditor.ButtonRects[rectIndex], 2)
                if rectIndex == 13 and Board.playerTurn == 'white' or rectIndex == 14 and Board.playerTurn == 'black' :
                    pygame.draw.rect(screen, Window.colours[8], BoardEditor.ButtonRects[rectIndex], 2)

            
            
            Window.DisplayText(30, 'Start in Mode:', Window.colours[Window.TextColourIndex], (700, 15))
            Window.DisplayText(30, 'Menu', colour, (840, 65))
            Window.DisplayText(30, 'AI', colour, (750, 65))
            Window.DisplayText(30, 'Player', colour, (660, 65))
            Window.DisplayText(15, 'Settings', colour, (877, 637))
            Window.DisplayText(20, 'Copy Fen', colour, (680, 635))

            ##### Side Block

            # Change Player Turn
            Window.DisplayText(25, 'Player Turn', colour, (680, 130))
            Window.DisplayText(25, 'White', colour, (685, 170))
            Window.DisplayText(25, 'Black', colour, (805, 170))

            # castling
            Window.DisplayText(30, 'Castling', colour, (680, 220))
            Window.DisplayText(25, 'White    O-O', colour, (690, 250))
            Window.DisplayText(25, 'Black    O-O', colour, (690, 280))
            Window.DisplayText(25, 'O-O-O', colour, (810, 250))
            Window.DisplayText(25, 'O-O-O', colour, (810, 280))

            # enpassant
            Window.DisplayText(27, 'En-Passant', colour, (685, 325))
            Enpassant()

            # clear board
            Window.DisplayText(30, 'Clear', colour, (675, 515))

            # starting position
            Window.DisplayText(25, 'Starting', colour, (770, 505))
            Window.DisplayText(25, 'position', colour, (770, 525))

            # flip
            Window.DisplayText(25, 'Flip', colour, (845, 515))

        def DisplayPieceChoices():
            screen.fill(Window.colours[0], (0, 600, 600, 60))
            for turn in range(12):
                image = Pieces.pieceImages[turn]

                screen.blit(pygame.transform.scale(image, (50, 50)), (turn*50, 605))
                #rect = (turn*50, 605, 50, 50)
                if BoardEditor.selectionIndex == turn:
                    pygame.draw.rect(screen, Window.colours[3], (turn*50, 600, 50, 60), 2)
                else:
                    pygame.draw.rect(screen, Window.colours[2], (turn*50, 600, 50, 60), 1)

            # piece deletion
            pygame.draw.rect(screen, Window.colours[0], (600, 625, 35, 35))
            if BoardEditor.selectionIndex == 12:
                pygame.draw.rect(screen, Window.colours[3], (600, 625, 35, 35), 2)
            else:
                pygame.draw.rect(screen, Window.colours[2], (600, 625, 35, 35), 1)
            Window.DisplayText(35, '!', Window.colours[2], (617, 642))

            # selection nulled
            pygame.draw.rect(screen, Window.colours[0], (600, 605, 35, 20))
            pygame.draw.rect(screen, Window.colours[2], (600, 605, 35, 20), 1)
        
        def DisplayPieceSelection():
            if BoardEditor.selectionIndex is not None and mousePos[0] < 600 and mousePos[1] < 600:
                if BoardEditor.selectionIndex != 12:
                    screen.blit(pygame.transform.scale(Pieces.pieceImages[BoardEditor.selectionIndex], (50, 50)), (mousePos[0]-25, mousePos[1]-25))
                else:
                    Window.DisplayText(35, '!', Window.colours[2], mousePos)

        def DisplayFen():
            fen = Board.BoardToFen()
            if len(fen) <= 60:
                pygame.draw.rect(screen, Window.colours[2], (615, 580, 270, 24), 2)
                Window.DisplayText(13, fen, Window.colours[Window.TextColourIndex], (620, 585), topLeft=True)
            else:
                fenSplit = fen.split(' ')
                pygame.draw.rect(screen, Window.colours[2], (615, 580, 270, 28), 2)
                if len(fen) <= 68:
                    Window.DisplayText(13, fenSplit[0], Window.colours[Window.TextColourIndex], (620, 585), topLeft=True)
                    Window.DisplayText(13, ' '.join(fenSplit[1::]), Window.colours[Window.TextColourIndex], (750, 597))
                else:
                    fen2Split = fenSplit[0].split('/')
                    num = ((len(fenSplit[0]) % 50) // 10)+1
                    Window.DisplayText(13, '/'.join(fen2Split[0:len(fen2Split)-num]) + '/', Window.colours[Window.TextColourIndex], (750, 587))
                    Window.DisplayText(13, '/'.join(fen2Split[len(fen2Split)-num::]) + ' ' + ' '.join(fenSplit[1::]), Window.colours[Window.TextColourIndex], (750, 597))

        if BoardEditor.selectionIndex is not None:
            BoardEditor.SelectionLogic()
        
        Board.DisplayBoard()

        DisplayPieceChoices()
        
        DisplayPieceSelection()
        
        DisplaySideScreen()

        DisplayFen()

    def Buttons():
        # piece deletion 
        if pygame.Rect((600, 625, 35, 35)).collidepoint(mousePos):
            BoardEditor.selectionIndex = 12
            return
        # selection nulled
        elif pygame.Rect((600, 605, 35, 20)).collidepoint(mousePos):
            BoardEditor.selectionIndex = None
            return

        for turn in range(12):
            if pygame.Rect((turn*50, 600, 50, 60)).collidepoint(mousePos):
                BoardEditor.selectionIndex = turn
                return
        
        for rectIndex in range(len(BoardEditor.ButtonRects)):
            if pygame.Rect(BoardEditor.ButtonRects[rectIndex]).collidepoint(mousePos) and rectIndex != 0:
                #player
                if rectIndex == 1:
                    Window.changingFen = Board.BoardToFen()
                    Window.currentMode = 'player'
                    Window.currentEvent = 'start'
                    Board.whiteName = 'White'
                    Board.blackName = 'Black'
                #AI
                elif rectIndex == 2:
                    Window.changingFen = Board.BoardToFen()
                    Window.currentMode = 'ai'
                    Window.currentEvent = 'start'
                    Board.whiteName = 'White'
                    Board.blackName = 'Ai'
                #Menu
                elif rectIndex == 3:
                    Window.currentMode = 'menu'
                #Settings
                elif rectIndex == 4:
                    Window.currentEvent = 'settings'
                #copy fen
                elif rectIndex == 5:
                    cb.copy(Board.BoardToFen())
                #Clear fen
                elif rectIndex == 6:
                    Board.SetBoard('8/8/8/8/8/8/8/8 w - - 0 1', resetFlip=False, resetMove=False)
                # starting position
                elif rectIndex == 7:
                    Board.SetBoard('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', resetFlip=False, resetMove=False)
                # flip board
                elif rectIndex == 8:
                    Board.boardFlipped = not Board.boardFlipped
                # white king side
                elif rectIndex == 9:
                    Pieces.castlingControl[0] = not Pieces.castlingControl[0]
                # white queen side
                elif rectIndex == 10:
                    Pieces.castlingControl[1] = not Pieces.castlingControl[1]
                # black king side
                elif rectIndex == 11:
                    Pieces.castlingControl[2] = not Pieces.castlingControl[2]
                # black queen side
                elif rectIndex == 12:
                    Pieces.castlingControl[3] = not Pieces.castlingControl[3]
                # change player turn to white
                elif rectIndex == 13:
                    Board.playerTurn = 'white'
                # change player turn to white
                elif rectIndex == 14:
                    Board.playerTurn = 'black'
                elif rectIndex in (15, 16, 17, 18):
                    if BoardEditor.selectedEnPassant == BoardEditor.enPassants[rectIndex-15]:
                        BoardEditor.selectedEnPassant = None
                    else:
                        BoardEditor.selectedEnPassant = BoardEditor.enPassants[rectIndex-15]
                    Pieces.enPassant = Pieces.EnpassantConversion(BoardEditor.selectedEnPassant) if BoardEditor.selectedEnPassant is not None else None


                if rectIndex not in (4, 5):
                    BoardEditor.selectionIndex = None
                    BoardEditor.clicked = False
                return

    def SelectionLogic():
        typeConverter = {
            0: ('white', 'pawn'),
            1: ('white', 'bishop'),
            2: ('white', 'knight'),
            3: ('white', 'rook'),
            4: ('white', 'queen'),
            5: ('white', 'king'),
            6: ('black', 'pawn'),
            7: ('black', 'bishop'),
            8: ('black', 'knight'),
            9: ('black', 'rook'),
            10: ('black', 'queen'),
            11: ('black', 'king')
        }
        pos = Board.GetCo_Ords()
        if BoardEditor.clicked and pos is not None:
            if BoardEditor.selectionIndex == 12:
                Board.storage[pos[0]][pos[1]] = None
                return
            
            info = typeConverter[BoardEditor.selectionIndex]
            
            if Board.storage[pos[0]][pos[1]] is None:
                Board.storage[pos[0]][pos[1]] = Pieces(pos, info[1], info[0], Pieces.pieceImages[BoardEditor.selectionIndex])
            elif not (Board.storage[pos[0]][pos[1]] is not None and Board.storage[pos[0]][pos[1]].type == info[1] and Board.storage[pos[0]][pos[1]].colour == info[0]):
                Board.storage[pos[0]][pos[1]] = Pieces(pos, info[1], info[0], Pieces.pieceImages[BoardEditor.selectionIndex])

class Tutorial:
    startingLevel = 0 #0 starting position, 1-6 piece movement, 7-15 is special cases, 16- is tactical
    level = 0
    title = ''
    message = []
    playerTurn = ''
    blocked = False
    movesNum = 0
    moveOrder = []

    previousFen = None
    moveIndex = 0
    playerSwitching = False

    def LevelOrganiser(incrementing=False):
        if incrementing:
            Tutorial.level += 1
        # TutorialData stores each level with: name of level#number of moves#player turn switching#fen#message(uses '\' to split between lines)#fens for required moves
        with open('TutorialData.txt', 'r') as file:
            levels = file.readlines()
            level = levels[Tutorial.level].strip()
            levelSplit = level.split('#')
            levelSplit[0] = levelSplit[0].split('\\')
            levelSplit[4] = levelSplit[4].split('\\')
            
            Board.SetBoard(levelSplit[3])
            Tutorial.previousFen = levelSplit[3]
            Tutorial.playerTurn = Board.playerTurn
            Tutorial.title = levelSplit[0]
            Tutorial.message = levelSplit[4]
            Tutorial.blocked = False
            Tutorial.movesNum = int(levelSplit[1])
            Tutorial.playerSwitching = bool(int(levelSplit[2]))
            Tutorial.moveOrder = levelSplit[5:]

    def Display():
        Board.DisplayBoard()

        colour = Window.colours[0]

        # title
        for titleIndex in range(len(Tutorial.title)):
            Window.DisplayText(40, Tutorial.title[titleIndex], colour, (750, 50+(20*titleIndex)))
        # message
        for lineIndex in range(len(Tutorial.message)):
            Window.DisplayText(25, Tutorial.message[lineIndex], colour, (620, 120+(20*lineIndex)), topLeft=True)
        # reset button
        if Tutorial.level != 0:
            pygame.draw.rect(screen, (50, 50, 50), (640, 460, 80, 40), (0 if pygame.Rect((640, 460, 80, 40)).collidepoint(mousePos) else 2))
            Window.DisplayText(24, 'Reset', colour, (680, 480))
        # next level button
        pygame.draw.rect(screen, (50, 50, 50), (770, 460, 80, 40), (0 if pygame.Rect((770, 460, 80, 40)).collidepoint(mousePos) else 2))
        Window.DisplayText(24, 'Continue', colour, (810, 480))
        # Menu
        pygame.draw.rect(screen, (50, 50, 50), (840, 600, 60, 60), (0 if pygame.Rect((840, 600, 60, 60)).collidepoint(mousePos) else 2))
        Window.DisplayText(30, 'Menu', colour, (870, 630))


        # easy level selection buttons
        pygame.draw.rect(screen, (50, 50, 50), (60, 610, 150, 40), (0 if pygame.Rect((60, 610, 150, 40)).collidepoint(mousePos) else 2))
        Window.DisplayText(24, 'Piece Movement', colour, (135, 630))
        pygame.draw.rect(screen, (50, 50, 50), (230, 610, 150, 40), (0 if pygame.Rect((230, 610, 150, 40)).collidepoint(mousePos) else 2))
        Window.DisplayText(24, 'Special Cases', colour, (305, 630))
        pygame.draw.rect(screen, (50, 50, 50), (400, 610, 150, 40), (0 if pygame.Rect((400, 610, 150, 40)).collidepoint(mousePos) else 2))
        Window.DisplayText(24, 'Tactics', colour, (475, 630))

    def Buttons():
        if pygame.Rect((770, 460, 80, 40)).collidepoint(mousePos): # continue
            Tutorial.LevelOrganiser(incrementing=True)
        elif pygame.Rect((640, 460, 80, 40)).collidepoint(mousePos) and Tutorial.level != 0: # reset
            Tutorial.LevelOrganiser()
        elif pygame.Rect((840, 600, 60, 60)).collidepoint(mousePos): # menu
            Window.currentMode = 'menu'
            Window.init()
            
        elif pygame.Rect((60, 610, 150, 40)).collidepoint(mousePos):
            Tutorial.level = 1
            Tutorial.LevelOrganiser(incrementing=False)
        elif pygame.Rect((230, 610, 150, 40)).collidepoint(mousePos):
            Tutorial.level = 7
            Tutorial.LevelOrganiser(incrementing=False)
        elif pygame.Rect((400, 610, 150, 40)).collidepoint(mousePos):
            Tutorial.level = 16
            Tutorial.LevelOrganiser(incrementing=False)

        if Tutorial.level == 1 and Board.storage[1][3] is not None:
            Tutorial.blocked = True
        if Tutorial.movesNum < 0:
            Tutorial.blocked = True


pygame.init()
screen = pygame.display.set_mode((900, 660))
pygame.display.set_caption('Chess.co.uk')
Window.init()
Board.init()

running = True
while running:
    mousePos = pygame.mouse.get_pos()
    for event in pygame.event.get():
        running = Window.EventLogic(event)

    Window.DisplayWindow()
    
    if (Pieces.pawnBeingUpgraded is None and Board.newMoveMade):
        Board.NewMoveLogic()
    else:
        Window.PlaySounds()   