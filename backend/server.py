# Global Imports
from fastapi import FastAPI
from uuid import uuid4
# Local Imports
from engine.models.model import Board
from engine.board import initialize_board

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/game")
async def start_game():
    board = Board()
    initialize_board(board)
    game_id = uuid4()
    return {
        "game_id": game_id,
        "board": board
    }
  
@app.post("/game/{game_id}/move")
async def move():
    return