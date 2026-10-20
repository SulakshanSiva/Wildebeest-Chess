import React from 'react'
import { TEXT } from '../Data/content'
import { CapturedPiece } from '../Data/types'
import PieceToken from './PieceToken'

interface CapturedBarProps {
  title: string
  pieces: CapturedPiece[]
  placement: 'left' | 'right'
}

/**
 * A bar beside the board listing captured pieces, oldest first.
 *
 * @param title Heading naming whose captures these are.
 * @param pieces The captured pieces.
 * @param placement Which side of the board the bar sits on.
 */
const CapturedBar = ({ title, pieces, placement }: CapturedBarProps) => (
  <aside className={`captured captured--${placement}`} aria-label={title}>
    <h2 className='captured__title'>{title}</h2>
    {pieces.length === 0 ? (
      <p className='captured__empty'>{TEXT.game.noCaptures}</p>
    ) : (
      <ul className='captured__list'>
        {pieces.map((piece) => (
          <li key={piece.id} className='captured__slot'>
            <PieceToken symbol={piece.symbol} />
          </li>
        ))}
      </ul>
    )}
  </aside>
)

export default CapturedBar
