import { act, fireEvent, render, screen, within } from '@testing-library/react'
import React from 'react'
import { createGame, resignGame, submitMove } from '../Api/client'
import { GameResponse, Move } from '../Api/types'
import { LAYOUT } from '../Data/layout'
import { layoutToBoard } from '../Logic/board'
import Game from './Game'

jest.mock('../Api/client', () => ({
  ...jest.requireActual('../Api/client'),
  createGame: jest.fn(),
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
})
