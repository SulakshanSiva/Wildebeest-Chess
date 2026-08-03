# Global Imports
from typing import List
# Local Imports
from .piece import Piece
from ..models.model import Move

class GrandEmpress(Piece):
    def getAllLegalMoves(self):
        moves: List[Move] = []
        
        # Define all possible Knight movements
        offsets = [
            (2, 1), (2, -1), (-2, 1), (-2, -1),
            (1, 2), (1, -2), (-1, 2), (-1, -2)
        ]

        # Loop through all possible movements
        for dx, dy in offsets:
            # Update position
            dest_x = self.x + dx
            dest_y = self.y + dy
            
            # If moving onto an existing square on the board
            if not self.isSquareOutOfBounds(dest_x, dest_y):
                # If the square does not have a piece on it
                if self.isSquareFree(dest_x, dest_y):
                    # Define potential move
                    moves.append(Move(src_x=self.x, src_y=self.y, dest_x=dest_x, dest_y=dest_y))

                # If the piece can be captured
                elif self.isCaptureValid(dest_x, dest_y):
                    # Define potential move
                    moves.append(Move(src_x=self.x, src_y=self.y, dest_x=dest_x, dest_y=dest_y))
                    
        # Define all possible Queen movements
        queen_directions = [
            (1, 0), (-1, 0), (0, 1), (0, -1), 
            (1, 1), (1, -1), (-1, 1), (-1, -1)
        ]
        
        # Loop through all possible movements
        for dx, dy in queen_directions:
            # Update position
            dest_x = self.x + dx
            dest_y = self.y + dy
            
            # Move until the edge of the board
            while not self.isSquareOutOfBounds(dest_x, dest_y):
                # If the square does not have a piece on it
                if self.isSquareFree(dest_x, dest_y):
                    # Define potential move
                    moves.append(Move(src_x=self.x, src_y=self.y, dest_x=dest_x, dest_y=dest_y))
                    
                    # Continue moving in the same direction
                    dest_x += dx
                    dest_y += dy
                # If a piece can be captured
                elif self.isCaptureValid(dest_x, dest_y):
                    # Define potential move
                    moves.append(Move(src_x=self.x, src_y=self.y, dest_x=dest_x, dest_y=dest_y))

                    # Stop sliding after a capture
                    break
                # We are blocked
                else:
                    break
                
        return moves