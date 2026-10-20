import React from 'react'
import { SIDES, TEXT } from '../Data/content'
import { PIECES } from '../Data/pieces'
import { Side } from '../Data/types'
import Screen from './Screen'

interface ColourSelectProps {
  onChoose: (side: Side) => void
}

const KING_GLYPH = PIECES.find((piece) => piece.symbol === 'K')?.glyph

/**
 * Full-screen choice of colour shown after Play. There is no way to skip it.
 *
 * @param onChoose Called with the colour the player picked.
 */
const ColourSelect = ({ onChoose }: Readonly<ColourSelectProps>) => (
  <Screen>
    <section className='menu__content px-6 text-center'>
      <p className='mb-4 text-xs font-semibold uppercase tracking-[0.45em] text-gold sm:text-sm'>
        {TEXT.colourSelect.eyebrow}
      </p>
      <h1 className='font-cinzel text-4xl font-bold text-cream sm:text-6xl'>{TEXT.colourSelect.title}</h1>
      <div className='mt-10 flex flex-col items-center justify-center gap-6 sm:flex-row'>
        {SIDES.map(({ side, label, note }) => (
          <button
            key={side}
            type='button'
            onClick={() => onChoose(side)}
            className='menu__play-button flex w-48 flex-col items-center gap-3 rounded-2xl border border-gold-light bg-felt/80 px-6 py-6 transition hover:-translate-y-1 hover:bg-felt-raised focus:outline-none focus:ring-2 focus:ring-cream focus:ring-offset-2 focus:ring-offset-ink'
          >
            <span className={`swatch swatch--${side}`}>{KING_GLYPH}</span>
            <span className='font-cinzel text-lg font-bold uppercase tracking-[0.2em] text-gold-light'>{label}</span>
            <span className='text-xs tracking-[0.12em] text-cream/70'>{note}</span>
          </button>
        ))}
      </div>
    </section>
  </Screen>
)

export default ColourSelect
