# Global Imports
from typing import List
# Local Imports
from backend.engine.pieces.piece import Piece
from backend.engine.models.model import Move

class BeeKeeper(Piece):
    def getAllLegalMoves(self):
        moves: List[Move] = []
        
        # Define all 8 directions
        offsets = [
            (1, 0), (-1, 0), (0, 1), (0, -1), 
            (1, 1), (1, -1), (-1, 1), (-1, -1),
        ]

        # Loop through all possible movement
        for dx, dy in offsets:
            # Update position
            dest_x = self.x + dx
            dest_y = self.y + dy
            
            # If square exists on the board
            if not self.isSquareOutOfBounds(dest_x, dest_y):
                # If moving onto an existing square on the board
                if self.isSquareFree(dest_x, dest_y):
                    # Define potential move
                    moves.append(Move(src_x=self.x, src_y=self.y, dest_x=dest_x, dest_y=dest_y))
                # If piece can be captured
                elif self.isCaptureValid(dest_x, dest_y):
                    # Define potential move
                    moves.append(Move(src_x=self.x, src_y=self.y, dest_x=dest_x, dest_y=dest_y))

        return moves
