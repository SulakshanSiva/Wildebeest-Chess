from engine.models.model import Board, starting_board

def initialize_board(board: Board):
    board.board_state = [
        list(row)
        for row in starting_board.strip().splitlines()
    ]
    
    # Loop through all squares on the board
    for row in range(board.rows):
        for col in range(board.cols):
            # Get character
            character = board.board_state[row][col]

            # If not a piece, skip
            if(character == "." or character == "#" or character == "*"):
                continue
