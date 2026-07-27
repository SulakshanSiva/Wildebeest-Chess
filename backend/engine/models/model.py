# Global Imports
from pydantic import BaseModel, Field
from datetime import timedelta

starting_board = """
RNZBOKXBCNR
GPPSPJPPPPG
...........
.*.......*.
...........
.....#.....
...........
.*.......*.
...........
gppspjppppg
rnzbokxbcnr
"""

class Move(BaseModel):
    src_x: int
    src_y: int
    dest_x: int
    dest_y: int
    isFlung: bool = False
    
class Board(BaseModel):
    board_state: list[list[str]] = Field(default_factory=list)
    total_time: timedelta = Field(default=timedelta(minutes=10))
    move_count: int = Field(default=0)
    rows: int = Field(default=11)
    cols: int = Field(default=11)
    curr_player: str = Field(default="B")
    
    def __str__(self):
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