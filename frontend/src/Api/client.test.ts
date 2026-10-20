import { ApiError, createGame, gamePath, resignGame, submitMove } from './client'
import { GameResponse, Move } from './types'

const fetchMock = jest.fn()
const GAME_ID = '0123456789abcdef0123456789abcdef'

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
    respond(201, { game_id: GAME_ID })
    await createGame('black')

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('http://localhost:8000/api/v1/games')
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body)).toEqual({ human_color: 'black' })
  })

  it('sends the move with its actor and the game version', async () => {
    respond(200, {})
    const move: Move = { actor: { row: 0, column: 8 }, origin: { row: 0, column: 9 }, destination: { row: 0, column: 7 }, action: 'fling' }
    await submitMove({ game_id: GAME_ID, version: 4 } as GameResponse, move)

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe(`http://localhost:8000/api/v1/games/${GAME_ID}/moves`)
    expect(JSON.parse(init.body)).toEqual({
      origin: move.origin,
      destination: move.destination,
      expected_version: 4,
      actor: move.actor,
    })
  })

  it('sends no body or content type to resign', async () => {
    respond(200, {})
    await resignGame(GAME_ID)

    const [, init] = fetchMock.mock.calls[0]
    expect(init.body).toBeUndefined()
    expect(init.headers).toBeUndefined()
  })

  it('turns the backend error envelope into an ApiError', async () => {
    respond(409, { error: { code: 'StaleVersionError', message: 'the game has moved on' } })

    await expect(resignGame(GAME_ID)).rejects.toEqual(
      expect.objectContaining({ status: 409, code: 'StaleVersionError', message: 'the game has moved on' }),
    )
    respond(409, { error: { code: 'StaleVersionError', message: 'x' } })
    await expect(resignGame(GAME_ID)).rejects.toBeInstanceOf(ApiError)
  })

  it('refuses a game id that is not the backend’s format, before any request', () => {
    expect(gamePath(GAME_ID, '/resign')).toBe(`/games/${GAME_ID}/resign`)
    for (const bad of ['..', '../healthz', `${GAME_ID}/../x`, 'ABCDEF0123456789ABCDEF0123456789', '']) {
      expect(() => gamePath(bad)).toThrow('invalid game id')
    }
    expect(() => resignGame('..')).toThrow()
    expect(fetchMock).not.toHaveBeenCalled()
  })
})
