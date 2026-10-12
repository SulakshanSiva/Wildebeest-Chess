# Global Imports
from dataclasses import dataclass, field

# Local Imports
from .models.model import starting_board
from .pieces.pawn import Pawn
from .pieces.bishop import Bishop
from .pieces.knight import Knight
from .pieces.rook import Rook
from .pieces.king import King
from .pieces.jet_pack_king import JetPackKing
from .pieces.joey import Joey
from .pieces.time_machine import TimeMachine
from .pieces.serpent import Serpent
from .pieces.old_woman import OldWoman
from .pieces.grand_empress import GrandEmpress
from .pieces.golf_cart import GolfCart
from .pieces.beekeeper import BeeKeeper
from .pieces.gorilla import Gorilla
from .pieces.catapult import Catapult
from .pieces.piece import Piece

PIECE_REGISTRY = {
    "P": Pawn, "p": Pawn,
    "B": Bishop, "b": Bishop,
    "N": Knight, "n": Knight,
    "R": Rook, "r": Rook,
    "K": King, "k": King,
    "W": JetPackKing, "w": JetPackKing,
    "J": Joey, "j": Joey,
    "H": TimeMachine, "h": TimeMachine,
    "S": Serpent, "s": Serpent,
    "O": OldWoman, "o": OldWoman,
    "E": GrandEmpress, "e": GrandEmpress,
    "X": GolfCart, "x": GolfCart,
    "Z": BeeKeeper, "z": BeeKeeper,
    "G": Gorilla, "g": Gorilla,
    "C": Catapult, "c": Catapult,
}

@dataclass
class Board:
    board_state: list[list[Piece | str]] = field(default_factory=list)
    rows: int = 11
    cols: int = 11
    curr_player: str = "B"
    
    def initialize_board(self):
        self.board_state = [
            list(row)
            for row in starting_board.strip().splitlines()
        ]
    
        # Loop through all squares on the board
        for row in range(self.rows):
            for col in range(self.cols):
                # Get character
                character = self.board_state[row][col]

                # If not a piece, skip
                if(character == "." or character == "#" or character == "*"):
                    continue
                    
                color = "W" if character.isupper() else "B"
                piece_class = PIECE_REGISTRY[character]
                piece = piece_class(x=row, y=col, player_color=color)

                self.board_state[row][col] = piece

    def __str__(self) -> str:
        board_string = ""

        # Write the current player's move
        if self.curr_player == "W":
            board_string += "B\n"
        else:
            board_string += "W\n"

        # Write the state of the board
        for row in self.board_state:
            board_string += "".join(str(item) for item in row) + "\n"

        board_string += f"{self.total_time}\n"
        board_string += f"{self.move_count}\n"

        return board_string
