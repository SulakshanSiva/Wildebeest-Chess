import { Move } from '../Api/types'
import { LAYOUT } from '../Data/layout'
import { applyMoveLocally, layoutToBoard, orientRows, pieceAt, squareName } from './board'

const start = layoutToBoard(LAYOUT)

/**
 * Builds a move where the moving piece also spends the turn.
 *
 * @param from Origin as [row, column].
 * @param to Destination as [row, column].
 * @param action The move's action.
 * @returns The move.
 */
const move = (from: [number, number], to: [number, number], action: Move['action'] = 'move'): Move => ({
  actor: { row: from[0], column: from[1] },
  origin: { row: from[0], column: from[1] },
  destination: { row: to[0], column: to[1] },
  action,
})

describe('layoutToBoard', () => {
  it('reads pieces with their colour and kind', () => {
    expect(pieceAt(start, { row: 0, column: 0 })).toMatchObject({ kind: 'rook', color: 'white', symbol: 'R' })
    expect(pieceAt(start, { row: 10, column: 5 })).toMatchObject({ kind: 'king', color: 'black', symbol: 'k' })
  })

  it('reads terrain squares as empty', () => {
    expect(start[3][1]).toEqual({ terrain: 'transporter_pad', piece: null })
    expect(start[5][5]).toEqual({ terrain: 'jet_pack', piece: null })
  })
})

describe('orientRows', () => {
  it('puts A1 bottom-left for White', () => {
    const rows = orientRows(start, 'white')
    expect(squareName(rows[10][0].square)).toBe('A1')
    expect(squareName(rows[0][10].square)).toBe('K11')
  })

  it('turns the board round for Black', () => {
    const rows = orientRows(start, 'black')
    expect(squareName(rows[10][0].square)).toBe('K11')
    expect(squareName(rows[0][10].square)).toBe('A1')
  })
})

describe('applyMoveLocally', () => {
  it('moves a piece and leaves the origin empty', () => {
    const after = applyMoveLocally(start, move([1, 1], [3, 1]))
    expect(pieceAt(after, { row: 1, column: 1 })).toBeNull()
    expect(pieceAt(after, { row: 3, column: 1 })?.kind).toBe('pawn')
    // The terrain under the destination is kept.
    expect(after[3][1].terrain).toBe('transporter_pad')
  })

  it('replaces the occupant on a capture', () => {
    const after = applyMoveLocally(start, move([1, 1], [9, 1], 'capture'))
    expect(pieceAt(after, { row: 9, column: 1 })).toMatchObject({ kind: 'pawn', color: 'white' })
  })

  it('shoves the occupant one square further on a push', () => {
    const after = applyMoveLocally(start, move([1, 0], [1, 1], 'push'))
    expect(pieceAt(after, { row: 1, column: 1 })?.kind).toBe('gorilla')
    expect(pieceAt(after, { row: 1, column: 2 })?.kind).toBe('pawn')
  })

  it('leaves the Catapult in place on a fling', () => {
    const fling: Move = {
      actor: { row: 0, column: 8 },
      origin: { row: 0, column: 9 },
      destination: { row: 0, column: 7 },
      action: 'fling',
    }
    const after = applyMoveLocally(start, fling)
    expect(pieceAt(after, { row: 0, column: 8 })?.kind).toBe('catapult')
    expect(pieceAt(after, { row: 0, column: 7 })?.kind).toBe('knight')
    expect(pieceAt(after, { row: 0, column: 9 })).toBeNull()
  })

  it('does not change the board it was given', () => {
    applyMoveLocally(start, move([1, 1], [3, 1]))
    expect(pieceAt(start, { row: 1, column: 1 })?.kind).toBe('pawn')
  })
})
