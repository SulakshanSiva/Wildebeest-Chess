# Global Imports
from fastapi import FastAPI
from uuid import uuid4
# Local Imports
from engine.board import Board

app = FastAPI()
games: dict[str, Board] = {}

@app.post("/game")
async def start_game():
    # Create board
    board = Board()
    board.initialize_board()
    
    # Create game id
    game_id = uuid4()
    games[game_id] = board
    
    return {
        "game_id": game_id,
        "board": board
    }
    