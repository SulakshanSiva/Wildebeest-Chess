# Global Imports
from typing import List
# Local Imports
from backend.engine.pieces.piece import Piece
from backend.engine.models.model import Move

class TimeMachine(Piece):
    def getAllLegalMoves(self):
        # Time machine cannot move or capture
        moves: List[Move] = []
        # Return no moves
        return moves
        