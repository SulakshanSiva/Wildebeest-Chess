import React from 'react'
import { pieceForSymbol, sideOfSymbol } from '../Data/pieces'

interface PieceTokenProps {
  symbol: string
}

/**
 * One round piece token. It sizes itself to its parent, which must set `container-type: size`.
 *
 * @param symbol The piece's board letter; its case gives the colour.
 */
const PieceToken = ({ symbol }: PieceTokenProps) => {
  const piece = pieceForSymbol(symbol)
  if (!piece) return null

  const classes = ['piece', `piece--${sideOfSymbol(symbol)}`, piece.classic ? 'piece--classic' : '']
  return (
    <span title={piece.name} className={classes.join(' ')}>
      {piece.glyph}
    </span>
  )
}

export default PieceToken
