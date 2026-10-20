import React, { useState } from 'react'
import { TEXT } from '../Data/content'
import { pieceForSymbol } from '../Data/pieces'
import { Side } from '../Data/types'
import { useGame } from '../Hooks/useGame'
import { opponentOf, pieceAt } from '../Logic/board'
import Board from './Board'
import Button from './Button'
import CapturedBar from './CapturedBar'
import Dialog from './Dialog'
import MoveHistory from './MoveHistory'
import Screen from './Screen'
import TurnIndicator from './TurnIndicator'

interface GameProps {
  side: Side
  onExit: () => void
  onPlayAgain: () => void
  onShowRules: () => void
}

/**
 * The game screen: the move history, the board between the two capture bars, rules top left,
 * resign top right, and the popups for resigning, choosing between moves and the result.
 *
 * @param side The colour the player chose.
 * @param onExit Called to return to the main menu.
 * @param onPlayAgain Called to start a new game from the colour choice.
 * @param onShowRules Called when the player opens the rules popup.
 */
const Game = ({ side, onExit, onPlayAgain, onShowRules }: Readonly<GameProps>) => {
  const game = useGame(side)
  const [confirmingResign, setConfirmingResign] = useState(false)
  const [resultDismissed, setResultDismissed] = useState(false)
  const isOver = game.phase === 'over'

  /**
   * Resigns after the player confirms.
   */
  const resign = () => {
    setConfirmingResign(false)
    game.resign()
  }

  return (
    <Screen>
      <button
        type='button'
        onClick={onShowRules}
        aria-label={TEXT.game.showRules}
        className='absolute left-4 top-4 z-10 flex h-11 w-11 items-center justify-center rounded-full border-2 border-gold-light bg-felt/85 font-cinzel text-xl font-bold text-gold-light transition hover:bg-gold hover:text-ink focus:outline-none focus:ring-2 focus:ring-cream'
      >
        ?
      </button>
      <Button className='absolute right-4 top-4 z-10 !px-6 !py-2' onClick={isOver ? onExit : () => setConfirmingResign(true)}>
        {isOver ? TEXT.game.menu : TEXT.game.resign}
      </Button>

      <section className='game px-2 pb-6 pt-20 sm:pt-16'>
        <TurnIndicator side={side} phase={game.phase} error={game.error} onRetry={game.retry} />
        <div className='game__layout'>
          <MoveHistory entries={game.history} />
          <CapturedBar title={TEXT.game.aiCaptures} pieces={game.captured[side]} placement='left' />
          <Board
            board={game.board}
            side={side}
            selected={game.selected}
            targets={game.targets}
            lastMove={game.lastMove}
            interactive={game.phase === 'yourTurn'}
            onSquareClick={game.clickSquare}
          />
          <CapturedBar title={TEXT.game.yourCaptures} pieces={game.captured[opponentOf(side)]} placement='right' />
        </div>
      </section>

      {confirmingResign && !isOver && (
        <Dialog
          title={TEXT.resign.title}
          message={TEXT.resign.message}
          onClose={() => setConfirmingResign(false)}
          actions={[
            { label: TEXT.resign.confirm, onClick: resign, primary: true },
            { label: TEXT.resign.cancel, onClick: () => setConfirmingResign(false) },
          ]}
        />
      )}

      {game.choices && (
        <Dialog
          title={TEXT.moveChoice.title}
          message={TEXT.moveChoice.message}
          onClose={game.cancelChoice}
          actions={[
            ...game.choices.map((move) => ({
              label: TEXT.moveChoice.describe(move.action, pieceForSymbol(pieceAt(game.board, move.origin)?.symbol ?? '')?.name ?? ''),
              onClick: () => game.choose(move),
              primary: true,
            })),
            { label: TEXT.moveChoice.cancel, onClick: game.cancelChoice },
          ]}
        />
      )}

      {isOver && game.outcome && !resultDismissed && (
        <Dialog
          title={TEXT.outcome.titles[game.outcome]}
          message={game.endReason ? TEXT.outcome.reason(game.endReason, game.outcome) : undefined}
          onClose={() => setResultDismissed(true)}
          actions={[
            { label: TEXT.outcome.playAgain, onClick: onPlayAgain, primary: true },
            { label: TEXT.outcome.menu, onClick: onExit },
            { label: TEXT.outcome.viewBoard, onClick: () => setResultDismissed(true) },
          ]}
        />
      )}
    </Screen>
  )
}

export default Game
