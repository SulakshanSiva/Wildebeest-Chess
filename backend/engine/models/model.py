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
    
class Board(BaseModel):
    board_state: list[list[str]] = Field(default_factory=list)
    total_time: timedelta = Field(default=timedelta(minutes=10))
    move_count: int = Field(default=0)
    rows: int = Field(default=11)
    cols: int = Field(default=11)