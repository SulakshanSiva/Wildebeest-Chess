# Global Imports
from typing import List
# Local Imports
from .piece import Piece
from ..models.model import Move

class GolfCart(Piece):
    def getAllLegalMoves(self):
        moves: List[Move] = []
        
        # Define movement type
        offsets = [(0, 1), (0, -1)]

        # Loop through all possible movement
        for dx, dy in offsets:
            # Update position
            dest_x = self.x + dx
            dest_y = self.y + dy
            
            # If moving onto an existing square on the board
            if not self.isSquareOutOfBounds(dest_x, dest_y):
                # If the square does not have a piece on it or can be captured
                if self.isSquareFree(dest_x, dest_y) or self.isCaptureValid(dest_x, dest_y):
                    # Define potential move
                    moves.append(Move(src_x=self.x, src_y=self.y, dest_x=dest_x, dest_y=dest_y))
                    
        return moves