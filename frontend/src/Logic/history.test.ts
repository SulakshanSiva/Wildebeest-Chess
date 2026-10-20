import { Move, Piece, Turn } from '../Api/types'
import { countRepeats, describeTurn, HistoryEntry, listPhrases } from './history'

const at = (row: number, column: number) => ({ row, column })

/**
 * Gives an entry's events without their ids, so expectations can list just kind and text.
 *
 * @param entry The described turn.
 * @returns Each event's kind and text.
 */
const eventsOf = (entry: HistoryEntry) => entry.events.map(({ kind, text }) => ({ kind, text }))

/**
 * Builds a turn with sensible defaults for anything not given.
 *
 * @param overrides Fields to change.
 * @returns The turn.
 */
const turn = (overrides: Partial<Turn>): Turn => ({
  ply: 0,
  side: 'white',
  move: { actor: at(0, 1), origin: at(0, 1), destination: at(2, 2), action: 'move' },
  piece: { id: 1, kind: 'knight' },
  displaced: null,
  captured: [],
  promoted: [],
  transported: [],
  ...overrides,
})

/**
 * Builds the known-piece index the describer looks colours up in.
 *
 * @param pieces Each piece as id, kind and colour.
 * @returns The index.
 */
const known = (...pieces: [number, string, Piece['color']][]) =>
  new Map<number, Piece>(pieces.map(([id, kind, color]) => [id, { id, kind, color, symbol: '' }]))

describe('describeTurn', () => {
  it('summarises a plain move with its squares', () => {
    const entry = describeTurn(turn({}), known([1, 'knight', 'white']), 'white')
    expect(entry.summary).toBe('Knight B1 → C3')
    expect(entry.byPlayer).toBe(true)
    expect(eventsOf(entry)).toEqual([])
  })

  it('names whose piece was captured from the player’s side', () => {
    const capture: Move = { actor: at(0, 1), origin: at(0, 1), destination: at(2, 2), action: 'capture' }
    const entry = describeTurn(
      turn({ move: capture, captured: [{ id: 9, kind: 'pawn', cause: 'capture' }] }),
      known([1, 'knight', 'white'], [9, 'pawn', 'black']),
      'white',
    )
    expect(eventsOf(entry)).toEqual([{ kind: 'capture', text: 'Captured the AI’s Pawn' }])
  })

  it('says where a Gorilla pushed a piece', () => {
    const push: Move = { actor: at(1, 0), origin: at(1, 0), destination: at(1, 1), action: 'push' }
    const entry = describeTurn(
      turn({ move: push, piece: { id: 1, kind: 'gorilla' }, displaced: { id: 2, kind: 'pawn' } }),
      known([1, 'gorilla', 'white'], [2, 'pawn', 'white']),
      'white',
    )
    expect(entry.summary).toBe('Gorilla A2 → B2')
    expect(eventsOf(entry)).toEqual([{ kind: 'push', text: 'Pushed your Pawn to C2' }])
  })

  it('names the Catapult behind a fling and what the flung piece landed on', () => {
    const fling: Move = { actor: at(0, 8), origin: at(0, 9), destination: at(9, 0), action: 'fling' }
    const entry = describeTurn(
      turn({ move: fling, captured: [{ id: 9, kind: 'rook', cause: 'fling' }] }),
      known([1, 'knight', 'white'], [9, 'rook', 'black']),
      'white',
    )
    expect(entry.summary).toBe('Knight J1 → A10')
    expect(eventsOf(entry)).toEqual([
      { kind: 'fling', text: 'Flung by the Catapult on I1' },
      { kind: 'fling', text: 'Landed on the AI’s Rook, capturing it' },
    ])
  })

  it('reports teleports and power-ups', () => {
    const entry = describeTurn(
      turn({
        side: 'black',
        piece: { id: 5, kind: 'king' },
        promoted: [{ id: 5, kind: 'jet_pack_king' }],
        transported: [{ id: 6, kind: 'rook', origin: at(3, 1), destination: at(7, 9) }],
      }),
      known([5, 'king', 'black'], [6, 'rook', 'black']),
      'white',
    )
    expect(entry.byPlayer).toBe(false)
    expect(eventsOf(entry)).toEqual([
      { kind: 'power', text: 'The AI’s King strapped on the jet pack' },
      { kind: 'teleport', text: 'Teleported the AI’s Rook B4 → J8' },
    ])
  })

  it('names the kind a pawn had before it became a Time Machine', () => {
    const entry = describeTurn(
      turn({ promoted: [{ id: 3, kind: 'time_machine' }] }),
      known([1, 'knight', 'white'], [3, 'pawn', 'white']),
      'white',
    )
    expect(eventsOf(entry)[0].text).toBe('Your Pawn reached the far row and became a Time Machine')
  })

  it('groups an explosion’s victims under the Joey that exploded', () => {
    const entry = describeTurn(
      turn({
        captured: [
          { id: 2, kind: 'joey', cause: 'explosion' },
          { id: 3, kind: 'king', cause: 'explosion' },
          { id: 4, kind: 'pawn', cause: 'explosion' },
        ],
      }),
      known([1, 'pawn', 'white'], [2, 'joey', 'white'], [3, 'king', 'white'], [4, 'pawn', 'black']),
      'white',
    )
    expect(eventsOf(entry)).toEqual([
      { kind: 'explosion', text: 'Your Prince Joey exploded, taking your King and the AI’s Pawn' },
    ])
  })

  it('orders effects as the rules resolve them, with rampage and poison named', () => {
    const entry = describeTurn(
      turn({
        captured: [
          { id: 7, kind: 'rook', cause: 'rampage' },
          { id: 8, kind: 'pawn', cause: 'poison' },
          { id: 9, kind: 'bishop', cause: 'rampage' },
        ],
      }),
      known([1, 'knight', 'white'], [7, 'rook', 'black'], [8, 'pawn', 'black'], [9, 'bishop', 'white']),
      'white',
    )
    expect(eventsOf(entry)).toEqual([
      { kind: 'poison', text: 'Poison took the AI’s Pawn' },
      { kind: 'rampage', text: 'A Golf Cart rampage destroyed the AI’s Rook and your Bishop' },
    ])
  })
})

describe('describeTurn event ids', () => {
  it('gives every event a distinct id, even when two lines read the same', () => {
    const entry = describeTurn(
      turn({ ply: 4, promoted: [{ id: 3, kind: 'time_machine' }, { id: 4, kind: 'time_machine' }] }),
      known([1, 'knight', 'white'], [3, 'pawn', 'white'], [4, 'pawn', 'white']),
      'white',
    )
    expect(entry.events[0].text).toBe(entry.events[1].text)
    expect(entry.events.map((event) => event.id)).toEqual(['4-0', '4-1'])
  })

  it('groups every poisoned piece into one line', () => {
    const entry = describeTurn(
      turn({
        captured: [
          { id: 8, kind: 'pawn', cause: 'poison' },
          { id: 9, kind: 'pawn', cause: 'poison' },
        ],
      }),
      known([1, 'knight', 'white'], [8, 'pawn', 'black'], [9, 'pawn', 'black']),
      'white',
    )
    expect(eventsOf(entry)).toEqual([{ kind: 'poison', text: 'Poison took the AI’s Pawn ×2' }])
  })
})

describe('countRepeats', () => {
  it('merges repeats into a count, keeping first-seen order', () => {
    expect(countRepeats(['your Pawn', 'your King', 'your Pawn'])).toEqual(['your Pawn ×2', 'your King'])
  })
})

describe('listPhrases', () => {
  it('joins lists the English way', () => {
    expect(listPhrases(['a'])).toBe('a')
    expect(listPhrases(['a', 'b'])).toBe('a and b')
    expect(listPhrases(['a', 'b', 'c'])).toBe('a, b and c')
  })
})
