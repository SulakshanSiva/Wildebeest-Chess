import React from 'react'
import { BoardCells, Move, MoveAction, Square } from '../Api/types'
import { TEXT } from '../Data/content'
import { FILES } from '../Data/layout'
import { pieceForSymbol, TERRAIN } from '../Data/pieces'
import { Side } from '../Data/types'
import { orientRows, sameSquare, squareKey, squareName } from '../Logic/board'
import PieceToken from './PieceToken'

interface BoardProps {
  board: BoardCells
  side: Side
  selected: Square | null
  targets: Map<string, Move[]>
  lastMove: Move | null
  interactive: boolean
  onSquareClick: (square: Square) => void
}

const TERRAIN_BY_NAME = new Map(TERRAIN.map((info) => [info.terrain, info]))

// Moves that remove the piece on their destination. A Gorilla's push moves it instead.
const REMOVING_ACTIONS: MoveAction[] = ['capture', 'crush', 'fling']

/**
 * The 11x11 board with rank numbers on the left and file letters underneath.
 *
 * Every square is a button. After a piece is selected, the squares it can reach are marked: a
 * dot on an empty square, a red ring where a piece would be removed, a gold ring where a Gorilla
 * would push one.
 *
 * @param board The cells to draw, row 0 first.
 * @param side The colour the player chose; the board is oriented to it.
 * @param selected The selected piece's square, if any.
 * @param targets The selected piece's moves, keyed by destination square.
 * @param lastMove The most recent move, whose squares are tinted.
 * @param interactive Whether clicks are accepted, which is only on the player's turn.
 * @param onSquareClick Called with the square that was clicked.
 */
const Board = ({ board, side, selected, targets, lastMove, interactive, onSquareClick }: Readonly<BoardProps>) => {
  const rows = orientRows(board, side)

  return (
    <div className='game__frame'>
      <div className='game__ranks' aria-hidden='true'>
        {rows.map((line) => (
          <span key={line[0].square.row}>{line[0].square.row + 1}</span>
        ))}
      </div>
      <div className={`game__board ${interactive ? '' : 'game__board--waiting'}`} role='group' aria-label={TEXT.game.boardLabel}>
        {rows.flat().map(({ square, cell }) => {
          const piece = cell.piece ? pieceForSymbol(cell.piece.symbol) : undefined
          const terrain = TERRAIN_BY_NAME.get(cell.terrain)
          const targetMoves = targets.get(squareKey(square))
          const isTarget = targetMoves !== undefined
          const removes = targetMoves?.some((move) => REMOVING_ACTIONS.includes(move.action)) ?? false
          const isSelected = sameSquare(square, selected)
          const isLastMove = lastMove !== null && (sameSquare(square, lastMove.origin) || sameSquare(square, lastMove.destination))

          const classes = [
            'game__square',
            (square.row + square.column) % 2 === 0 ? 'game__square--dark' : 'game__square--light',
            isSelected ? 'game__square--selected' : '',
            isLastMove ? 'game__square--last-move' : '',
            isTarget && cell.piece && removes ? 'game__square--capture-target' : '',
            isTarget && cell.piece && !removes ? 'game__square--push-target' : '',
          ]
          const description = [
            squareName(square),
            cell.piece && piece ? `${cell.piece.color} ${piece.name}` : '',
            terrain?.name.toLowerCase() ?? '',
            isSelected ? TEXT.game.selected : '',
            isTarget ? TEXT.game.possibleMove : '',
          ]

          return (
            <button
              key={squareKey(square)}
              type='button'
              disabled={!interactive}
              aria-label={description.filter(Boolean).join(', ')}
              aria-pressed={isSelected}
              className={classes.filter(Boolean).join(' ')}
              onClick={() => onSquareClick(square)}
            >
              {terrain && <span className='game__terrain'>{terrain.glyph}</span>}
              {cell.piece && <PieceToken symbol={cell.piece.symbol} />}
              {isTarget && !cell.piece && <span className='game__target-dot' />}
            </button>
          )
        })}
      </div>
      <div className='game__files' aria-hidden='true'>
        {rows[0].map(({ square }) => (
          <span key={square.column}>{FILES[square.column]}</span>
        ))}
      </div>
    </div>
  )
}

export default Board
