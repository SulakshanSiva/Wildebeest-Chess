import { GameStatus } from '../Api/types'
import { Side } from '../Data/types'

export type Outcome = 'win' | 'lose' | 'draw'

/**
 * Turns the game's status into a result from the player's point of view.
 *
 * @param status The backend's game status.
 * @param humanColor The colour the player plays.
 * @returns Win, lose or draw, or null while the game is still being played.
 */
export const outcomeFor = (status: GameStatus, humanColor: Side): Outcome | null => {
  if (status === 'active') return null
  if (status === 'draw') return 'draw'

  const winner: Side = status === 'white_wins' ? 'white' : 'black'
  return winner === humanColor ? 'win' : 'lose'
}
