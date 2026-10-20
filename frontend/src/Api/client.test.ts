import { ApiError, createGame, resignGame, submitMove } from './client'
import { GameResponse, Move } from './types'

const fetchMock = jest.fn()

beforeEach(() => {
  fetchMock.mockReset()
  global.fetch = fetchMock
})

/**
 * Makes fetch answer with one response.
 *
 * @param status The HTTP status.
 * @param body The JSON body.
 */
const respond = (status: number, body: unknown) => {
  fetchMock.mockResolvedValueOnce({ ok: status < 400, status, json: () => Promise.resolve(body) })
}

describe('game API client', () => {
  it('creates a game with the chosen colour', async () => {
    respond(201, { game_id: 'abc' })
    await createGame('black')

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('http://localhost:8000/api/v1/games')
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body)).toEqual({ human_color: 'black' })
  })

  it('sends the move with its actor and the game version', async () => {
    respond(200, {})
    const move: Move = { actor: { row: 0, column: 8 }, origin: { row: 0, column: 9 }, destination: { row: 0, column: 7 }, action: 'fling' }
    await submitMove({ game_id: 'abc', version: 4 } as GameResponse, move)

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('http://localhost:8000/api/v1/games/abc/moves')
    expect(JSON.parse(init.body)).toEqual({
      origin: move.origin,
      destination: move.destination,
      expected_version: 4,
      actor: move.actor,
    })
  })

  it('sends no body or content type to resign', async () => {
    respond(200, {})
    await resignGame('abc')

    const [, init] = fetchMock.mock.calls[0]
    expect(init.body).toBeUndefined()
    expect(init.headers).toBeUndefined()
  })

  it('turns the backend error envelope into an ApiError', async () => {
    respond(409, { error: { code: 'StaleVersionError', message: 'the game has moved on' } })

    await expect(resignGame('abc')).rejects.toEqual(
      expect.objectContaining({ status: 409, code: 'StaleVersionError', message: 'the game has moved on' }),
    )
    respond(409, { error: { code: 'StaleVersionError', message: 'x' } })
    await expect(resignGame('abc')).rejects.toBeInstanceOf(ApiError)
  })
})
