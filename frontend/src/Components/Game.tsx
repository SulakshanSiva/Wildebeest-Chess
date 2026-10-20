import React from 'react'
import { TEXT } from '../Data/content'
import { CapturedPiece, Side } from '../Data/types'
import Board from './Board'
import Button from './Button'
import CapturedBar from './CapturedBar'
import Screen from './Screen'

interface GameProps {
  side: Side
  onResign: () => void
  onShowRules: () => void
  capturedByPlayer?: CapturedPiece[]
  capturedByOpponent?: CapturedPiece[]
}

// Nothing is captured until the board is connected to the game API.
const NO_CAPTURES: CapturedPiece[] = []

/**
 * The game screen: the board, a rules button top left and resign top right.
 *
 * @param side The colour the player chose.
 * @param onResign Called when the player resigns.
 * @param onShowRules Called when the player opens the rules popup.
 * @param capturedByPlayer Opposing pieces the player has taken, shown on the right.
 * @param capturedByOpponent The player's pieces the AI has taken, shown on the left.
 */
const Game = ({
  side,
  onResign,
  onShowRules,
  capturedByPlayer = NO_CAPTURES,
  capturedByOpponent = NO_CAPTURES,
}: GameProps) => (
  <Screen>
    <button
      type='button'
      onClick={onShowRules}
      aria-label={TEXT.game.showRules}
      className='absolute left-4 top-4 z-10 flex h-11 w-11 items-center justify-center rounded-full border-2 border-gold-light bg-felt/85 font-cinzel text-xl font-bold text-gold-light transition hover:bg-gold hover:text-ink focus:outline-none focus:ring-2 focus:ring-cream'
    >
      ?
    </button>
    <Button className='absolute right-4 top-4 z-10 !px-6 !py-2' onClick={onResign}>
      {TEXT.game.resign}
    </Button>

    <section className='game px-2 pb-6 pt-20 sm:pt-16'>
      <p className='mb-3 text-center text-xs font-semibold uppercase tracking-[0.35em] text-gold'>
        {TEXT.game.youPlay(side)}
      </p>
      <div className='game__layout'>
        <CapturedBar title={TEXT.game.capturedByOpponent} pieces={capturedByOpponent} placement='left' />
        <Board side={side} />
        <CapturedBar title={TEXT.game.capturedByYou} pieces={capturedByPlayer} placement='right' />
      </div>
    </section>
  </Screen>
)

export default Game
