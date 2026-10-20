import React, { useState } from 'react'
import { TEXT } from '../Data/content'
import { GENERAL_RULES, PIECES, TERRAIN } from '../Data/pieces'
import Modal from './Modal'

interface RulesModalProps {
  onClose: () => void
}

const HEADING = 'font-cinzel text-sm font-bold uppercase tracking-[0.25em] text-gold'
const LABEL = 'text-sm font-semibold uppercase tracking-[0.18em] text-gold'

/**
 * Popup that explains the rules, with one entry per piece.
 *
 * @param onClose Called when the player dismisses the popup.
 */
const RulesModal = ({ onClose }: Readonly<RulesModalProps>) => {
  const [selected, setSelected] = useState(0)
  const piece = PIECES[selected]

  return (
    <Modal labelledBy='rules-title' onClose={onClose} className='flex max-h-[90vh] max-w-3xl flex-col'>
      <header className='flex items-center justify-between border-b border-gold/40 px-6 py-4'>
        <h2 id='rules-title' className='font-cinzel text-2xl font-bold text-gold-light'>{TEXT.rules.title}</h2>
        <button
          type='button'
          onClick={onClose}
          aria-label={TEXT.rules.close}
          className='h-9 w-9 rounded-full border border-gold text-xl leading-none text-gold transition hover:bg-gold hover:text-ink focus:outline-none focus:ring-2 focus:ring-cream'
        >
          ×
        </button>
      </header>

      <div className='overflow-y-auto px-6 py-5'>
        <ul className='mb-6 list-disc space-y-2 pl-5 text-sm text-cream/85'>
          {GENERAL_RULES.map((rule) => (
            <li key={rule}>{rule}</li>
          ))}
        </ul>

        <h3 className={`mb-3 ${HEADING}`}>{TEXT.rules.pieces}</h3>
        <div className='grid gap-4 sm:grid-cols-[13rem_1fr]'>
          <div className='grid grid-cols-5 gap-2 sm:grid-cols-3' role='tablist' aria-label={TEXT.rules.pieces}>
            {PIECES.map((entry, index) => (
              <button
                key={entry.symbol}
                type='button'
                role='tab'
                aria-selected={index === selected}
                aria-label={entry.name}
                title={entry.name}
                onClick={() => setSelected(index)}
                className={`flex aspect-square items-center justify-center rounded-lg border ${entry.classic ? 'text-4xl' : 'text-2xl'} transition focus:outline-none focus:ring-2 focus:ring-cream ${
                  index === selected
                    ? 'border-gold-light bg-gold text-ink'
                    : 'border-gold/40 bg-felt-raised text-cream hover:border-gold-light'
                }`}
              >
                {entry.glyph}
              </button>
            ))}
          </div>

          <article className='rounded-xl border border-gold/40 bg-felt-raised p-5' aria-live='polite'>
            <div className='mb-3 flex items-center gap-3'>
              <span className={`flex h-12 w-12 items-center justify-center rounded-full bg-gold text-ink ${piece.classic ? 'text-5xl' : 'text-3xl'}`}>{piece.glyph}</span>
              <h4 className='font-cinzel text-xl font-bold text-cream'>{piece.name}</h4>
            </div>
            <p className={LABEL}>{TEXT.rules.movement}</p>
            <p className='mb-3 text-sm text-cream/90'>{piece.moves}</p>
            {piece.special && (
              <>
                <p className={LABEL}>{TEXT.rules.special}</p>
                <p className='text-sm text-cream/90'>{piece.special}</p>
              </>
            )}
          </article>
        </div>

        <h3 className={`mb-3 mt-6 ${HEADING}`}>{TEXT.rules.squares}</h3>
        <ul className='space-y-2 text-sm text-cream/85'>
          {TERRAIN.map((terrain) => (
            <li key={terrain.name}>
              <span className='mr-2'>{terrain.glyph}</span>
              <strong className='text-cream'>{terrain.name}.</strong> {terrain.description}
            </li>
          ))}
        </ul>
      </div>
    </Modal>
  )
}

export default RulesModal
