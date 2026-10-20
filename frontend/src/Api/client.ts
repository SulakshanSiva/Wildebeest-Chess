import { Side } from '../Data/types'
import { API_BASE_URL } from './config'
import { GameResponse, Move } from './types'

/**
 * An error response from the backend, carrying its stable error code.
 */
export class ApiError extends Error {
  readonly status: number
  readonly code: string

  /**
   * Builds the error from the backend's error envelope.
   *
   * @param status The HTTP status code.
   * @param code The backend's machine-readable error code, for example "StaleVersionError".
   * @param message The backend's human-readable explanation.
   */
  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST'
  body?: unknown
  signal?: AbortSignal
}

/**
 * Sends one request to the game API and reads the game it returns.
 *
 * @param path The route under the API prefix, for example "/games".
 * @param options The method, an optional JSON body, and a signal to cancel the request.
 * @returns The game as the backend now has it.
 */
const request = async (path: string, { method = 'GET', body, signal }: RequestOptions = {}): Promise<GameResponse> => {
  // Only send a content type with a body, so a bodiless request stays a simple CORS request.
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    signal,
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const payload = await response.json().catch(() => null)

  if (!response.ok) {
    const error = payload?.error
    throw new ApiError(response.status, error?.code ?? 'UnknownError', error?.message ?? `Request failed (${response.status})`)
  }
  return payload as GameResponse
}

/**
 * Starts a game against the AI.
 *
 * @param side The colour the person plays.
 * @param signal Cancels the request.
 * @returns The new game, including the AI's first move when the person plays Black.
 */
export const createGame = (side: Side, signal?: AbortSignal) =>
  request('/games', { method: 'POST', body: { human_color: side }, signal })

/**
 * Fetches a game as it stands, to recover after a failed request.
 *
 * @param gameId The game to fetch.
 * @param signal Cancels the request.
 * @returns The game.
 */
export const getGame = (gameId: string, signal?: AbortSignal) =>
  request(`/games/${encodeURIComponent(gameId)}`, { signal })

/**
 * Plays the person's move. The AI replies within the same request.
 *
 * @param game The game as last received, whose version the move was chosen against.
 * @param move One of the game's legal moves.
 * @param signal Cancels the request.
 * @returns The game after the person's move and the AI's reply.
 */
export const submitMove = (game: GameResponse, move: Move, signal?: AbortSignal) =>
  request(`/games/${encodeURIComponent(game.game_id)}/moves`, {
    method: 'POST',
    body: {
      origin: move.origin,
      destination: move.destination,
      expected_version: game.version,
      // Always sent: it is what tells a Catapult fling apart from the passenger's own move.
      actor: move.actor,
    },
    signal,
  })

/**
 * Concedes the game to the AI.
 *
 * @param gameId The game to resign.
 * @param signal Cancels the request.
 * @returns The finished game.
 */
export const resignGame = (gameId: string, signal?: AbortSignal) =>
  request(`/games/${encodeURIComponent(gameId)}/resign`, { method: 'POST', signal })
