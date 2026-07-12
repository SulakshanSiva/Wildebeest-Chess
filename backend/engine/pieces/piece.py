# Global Imports
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

@dataclass
class Piece(ABC):
    x: int
    y: int
    player_color: str
    opponent_color: str = field(init=False)
    maxRows: int = 11        
    maxCols: int = 11
    heuristic: int
    biological: bool = True
    
    def __post_init__(self):
        if(self.player_color == "W"):
            self.opponent_color = "B"
        else:
            self.opponent_color = "W"

    # Function to check if a square does not have a piece on it
    def isSquareFree(self, x, y):
        # If the square does not exist on the board
        if(self.isSquareOutOfBounds(x, y)):
            return False
        # If the square is empty
        if(self.board_state[x][y] == "." or self.board_state[x][y] == '#' or self.board_state[x][y] == '*'):
            return True
    
    # Function to check if a square exists on the board
    def isSquareOutOfBounds(self, x, y):
        # If bounds are outside of the board
        if(x < 0 or x >= self.maxRows or y < 0 or y >= self.maxCols):
            return True
        return False
    
    # Function to check if a piece capture can occur
    def isCaptureValid(self, x, y):
        # Check if the square is on the board
        if(self.isSquareOutOfBounds(x, y)):
            return False
        
        # Get piece to capture
        destPiece = self.board_state[x][y]
        # If the square contains a Piece
        if isinstance(destPiece, Piece):
            # If the piece is an opposing player's
            if destPiece.player_color != self.player_color:
                return True
            
    @abstractmethod
    # Function to get all valid moves
    def getAllLegalMoves(self):
        pass

    # Function to get a direction for a piece
    def getDirection(self):
        return 1 if self.player_color == "W" else -1
