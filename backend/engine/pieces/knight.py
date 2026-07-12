# Global Imports
from typing import List
# Local Imports
from backend.engine.pieces.piece import Piece
from backend.engine.models import Move

class Knight(Piece):
    def getAllLegalMoves(self):
        moves: List[Move] = []
        
        # List of all possible L shape movements
        offsets = [
            (2, 1), (2, -1), (-2, 1), (-2, -1),
            (1, 2), (1, -2), (-1, 2), (-1, -2)
        ]
        
        # Loop through all possible movement
        for dx, dy in offsets:
            # Update position
            dest_x = self.x + dx
            dest_y = self.y + dy
            
            # If moving onto an existing square on the board
            if not self.isSquareOutOfBounds(dest_x, dest_y):
                # If the square is empty or if the piece on the square can be captured
                if self.isSquareFree(dest_x, dest_y) or self.isCaptureValid(dest_x, dest_y):
                    # Define potential move
                    moves.append(Move(src_x=self.x, src_y=self.y, dest_x=dest_x, dest_y=dest_y))
                    
        return moves
