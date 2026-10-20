import React from 'react'
import { TEXT } from '../Data/content'
import Button from './Button'
import Screen from './Screen'

interface MenuProps {
  onPlay: () => void
  onRules: () => void
}

/**
 * The home page.
 *
 * @param onPlay Called when Play is clicked.
 * @param onRules Called when Rules is clicked.
 */
const Menu = ({ onPlay, onRules }: Readonly<MenuProps>) => (
  <Screen>
    <section className='menu__content px-6 text-center'>
      <p className='mb-4 text-xs font-semibold uppercase tracking-[0.45em] text-gold sm:text-sm'>
        {TEXT.menu.tagline}
      </p>
      <h1 className='font-cinzel text-5xl font-bold leading-tight text-cream drop-shadow-[0_4px_0_rgba(31,18,8,0.35)] sm:text-7xl md:text-8xl'>
        {TEXT.menu.title}
      </h1>
      <div className='mt-10 flex flex-col items-center gap-4'>
        <Button className='w-40' onClick={onPlay}>{TEXT.menu.play}</Button>
        <Button className='w-40' onClick={onRules}>{TEXT.menu.rules}</Button>
      </div>
    </section>

    <footer className='menu__credits'>
      <a
        href={TEXT.menu.sourceUrl}
        target='_blank'
        rel='noreferrer'
        className='text-xs tracking-[0.16em] text-cream/75 transition hover:text-cream focus:outline-none focus:ring-2 focus:ring-gold-light focus:ring-offset-2 focus:ring-offset-ink'
      >
        {TEXT.menu.source}
      </a>
    </footer>
  </Screen>
)

export default Menu
