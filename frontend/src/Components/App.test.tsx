import { fireEvent, render, screen, within } from '@testing-library/react'
import React from 'react'
import { createGame } from '../Api/client'
import { GameResponse } from '../Api/types'
import { LAYOUT } from '../Data/layout'
import { layoutToBoard } from '../Logic/board'
import App from './App'

jest.mock('../Api/client', () => ({
  ...jest.requireActual('../Api/client'),
  createGame: jest.fn(),
}))
jest.mock('../Data/settings', () => ({ AI_MIN_THINKING_MS: 0 }))

const blackGame: GameResponse = {
  game_id: 'g1',
  version: 1,
  status: 'active',
  end_reason: null,
  side_to_move: 'black',
  human_color: 'black',
  board: layoutToBoard(LAYOUT),
  legal_moves: [],
  turns: [],
}

describe('App', () => {
  beforeEach(() => {
    jest.mocked(createGame).mockResolvedValue(blackGame)
  })

  it('opens the rules from the menu, shows a piece, and closes on Escape', () => {
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Rules' }))

    const rules = screen.getByRole('dialog', { name: 'Rules' })
    fireEvent.click(within(rules).getByRole('tab', { name: 'Gorilla' }))
    expect(within(rules).getByRole('heading', { name: 'Gorilla' })).toBeInTheDocument()

    fireEvent.keyDown(window, { key: 'Escape' })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('goes from Play to the colour choice to a game as that colour', async () => {
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Play' }))
    expect(screen.getByRole('heading', { name: 'Pick a colour' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /Black/ }))

    expect(await screen.findByText('You play black')).toBeInTheDocument()
    expect(createGame).toHaveBeenCalledWith('black', expect.anything())
  })

  it('opens the rules from the game’s question mark button', async () => {
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Play' }))
    fireEvent.click(screen.getByRole('button', { name: /White/ }))

    fireEvent.click(await screen.findByRole('button', { name: 'Show rules' }))
    expect(screen.getByRole('dialog', { name: 'Rules' })).toBeInTheDocument()
  })
})
