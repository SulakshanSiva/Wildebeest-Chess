import React, { ButtonHTMLAttributes } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  className?: string
}

const BASE =
  'menu__play-button rounded-full border border-gold-light bg-gold px-10 py-3 font-cinzel text-sm font-bold uppercase tracking-[0.2em] text-ink transition hover:bg-gold-light focus:outline-none focus:ring-2 focus:ring-cream focus:ring-offset-2 focus:ring-offset-ink'

/**
 * The gold pill button used across the app.
 *
 * @param className Extra classes for sizing and positioning.
 */
const Button = ({ className = '', type = 'button', ...rest }: ButtonProps) => (
  <button type={type} className={`${BASE} ${className}`} {...rest} />
)

export default Button
