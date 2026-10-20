import { BoardCells, Piece, Turn } from '../Api/types'
import { symbolForKind } from '../Data/pieces'
import { CapturedPiece, Side } from '../Data/types'
import { opponentOf } from './board'

// Removed pieces, grouped by the colour of the piece removed.
export type CapturedBySide = Record<Side, CapturedPiece[]>

export const NO_CAPTURES: CapturedBySide = { white: [], black: [] }

/**
 * Indexes every piece on a board by its id.
 *
 * @param board The board.
 * @returns A map from piece id to piece.
 */
export const piecesById = (board: BoardCells) => {
  const pieces = new Map<number, Piece>()
  for (const cell of board.flat()) {
    if (cell.piece) pieces.set(cell.piece.id, cell.piece)
  }
  return pieces
}

/**
 * Adds the pieces removed during some turns to the running list.
 *
 * The backend names a removed piece only by id and kind, so its colour is looked up on the
 * board from before the request. Pieces are never created mid-game, so every piece removed in
 * those turns was on that board.
 *
 * @param current The captures so far.
 * @param turns The turns the latest request played.
 * @param known Every piece on the board before those turns, by id.
 * @returns A new capture list including the new removals.
 */
export const addCaptures = (current: CapturedBySide, turns: Turn[], known: Map<number, Piece>): CapturedBySide => {
  const next: CapturedBySide = { white: [...current.white], black: [...current.black] }
  for (const turn of turns) {
    for (const removed of turn.captured) {
      // Fallback for a piece not on the known board: assume the side that moved took it.
      const color = known.get(removed.id)?.color ?? opponentOf(turn.side)
      next[color].push({ id: removed.id, symbol: symbolForKind(removed.kind, color) })
    }
  }
  return next
}
