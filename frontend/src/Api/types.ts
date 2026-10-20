import { Side } from '../Data/types'

// These mirror backend/api/schemas/games.py, so field names keep the backend's snake_case.

export type Terrain = 'normal' | 'jet_pack' | 'transporter_pad'
export type GameStatus = 'active' | 'white_wins' | 'black_wins' | 'draw'
export type EndReason = 'king_captured' | 'resignation' | 'no_legal_moves'
export type MoveAction = 'move' | 'capture' | 'push' | 'crush' | 'fling'

export interface Square {
  row: number
  column: number
}

export interface Piece {
  id: number
  kind: string
  color: Side
  symbol: string
}

export interface Cell {
  terrain: Terrain
  piece: Piece | null
}

// Rows of cells, row 0 (White's back row) first.
export type BoardCells = Cell[][]

export interface Move {
  actor: Square
  origin: Square
  destination: Square
  action: MoveAction
}

export interface PieceRef {
  id: number
  kind: string
}

export interface Turn {
  ply: number
  side: Side
  move: Move
  captured: PieceRef[]
  promoted: PieceRef[]
}

export interface GameResponse {
  game_id: string
  version: number
  status: GameStatus
  end_reason: EndReason | null
  side_to_move: Side
  human_color: Side
  board: BoardCells
  legal_moves: Move[]
  turns: Turn[]
}
