# Global Imports
from typing import List
# Local Imports
from backend.engine.pieces.piece import Piece
from backend.engine.models.model import Move

class Gorilla(Piece):
    def getAllLegalMoves(self):
        moves: List[Move] = []
        
        # Define all 8 possible movements
        offsets = [
            (1, 0), (-1, 0), (0, 1), (0, -1), 
            (1, 1), (1, -1), (-1, 1), (-1, -1),
        ]

        # Loop through all possible movement
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
                else:
                    # Get piece on destination square
                    occupant = self.board.board_state[dest_x][dest_y]
                    # Check if piece is a gorilla
                    if not isinstance(occupant, Gorilla):
                        # Calculate where the piece will be pushed
                        push_to_x = dest_x + dx
                        push_to_y = dest_y + dy
                        # Check if we are pushing off the board
                        if not self.isSquareOutOfBounds(push_to_x, push_to_y):
                            # Define potential move
                            moves.append(Move(src_x=self.x, src_y=self.y, dest_x=dest_x, dest_y=dest_y))

        return moves