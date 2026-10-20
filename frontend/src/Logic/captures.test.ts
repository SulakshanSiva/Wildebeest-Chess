import { Piece, Turn } from '../Api/types'
import { addCaptures, NO_CAPTURES } from './captures'

const turn = (side: Turn['side'], captured: Turn['captured']): Turn => ({
  ply: 0,
  side,
  move: { actor: { row: 0, column: 0 }, origin: { row: 0, column: 0 }, destination: { row: 1, column: 0 }, action: 'capture' },
  captured,
  promoted: [],
})

describe('addCaptures', () => {
  const known = new Map<number, Piece>([
    [7, { id: 7, kind: 'pawn', color: 'black', symbol: 'p' }],
    [3, { id: 3, kind: 'serpent', color: 'white', symbol: 'S' }],
  ])

  it('sorts removed pieces by their own colour', () => {
    const result = addCaptures(NO_CAPTURES, [turn('white', [{ id: 7, kind: 'pawn' }, { id: 3, kind: 'serpent' }])], known)
    expect(result.black).toEqual([{ id: 7, symbol: 'p' }])
    expect(result.white).toEqual([{ id: 3, symbol: 'S' }])
  })

  it('uses the kind at removal, not the kind on the old board', () => {
    const result = addCaptures(NO_CAPTURES, [turn('white', [{ id: 7, kind: 'time_machine' }])], known)
    expect(result.black).toEqual([{ id: 7, symbol: 'h' }])
  })

  it('falls back to the side that did not move for an unknown piece', () => {
    const result = addCaptures(NO_CAPTURES, [turn('black', [{ id: 99, kind: 'rook' }])], known)
    expect(result.white).toEqual([{ id: 99, symbol: 'R' }])
  })

  it('adds to the existing list without changing it', () => {
    const first = addCaptures(NO_CAPTURES, [turn('white', [{ id: 7, kind: 'pawn' }])], known)
    addCaptures(first, [turn('white', [{ id: 3, kind: 'serpent' }])], known)
    expect(first.white).toEqual([])
    expect(NO_CAPTURES.black).toEqual([])
  })
})
