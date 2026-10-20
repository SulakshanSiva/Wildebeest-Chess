import React from 'react'
import { TEXT } from '../Data/content'
import { Side } from '../Data/types'
import { Phase } from '../Hooks/useGame'

interface TurnIndicatorProps {
  side: Side
  phase: Phase
  error: string | null
  retryLabel: string
  onRetry: () => void
}

const LABELS: Record<Exclude<Phase, 'error'>, string> = {
  starting: TEXT.game.starting,
  yourTurn: TEXT.game.yourMove,
  aiThinking: TEXT.game.aiThinking,
  over: TEXT.game.over,
}

/**
 * The line above the board saying whose turn it is, with a spinner while the AI thinks.
 *
 * @param side The colour the player chose.
 * @param phase What the game is waiting for.
 * @param error The message to show when a request failed.
 * @param retryLabel The wording of the button shown with the error.
 * @param onRetry Called when the player retries after an error.
 */
const TurnIndicator = ({ side, phase, error, retryLabel, onRetry }: Readonly<TurnIndicatorProps>) => (
  <div className='mb-3 flex flex-wrap items-center justify-center gap-3' role='status' aria-live='polite'>
    <span className='text-xs font-semibold uppercase tracking-[0.35em] text-gold'>{TEXT.game.youPlay(side)}</span>
    {phase === 'error' ? (
      <span className='turn turn--error'>
        {error}
        <button type='button' onClick={onRetry} className='turn__retry'>
          {retryLabel}
        </button>
      </span>
    ) : (
      <span className={`turn turn--${phase}`}>
        {phase === 'aiThinking' && <span className='turn__spinner' aria-hidden='true' />}
        {LABELS[phase]}
      </span>
    )}
  </div>
)

export default TurnIndicator
