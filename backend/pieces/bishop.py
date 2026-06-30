from piece import Piece
from models import Move
from typing import List

class Bishop(Piece):
    def getAllLegalMoves(self):
        moves: List[Move] = []
        
        # The four diagonal directions
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]

        # Loop through all possible movement
        for dx, dy in directions:
            # Update position
            dest_x = self.x + dx
            dest_y = self.y + dy
            
            # Move until the edge of the board
            while not self.isSquareOutOfBounds(dest_x, dest_y):
                # If moving onto an existing square on the board
                if self.isSquareFree(dest_x, dest_y):
                    # Define potential move
                    moves.append(Move(src_x=self.x, src_y=self.y, dest_x=dest_x, dest_y=dest_y))
                else:
                    # If piece can be captured
                    if self.isCaptureValid(dest_x, dest_y):
                        # Define potential move
                        moves.append(Move(src_x=self.x, src_y=self.y, dest_x=dest_x, dest_y=dest_y))
                    # Stop moving if we have hit an obstacle
                    break
                # Move further along the diagonal
                dest_x += dx
                dest_y += dy
                
        return moves
