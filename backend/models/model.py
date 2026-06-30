from pydantic import BaseModel

class Move(BaseModel):
    src_x: int
    src_y: int
    dest_x: int
    dest_y: int