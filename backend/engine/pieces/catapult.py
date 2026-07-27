# Global Imports
from typing import List
# Local Imports
from backend.engine.pieces.piece import Piece
from backend.engine.models.model import Move

class Catapult(Piece):
    def getAllLegalMoves(self):
        moves: List[Move] = []
        
        # Define all 8 directions around the Catapult
        offsets = [
            (1, 0), (-1, 0), (0, 1), (0, -1), 
            (1, 1), (1, -1), (-1, 1), (-1, -1),
        ]

        from time_machine import TimeMachine
        from gorilla import Gorilla
        from king import King

        # Loop through all possible movement
        for dx, dy in offsets:
            # Update position
            dest_x = self.x + dx
            dest_y = self.y + dy
            
            # If moving onto an existing square on the board
            if not self.isSquareOutOfBounds(dest_x, dest_y):
                # If the square has no piece on it
                if self.isSquareFree(dest_x, dest_y):
                    # Define potential move
                    moves.append(Move(src_x=self.x, src_y=self.y, dest_x=dest_x, dest_y=dest_y))
                else:
                    # Get adjacent piece
                    adj_piece = self.board.board_state[dest_x][dest_y]
                    # If piece is a friendly
                    if isinstance(adj_piece, Piece) and adj_piece.player_color == self.player_color:
                        # If piece is not a time machine
                        if not isinstance(adj_piece, TimeMachine):
                            # Compute direction
                            fdx = self.x - dest_x
                            fdy = self.y - dest_y
                            
                            # Get square we are flinging to
                            lx = self.x + fdx
                            ly = self.y + fdy
                            
                            # Move until the edge of the baord
                            while not self.isSquareOutOfBounds(lx, ly):
                                # Get flung square
                                # TODO: put to working state
                                target = self.board.board_state[lx][ly]
                                
                                # If square has no piece on it
                                if self.isSquareFree(lx, ly):
                                    # Define potential move
                                    m = Move(src_x=dest_x, src_y=dest_y, dest_x=lx, dest_y=ly)
                                    m.isFlung = True
                                    moves.append(m)
                                # If square has a piece on it
                                else:
                                    # If opposing piece
                                    if target.player_color != self.player_color:
                                        is_flung_gorilla = isinstance(adj_piece, Gorilla)
                                        is_protected_target = isinstance(target, (King, Gorilla))
                                        # Fling if not a gorilla or if not capturing a King or Gorilla
                                        if is_flung_gorilla or not is_protected_target:
                                            # Define potential move
                                            m = Move(src_x=dest_x, src_y=dest_y, dest_x=lx, dest_y=ly)
                                            m.isFlung = True
                                            moves.append(m)
                                # Update move
                                lx += fdx
                                ly += fdy
        return moves

        