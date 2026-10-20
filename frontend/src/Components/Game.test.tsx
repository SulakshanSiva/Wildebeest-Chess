import { act, fireEvent, render, screen, within } from '@testing-library/react'
import React from 'react'
import { ApiError, createGame, getGame, resignGame, submitMove } from '../Api/client'
import { GameResponse, Move } from '../Api/types'
import { LAYOUT } from '../Data/layout'
import { layoutToBoard } from '../Logic/board'
import Game from './Game'

jest.mock('../Api/client', () => ({
  ...jest.requireActual('../Api/client'),
  createGame: jest.fn(),
  getGame: jest.fn(),
  submitMove: jest.fn(),
  resignGame: jest.fn(),
}))
// No artificial thinking delay in tests.
jest.mock('../Data/settings', () => ({ AI_MIN_THINKING_MS: 0 }))

const pawnStep: Move = { actor: { row: 1, column: 1 }, origin: { row: 1, column: 1 }, destination: { row: 2, column: 1 }, action: 'move' }
const pawnDouble: Move = { ...pawnStep, destination: { row: 3, column: 1 } }

/**
 * Builds a game response on the starting board.
 *
 * @param overrides Fields to change.
 * @returns The response.
 */
const gameResponse = (overrides: Partial<GameResponse> = {}): GameResponse => ({
  game_id: 'g1',
  version: 0,
  status: 'active',
  end_reason: null,
  side_to_move: 'white',
  human_color: 'white',
  board: layoutToBoard(LAYOUT),
  legal_moves: [pawnStep, pawnDouble],
  turns: [],
  ...overrides,
})

/**
 * Renders the game screen as White and waits for the game to be created.
 */
const renderGame = async () => {
  render(<Game side='white' onExit={jest.fn()} onPlayAgain={jest.fn()} onShowRules={jest.fn()} />)
  expect(await screen.findByText('Your move')).toBeInTheDocument()
}

describe('Game', () => {
  beforeEach(() => {
    jest.mocked(createGame).mockResolvedValue(gameResponse())
  })

  it('highlights the squares a clicked piece can move to', async () => {
    await renderGame()
    fireEvent.click(screen.getByRole('button', { name: 'B2, white Pawn' }))

    expect(screen.getByRole('button', { name: 'B2, white Pawn, selected' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'B3, possible move' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'B4, transporter pad, possible move' })).toBeInTheDocument()
  })

  it('shows the AI thinking until its reply arrives', async () => {
    let reply: (game: GameResponse) => void = () => undefined
    jest.mocked(submitMove).mockReturnValue(new Promise((resolve) => (reply = resolve)))
    await renderGame()

    fireEvent.click(screen.getByRole('button', { name: 'B2, white Pawn' }))
    fireEvent.click(screen.getByRole('button', { name: 'B3, possible move' }))

    expect(screen.getByText('AI is thinking')).toBeInTheDocument()
    // The player's move is drawn straight away.
    expect(screen.getByRole('button', { name: /^B3, white Pawn/ })).toBeDisabled()

    await act(async () => reply(gameResponse({ version: 2 })))
    expect(screen.getByText('Your move')).toBeInTheDocument()
  })

  it('adds each played turn to the history', async () => {
    jest.mocked(submitMove).mockResolvedValue(
      gameResponse({
        version: 2,
        turns: [
          { ply: 0, side: 'white', move: pawnStep, piece: { id: 13, kind: 'pawn' }, displaced: null, captured: [], promoted: [], transported: [] },
        ],
      }),
    )
    await renderGame()
    expect(screen.getByText('No moves yet')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'B2, white Pawn' }))
    fireEvent.click(screen.getByRole('button', { name: 'B3, possible move' }))

    const history = await screen.findByRole('complementary', { name: 'History' })
    expect(await within(history).findByText('Pawn B2 → B3')).toBeInTheDocument()
  })

  it('announces a win at the end of the game', async () => {
    jest.mocked(submitMove).mockResolvedValue(
      gameResponse({ status: 'white_wins', end_reason: 'king_captured', legal_moves: [] }),
    )
    await renderGame()

    fireEvent.click(screen.getByRole('button', { name: 'B2, white Pawn' }))
    fireEvent.click(screen.getByRole('button', { name: 'B3, possible move' }))

    expect(await screen.findByRole('dialog', { name: 'You win!' })).toBeInTheDocument()
    expect(screen.getByText('The AI’s King has fallen.')).toBeInTheDocument()
  })

  it('asks before resigning, then shows the loss', async () => {
    jest.mocked(resignGame).mockResolvedValue(
      gameResponse({ status: 'black_wins', end_reason: 'resignation', legal_moves: [] }),
    )
    await renderGame()

    fireEvent.click(screen.getByRole('button', { name: 'Resign' }))
    const confirm = screen.getByRole('dialog', { name: 'Resign this game?' })
    expect(resignGame).not.toHaveBeenCalled()

    fireEvent.click(within(confirm).getByRole('button', { name: 'Resign' }))
    expect(await screen.findByRole('dialog', { name: 'You lose' })).toBeInTheDocument()
    expect(screen.getByText('You resigned the game.')).toBeInTheDocument()
  })

  it('asks which move was meant when two end on the same square', async () => {
    const step: Move = { actor: { row: 0, column: 8 }, origin: { row: 0, column: 8 }, destination: { row: 0, column: 9 }, action: 'move' }
    const fling: Move = { actor: { row: 0, column: 8 }, origin: { row: 0, column: 7 }, destination: { row: 0, column: 9 }, action: 'fling' }
    jest.mocked(createGame).mockResolvedValue(gameResponse({ legal_moves: [step, fling] }))
    jest.mocked(submitMove).mockResolvedValue(gameResponse({ version: 2 }))
    await renderGame()

    fireEvent.click(screen.getByRole('button', { name: 'I1, white Catapult' }))
    fireEvent.click(screen.getByRole('button', { name: 'J1, white Knight, possible move' }))

    const choice = screen.getByRole('dialog', { name: 'Choose a move' })
    expect(within(choice).getByRole('button', { name: 'Move the Catapult' })).toBeInTheDocument()
    fireEvent.click(within(choice).getByRole('button', { name: 'Fling the Bishop with the Catapult' }))

    expect(submitMove).toHaveBeenCalledWith(expect.anything(), fling, expect.anything())
    expect(await screen.findByText('Your move')).toBeInTheDocument()
  })

  it('shows a removed piece in its bar and in the history', async () => {
    const capture: Move = { ...pawnStep, destination: { row: 9, column: 1 }, action: 'capture' }
    jest.mocked(createGame).mockResolvedValue(gameResponse({ legal_moves: [capture] }))
    jest.mocked(submitMove).mockResolvedValue(
      gameResponse({
        version: 2,
        turns: [
          {
            ply: 0,
            side: 'white',
            move: capture,
            piece: { id: 13, kind: 'pawn' },
            displaced: null,
            // Id 24 is Black's B10 pawn in the starting layout.
            captured: [{ id: 24, kind: 'pawn', cause: 'capture' }],
            promoted: [],
            transported: [],
          },
        ],
      }),
    )
    await renderGame()

    fireEvent.click(screen.getByRole('button', { name: 'B2, white Pawn' }))
    fireEvent.click(screen.getByRole('button', { name: 'B10, black Pawn, possible move' }))

    const bar = await screen.findByRole('complementary', { name: 'Your captures' })
    expect(await within(bar).findByTitle('Pawn')).toBeInTheDocument()
    expect(screen.getByText('Captured the AI’s Pawn')).toBeInTheDocument()
  })

  it('offers a retry when the server cannot be reached, and recovers', async () => {
    jest.mocked(createGame).mockRejectedValueOnce(new TypeError('Failed to fetch'))
    render(<Game side='white' onExit={jest.fn()} onPlayAgain={jest.fn()} onShowRules={jest.fn()} />)

    expect(await screen.findByText('Could not reach the game server. Is the backend running?')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }))

    expect(await screen.findByText('Your move')).toBeInTheDocument()
    expect(createGame).toHaveBeenCalledTimes(2)
  })

  it('fetches the game again after a failed move', async () => {
    jest.mocked(submitMove).mockRejectedValueOnce(new TypeError('Failed to fetch'))
    jest.mocked(getGame).mockResolvedValue(gameResponse({ version: 0 }))
    await renderGame()

    fireEvent.click(screen.getByRole('button', { name: 'B2, white Pawn' }))
    fireEvent.click(screen.getByRole('button', { name: 'B3, possible move' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Try again' }))

    expect(await screen.findByText('Your move')).toBeInTheDocument()
    expect(getGame).toHaveBeenCalledWith('g1', expect.anything())
    // The failed move was undone: the pawn is back where it started.
    expect(screen.getByRole('button', { name: 'B2, white Pawn' })).toBeInTheDocument()
  })

  it('rings a Gorilla push in gold and a capture in red', async () => {
    const push: Move = { actor: { row: 1, column: 0 }, origin: { row: 1, column: 0 }, destination: { row: 1, column: 1 }, action: 'push' }
    const crush: Move = { actor: { row: 1, column: 0 }, origin: { row: 1, column: 0 }, destination: { row: 0, column: 0 }, action: 'crush' }
    jest.mocked(createGame).mockResolvedValue(gameResponse({ legal_moves: [push, crush] }))
    await renderGame()

    fireEvent.click(screen.getByRole('button', { name: 'A2, white Gorilla' }))

    expect(screen.getByRole('button', { name: 'B2, white Pawn, possible move' })).toHaveClass('game__square--push-target')
    expect(screen.getByRole('button', { name: 'A1, white Rook, possible move' })).toHaveClass('game__square--capture-target')
  })

  it('offers a new game when the server no longer has this one', async () => {
    jest.mocked(submitMove).mockRejectedValueOnce(new ApiError(404, 'GameNotFoundError', "No game with id 'g1'."))
    await renderGame()

    fireEvent.click(screen.getByRole('button', { name: 'B2, white Pawn' }))
    fireEvent.click(screen.getByRole('button', { name: 'B3, possible move' }))

    expect(await screen.findByText(/no longer on the server/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'New game' }))

    expect(await screen.findByText('Your move')).toBeInTheDocument()
    expect(createGame).toHaveBeenCalledTimes(2)
    expect(getGame).not.toHaveBeenCalled()
  })
})

