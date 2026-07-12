# Global Imports
from typing import List
# Local Imports
from backend.engine.pieces.piece import Piece
from backend.engine.models.model import Move

class Pawn(Piece):
    def getAllLegalMoves(self):
        moves: List[Move] = []
        
        # Get the direction of movement
        direction = self.getDirection()
        
        # If the pawn can move 2 forward
        if(self.first_move_complete == False): 
            # Update position
            dest_x = self.x + (2 * direction)
            stepx = self.x + (1 * direction)
            
            # If the pawn has a clear path
            if(self.isSquareFree(stepx, self.y) and self.isSquareFree(dest_x, self.y)):
                # Define potential move
                moves.append(Move(src_x=self.x, src_y=self.y, dest_x=dest_x, dest_y=self.y))
                
        # Move the pawn 1 forward
        # Update position
        dest_x = self.x + (1 * direction)
        # If the space in front of the pawn is free
        if(self.isSquareFree(dest_x, self.y)):
            # Define potential move
            moves.append(Move(src_x=self.x, src_y=self.y, dest_x=dest_x, dest_y=self.y))

        # Check for left diagonal capture
        # Update position
        dest_x = self.x + (1 * direction)
        dest_y = self.y - 1
        if(self.isCaptureValid(dest_x, dest_y)):
            # Define potential move
            moves.append(Move(src_x=self.x, src_y=self.y, dest_x=dest_x, dest_y=dest_y))
            
        # Check for right diagonal capture
        # Update position
        dest_x = self.x + (1 * direction)
        dest_y = self.y + 1
        if(self.isCaptureValid(dest_x, dest_y)):
            # Define potential move
            moves.append(Move(src_x=self.x, src_y=self.y, dest_x=dest_x, dest_y=dest_y))
        
        return moves

        
        