import { BoardCells, Cell, Move, Piece, Square, Terrain } from '../Api/types'
import { FILES, JET_PACK_CHAR, TRANSPORTER_CHAR } from '../Data/layout'
import { pieceForSymbol, sideOfSymbol } from '../Data/pieces'
import { Side } from '../Data/types'

export interface PlacedCell {
  square: Square
  cell: Cell
}

const TERRAIN_BY_CHAR: Record<string, Terrain> = {
  [TRANSPORTER_CHAR]: 'transporter_pad',
  [JET_PACK_CHAR]: 'jet_pack',
}

/**
 * Gives a square a string key, for use in maps and as a React key.
 *
 * @param square The square.
 * @returns A key such as "3,1".
 */
export const squareKey = (square: Square) => `${square.row},${square.column}`

/**
 * Says whether two squares are the same square.
 *
 * @param a The first square.
 * @param b The second square, or null.
 * @returns True when both name the same row and column.
 */
export const sameSquare = (a: Square, b: Square | null) => b !== null && a.row === b.row && a.column === b.column

/**
 * Names a square the way the board's coordinates label it.
 *
 * @param square The square.
 * @returns A name such as "G5".
 */
export const squareName = (square: Square) => `${FILES[square.column]}${square.row + 1}`

/**
 * Gives the other colour.
 *
 * @param side A colour.
 * @returns The opposing colour.
 */
export const opponentOf = (side: Side): Side => (side === 'white' ? 'black' : 'white')

/**
 * Reads the piece on a square.
 *
 * @param board The board.
 * @param square The square to read.
 * @returns The piece, or null when the square is empty.
 */
export const pieceAt = (board: BoardCells, square: Square): Piece | null => board[square.row][square.column].piece

/**
 * Puts the board's squares in display order with the player's side at the bottom.
 *
 * @param board Rows of cells, row 0 (White's back row) first.
 * @param side The colour the player chose.
 * @returns Rows from top to bottom, each square paired with its board position.
 */
export const orientRows = (board: BoardCells, side: Side): PlacedCell[][] => {
  const rows = board.map((cells, row) => cells.map((cell, column) => ({ square: { row, column }, cell })))
  // White sees row 0 at the bottom; Black sees the board turned round.
  return side === 'white' ? [...rows].reverse() : rows.map((line) => [...line].reverse())
}

/**
 * Builds a board from a text layout, shown while the real game is being created.
 *
 * @param layout Rows of layout characters, row 0 first.
 * @returns The board, with placeholder piece ids counting up from 1.
 */
export const layoutToBoard = (layout: string[]): BoardCells => {
  let nextId = 1
  return layout.map((line) =>
    line.split('').map((char): Cell => {
      const info = pieceForSymbol(char)
      if (!info) return { terrain: TERRAIN_BY_CHAR[char] ?? 'normal', piece: null }

      const piece = { id: nextId, kind: info.kind, color: sideOfSymbol(char), symbol: char }
      nextId += 1
      return { terrain: 'normal', piece }
    }),
  )
}

/**
 * Shows a move on the board straight away, before the server confirms it.
 *
 * Only the move itself is drawn. After-effects such as poison or transporters are left to the
 * server's reply, which replaces this board entirely.
 *
 * @param board The board before the move.
 * @param move One of the player's legal moves.
 * @returns A new board with the moving piece, and any pushed piece, relocated.
 */
export const applyMoveLocally = (board: BoardCells, move: Move): BoardCells => {
  const next = board.map((row) => [...row])
  const place = (square: Square, piece: Piece | null) => {
    next[square.row][square.column] = { ...next[square.row][square.column], piece }
  }

  // A Gorilla's push shoves the occupant one more square in the direction it stepped.
  if (move.action === 'push') {
    const pushedTo = {
      row: 2 * move.destination.row - move.origin.row,
      column: 2 * move.destination.column - move.origin.column,
    }
    place(pushedTo, pieceAt(board, move.destination))
  }

  // For a fling the origin is the flung piece, so the Catapult (the actor) stays put.
  const mover = pieceAt(board, move.origin)
  place(move.origin, null)
  place(move.destination, mover)
  return next
}
