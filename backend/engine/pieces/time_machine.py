# Global Imports
from typing import List
# Local Imports
from .piece import Piece
from ..models.model import Move

class TimeMachine(Piece):
    def getAllLegalMoves(self):
        # Time machine cannot move or capture
        moves: List[Move] = []
        # Return no moves
        return moves
        