import { PieceInfo, Side, TerrainInfo } from './types'

/**
 * Asks the browser to draw a symbol as a flat glyph rather than a colour emoji.
 *
 * @param glyph The symbol to draw.
 * @returns The symbol followed by the text variation selector.
 */
const flat = (glyph: string) => `${glyph}\uFE0E`

/**
 * Marks a classic chess symbol, which draws smaller than emoji, for a larger size.
 *
 * @param glyph The chess symbol.
 * @returns The glyph and classic flag, to spread into a piece entry.
 */
const classic = (glyph: string) => ({ glyph: flat(glyph), classic: true })

export const PIECES: PieceInfo[] = [
  { symbol: 'P', kind: 'pawn', name: 'Pawn', ...classic('♟'), moves: 'Moves forward one square, or two on its first move if both squares are clear. Captures one square diagonally forward, never straight ahead.', special: 'Reaching the far row turns it into a Time Machine. No en passant.' },
  { symbol: 'R', kind: 'rook', name: 'Rook', ...classic('♜'), moves: 'Slides any distance in a straight line, forwards, backwards or sideways.' },
  { symbol: 'N', kind: 'knight', name: 'Knight', ...classic('♞'), moves: 'Leaps in an L shape: two squares one way and one square at a right angle. It jumps over other pieces.' },
  { symbol: 'B', kind: 'bishop', name: 'Bishop', ...classic('♝'), moves: 'Slides any distance along a diagonal.' },
  { symbol: 'K', kind: 'king', name: 'King', ...classic('♚'), moves: 'Steps one square in any direction. Capturing the enemy King wins the game.', special: 'Landing on the jet pack square upgrades it to a King with a Jet Pack.' },
  { symbol: 'W', kind: 'jet_pack_king', name: 'King with a Jet Pack', glyph: flat('🚀'), moves: 'Slides any distance along a diagonal, like a Bishop. Still counts as a King.', special: 'It hovers: a Gorilla cannot push it, and flung pieces pass over it.' },
  { symbol: 'J', kind: 'joey', name: 'Prince Joey', glyph: flat('🦘'), moves: 'Steps one square in any direction.', special: 'After each move, if the number of pieces in Joey’s row is a multiple of five, he explodes and removes himself and every piece next to him, friend or foe.' },
  { symbol: 'S', kind: 'serpent', name: 'Serpent', glyph: flat('🐍'), moves: 'Steps one square in any direction, but can never capture by moving.', special: 'Poison: every enemy piece standing next to a Serpent is removed after a move. Golf Carts and Time Machines are immune.' },
  { symbol: 'O', kind: 'old_woman', name: 'Old Woman', glyph: flat('👵'), moves: 'Steps one square in any direction.', special: 'If a poisoned piece stands next to your Old Woman, it survives and the poisoner dies instead. She becomes a Grand Empress. She cannot save herself.' },
  { symbol: 'E', kind: 'grand_empress', name: 'Grand Empress', ...classic('♛'), moves: 'Slides any distance in any direction and also leaps like a Knight.', special: 'She poisons adjacent enemies, just like the Serpent she is made from.' },
  { symbol: 'X', kind: 'golf_cart', name: 'Golf Cart', glyph: flat('🛺'), moves: 'Moves and captures left and right along the top and bottom rows only.', special: 'Charged by an advanced enemy pawn on the middle row (or your own Time Machine), it rampages to the other end of its column, capturing everything in its path, friend or foe.' },
  { symbol: 'Z', kind: 'beekeeper', name: 'BeeKeeper', glyph: flat('🐝'), moves: 'Steps one square in any direction.', special: 'Its swarm paralyses every enemy piece next to it. A paralysed piece cannot move on its turn. Golf Carts and Time Machines are immune.' },
  { symbol: 'G', kind: 'gorilla', name: 'Gorilla', glyph: flat('🦍'), moves: 'Steps one square in any direction. It never captures by moving.', special: 'Stepping onto a piece pushes it one square further. If that square is blocked, the pushed piece is crushed. Gorillas and hovering pieces cannot be pushed, and nothing is pushed off the board.' },
  { symbol: 'C', kind: 'catapult', name: 'Catapult', glyph: flat('🏹'), moves: 'Steps one square in any direction without capturing.', special: 'Or spends its turn flinging a friendly neighbour in a line over the Catapult. It flies over everything and lands on an empty square or captures an enemy, but never a King or a Gorilla.' },
  { symbol: 'H', kind: 'time_machine', name: 'Time Machine', glyph: flat('⏳'), moves: 'Cannot move or capture.', special: 'Charges its side’s Golf Carts while it is on the board. Cannot be flung or paralysed.' },
]

const TRANSPORTER_GLYPH = '✦'
const JET_PACK_GLYPH = flat('🚀')

export const TERRAIN: TerrainInfo[] = [
  { terrain: 'jet_pack', name: 'Jet pack', glyph: JET_PACK_GLYPH, description: 'A King that lands here becomes a King with a Jet Pack. The square is never used up.' },
  { terrain: 'transporter_pad', name: 'Transporter pad', glyph: TRANSPORTER_GLYPH, description: 'A piece resting on a pad is carried to the next pad in the cycle at the end of the turn.' },
]

export const GENERAL_RULES: string[] = [
  'Capture the enemy King to win. If both Kings fall together, or a side has no legal move, the game is a draw.',
  'White moves first, then players alternate. You may resign at any time.',
  'After every move the after-effects run in order: poison, promotion, golf cart rampage, transporters, then Joey explosions.',
]

const PIECE_BY_SYMBOL = new Map(PIECES.map((piece) => [piece.symbol, piece]))
const PIECE_BY_KIND = new Map(PIECES.map((piece) => [piece.kind, piece]))

/**
 * Finds the piece a board letter stands for, in either colour.
 *
 * @param symbol A board letter, uppercase for White and lowercase for Black.
 * @returns The piece, or undefined for a letter that is not a piece.
 */
export const pieceForSymbol = (symbol: string) => PIECE_BY_SYMBOL.get(symbol.toUpperCase())

/**
 * Gives the colour a board letter belongs to.
 *
 * @param symbol A board letter.
 * @returns White for uppercase, Black for lowercase.
 */
export const sideOfSymbol = (symbol: string): Side => (symbol === symbol.toUpperCase() ? 'white' : 'black')

/**
 * Gives the board letter for a piece kind in a given colour.
 *
 * @param kind The backend's piece kind, for example "golf_cart".
 * @param side The piece's colour.
 * @returns Uppercase for White, lowercase for Black, or an empty string for an unknown kind.
 */
export const symbolForKind = (kind: string, side: Side) => {
  const symbol = PIECE_BY_KIND.get(kind)?.symbol ?? ''
  return side === 'white' ? symbol : symbol.toLowerCase()
}
