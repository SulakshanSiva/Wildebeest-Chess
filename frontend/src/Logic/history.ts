import { Piece, PieceRef, Turn } from '../Api/types'
import { TEXT } from '../Data/content'
import { PIECES } from '../Data/pieces'
import { Side } from '../Data/types'
import { opponentOf, squareName } from './board'

export type HistoryEventKind =
  | 'capture'
  | 'crush'
  | 'push'
  | 'fling'
  | 'poison'
  | 'power'
  | 'rampage'
  | 'teleport'
  | 'explosion'

export interface HistoryEvent {
  kind: HistoryEventKind
  text: string
}

export interface HistoryEntry {
  ply: number
  side: Side
  byPlayer: boolean
  summary: string
  events: HistoryEvent[]
}

const NAME_BY_KIND = new Map(PIECES.map((piece) => [piece.kind, piece.name]))

/**
 * Gives a piece kind's display name.
 *
 * @param kind The backend's piece kind, for example "golf_cart".
 * @returns The name used in the rules, for example "Golf Cart".
 */
const nameOf = (kind: string) => NAME_BY_KIND.get(kind) ?? kind

/**
 * Upper-cases the first letter, for a piece phrase that starts a sentence.
 *
 * @param text The phrase.
 * @returns The phrase with a capital first letter.
 */
const capitalise = (text: string) => text.charAt(0).toUpperCase() + text.slice(1)

/**
 * Joins phrases into an English list: "a", "a and b", "a, b and c".
 *
 * @param items The phrases.
 * @returns The joined list.
 */
export const listPhrases = (items: string[]) =>
  items.length <= 1 ? items.join('') : `${items.slice(0, -1).join(', ')} ${TEXT.history.and} ${items.at(-1)}`

/**
 * Merges repeated phrases into one with a count, keeping first-seen order.
 *
 * @param items The phrases, possibly repeated.
 * @returns Each distinct phrase once, as "your Pawn ×2" when it appeared twice.
 */
export const countRepeats = (items: string[]) => {
  const counts = new Map<string, number>()
  for (const item of items) counts.set(item, (counts.get(item) ?? 0) + 1)
  return Array.from(counts, ([item, count]) => (count > 1 ? TEXT.history.repeated(item, count) : item))
}

/**
 * Describes one played turn in plain language, from the player's point of view.
 *
 * The events follow the order the rules resolve them: the move's own capture or push, then
 * poison, promotions, a rampage, transporters and finally explosions.
 *
 * @param turn The turn as the backend reported it.
 * @param pieces Every piece known before the turn, by id, used to say whose piece is whose.
 * @param humanColor The colour the player plays.
 * @returns The turn's summary line and the events beneath it.
 */
export const describeTurn = (turn: Turn, pieces: Map<number, Piece>, humanColor: Side): HistoryEntry => {
  // Whose a piece is: from the board before the turn, or else the side that did not move.
  const ownerOf = (id: number): Side => pieces.get(id)?.color ?? opponentOf(turn.side)
  const phrase = (ref: PieceRef) =>
    ownerOf(ref.id) === humanColor ? TEXT.history.yourPiece(nameOf(ref.kind)) : TEXT.history.aiPiece(nameOf(ref.kind))
  const phrases = (refs: PieceRef[]) => listPhrases(countRepeats(refs.map(phrase)))
  const removedBy = (cause: string) => turn.captured.filter((removed) => removed.cause === cause)

  const { move } = turn
  const events: HistoryEvent[] = []

  for (const victim of removedBy('capture')) events.push({ kind: 'capture', text: TEXT.history.captured(phrase(victim)) })
  for (const victim of removedBy('crush')) events.push({ kind: 'crush', text: TEXT.history.crushed(phrase(victim)) })
  if (turn.displaced) {
    // A Gorilla steps one square, so the pushed piece lands one more step the same way.
    const pushedTo = {
      row: 2 * move.destination.row - move.origin.row,
      column: 2 * move.destination.column - move.origin.column,
    }
    events.push({ kind: 'push', text: TEXT.history.pushed(phrase(turn.displaced), squareName(pushedTo)) })
  }
  if (move.action === 'fling') events.push({ kind: 'fling', text: TEXT.history.flung(squareName(move.actor)) })
  for (const victim of removedBy('fling')) events.push({ kind: 'fling', text: TEXT.history.flungOnto(phrase(victim)) })

  for (const victim of removedBy('poison')) events.push({ kind: 'poison', text: TEXT.history.poisoned(phrase(victim)) })

  for (const promoted of turn.promoted) {
    const before = pieces.get(promoted.id)
    const piece = capitalise(phrase({ id: promoted.id, kind: before?.kind ?? promoted.kind }))
    const describe = TEXT.history.became[promoted.kind]
    events.push({
      kind: 'power',
      text: describe ? describe(piece) : TEXT.history.becameOther(piece, nameOf(promoted.kind)),
    })
  }

  const rampaged = removedBy('rampage')
  if (rampaged.length > 0) events.push({ kind: 'rampage', text: TEXT.history.rampage(phrases(rampaged)) })

  for (const journey of turn.transported) {
    events.push({
      kind: 'teleport',
      text: TEXT.history.teleported(phrase(journey), squareName(journey.origin), squareName(journey.destination)),
    })
  }

  const exploded = removedBy('explosion')
  const joeys = exploded.filter((removed) => removed.kind === 'joey')
  const caught = exploded.filter((removed) => removed.kind !== 'joey')
  if (joeys.length > 0) {
    const joey = capitalise(phrases(joeys))
    events.push({
      kind: 'explosion',
      text: caught.length > 0 ? TEXT.history.explodedTaking(joey, phrases(caught)) : TEXT.history.exploded(joey),
    })
  }

  return {
    ply: turn.ply,
    side: turn.side,
    byPlayer: turn.side === humanColor,
    summary: TEXT.history.moved(nameOf(turn.piece.kind), squareName(move.origin), squareName(move.destination)),
    events,
  }
}
