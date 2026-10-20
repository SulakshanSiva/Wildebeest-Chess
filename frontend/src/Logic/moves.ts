import { Move, Square } from '../Api/types'
import { sameSquare, squareKey } from './board'

/**
 * Lists the legal moves a clicked piece can make.
 *
 * A piece is involved if it moves (the origin) or spends the turn (the actor). That way a
 * Catapult's flings show both when the Catapult and when the piece being flung is clicked.
 *
 * @param legalMoves The player's legal moves.
 * @param square The clicked square.
 * @returns The moves that piece takes part in.
 */
export const movesFor = (legalMoves: Move[], square: Square) =>
  legalMoves.filter((move) => sameSquare(move.origin, square) || sameSquare(move.actor, square))

/**
 * Groups moves by the square they end on, which is what the player clicks second.
 *
 * @param moves The moves to group.
 * @returns A map from destination key to the moves ending there. More than one means the
 *   player has to choose, for example between moving a piece and flinging it.
 */
export const groupByDestination = (moves: Move[]) => {
  const groups = new Map<string, Move[]>()
  for (const move of moves) {
    const key = squareKey(move.destination)
    groups.set(key, [...(groups.get(key) ?? []), move])
  }
  return groups
}
