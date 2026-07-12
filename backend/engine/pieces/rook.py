# Global Imports
from typing import List
# Local Imports
from backend.engine.pieces.piece import Piece
from backend.engine.models.model import Move

class Rook(Piece):
    def getAllLegalMoves(self):
        moves: List[Move] = []
        
        # Define all potential moves by direction
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        # Loop through all directions
        for dx, dy in directions:
            # Update position
            dest_x = self.x + dx
            dest_y = self.y + dy
            
            # Loop until we hit the edge of the board
            while not self.isSquareOutOfBounds(dest_x, dest_y):
                # If square does not have a piece on it
                if self.isSquareFree(dest_x, dest_y):
                    # Define potential move
                    moves.append(Move(src_x=self.x, src_y=self.y, dest_x=dest_x, dest_y=dest_y))
                else:
                    # If a capture can take place
                    if self.isCaptureValid(dest_x, dest_y):
                         # Define potential move
                        moves.append(Move(src_x=self.x, src_y=self.y, dest_x=dest_x, dest_y=dest_y))
                    # Stop moving if we have hit an obstacle
                    break
                # Move by 1 in the same direction
                dest_x += dx
                dest_y += dy
                
        return moves

