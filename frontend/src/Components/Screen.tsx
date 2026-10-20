import React, { ReactNode } from 'react'

interface ScreenProps {
  children: ReactNode
}

/**
 * Shared full-page shell with the checkerboard backdrop used on every screen.
 *
 * @param children The screen's content.
 */
const Screen = ({ children }: ScreenProps) => (
  <main className='menu min-h-screen overflow-hidden bg-felt text-white'>
    <div className='menu__board' aria-hidden='true' />
    <div className='menu__overlay' aria-hidden='true' />
    {children}
  </main>
)

export default Screen
