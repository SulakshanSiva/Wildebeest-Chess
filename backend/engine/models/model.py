# Global Imports
from pydantic import BaseModel

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
    