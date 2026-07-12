from backend.engine.models.model import Board

def initialize_board(board: Board):
    # Loop through all squares on the board
    for row in board.rows:
        for col in board.cols:
            # Get character
            character = board.board_state[row][col]

            # If not a piece, skip
            if(character == "." or character == "#" or character == "*"):
                continue
            
            
