import React from 'react'
import { TEXT } from '../Data/content'
import { EMPTY_CHAR, FILES, JET_PACK_CHAR, LAYOUT, TRANSPORTER_CHAR } from '../Data/layout'
import { JET_PACK_GLYPH, TRANSPORTER_GLYPH, pieceForSymbol, sideOfSymbol } from '../Data/pieces'
import { Side } from '../Data/types'
import PieceToken from './PieceToken'

interface BoardProps {
  side: Side
}

const TERRAIN_CHARS = [EMPTY_CHAR, TRANSPORTER_CHAR, JET_PACK_CHAR]

/**
 * Gives the squares in display order with the player's side at the bottom.
 *
 * @param side The colour the player chose.
 * @returns Rows from top to bottom, each a list of squares with its layout character.
 */
const buildRows = (side: Side) => {
  const rows = LAYOUT.map((line, row) => line.split('').map((char, column) => ({ row, column, char })))
  // Row 0 is White's back row, drawn at the bottom for White; Black sees the board turned round.
  return side === 'white' ? [...rows].reverse() : rows.map((line) => [...line].reverse())
}

/**
 * The 11x11 board with rank numbers on the left and file letters underneath.
 *
 * @param side The colour the player chose; the board is oriented to it.
 */
const Board = ({ side }: BoardProps) => {
  const rows = buildRows(side)

  return (
    <div className='game__frame'>
      <div className='game__ranks' aria-hidden='true'>
        {rows.map((line) => (
          <span key={line[0].row}>{line[0].row + 1}</span>
        ))}
      </div>
      <div className='game__board' role='grid' aria-label={TEXT.game.boardLabel}>
        {rows.flat().map(({ row, column, char }) => {
          const piece = TERRAIN_CHARS.includes(char) ? undefined : pieceForSymbol(char)
          const square = `${FILES[column]}${row + 1}`
          const shade = (row + column) % 2 === 0 ? 'dark' : 'light'
          return (
            <div
              key={square}
              role='gridcell'
              aria-label={piece ? `${square} ${sideOfSymbol(char)} ${piece.name}` : square}
              className={`game__square game__square--${shade}`}
            >
              {char === TRANSPORTER_CHAR && <span className='game__terrain'>{TRANSPORTER_GLYPH}</span>}
              {char === JET_PACK_CHAR && <span className='game__terrain'>{JET_PACK_GLYPH}</span>}
              {piece && <PieceToken symbol={char} />}
            </div>
          )
        })}
      </div>
      <div className='game__files' aria-hidden='true'>
        {rows[0].map((square) => (
          <span key={square.column}>{FILES[square.column]}</span>
        ))}
      </div>
    </div>
  )
}

export default Board
