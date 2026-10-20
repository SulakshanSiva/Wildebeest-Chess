import React, { useId } from 'react'
import Modal from './Modal'

export interface DialogAction {
  label: string
  onClick: () => void
  primary?: boolean
}

interface DialogProps {
  title: string
  message?: string
  actions: DialogAction[]
  onClose: () => void
}

const ACTION_BASE =
  'rounded-full border px-6 py-2 font-cinzel text-sm font-bold uppercase tracking-[0.16em] transition focus:outline-none focus:ring-2 focus:ring-cream'
const PRIMARY = 'border-gold-light bg-gold text-ink hover:bg-gold-light'
const SECONDARY = 'border-gold/60 text-gold-light hover:bg-felt-raised'

/**
 * A small popup with a title, a message and a row of buttons.
 *
 * @param title The popup's heading.
 * @param message An optional sentence under the heading.
 * @param actions The buttons, in display order.
 * @param onClose Called on Escape or a click outside.
 */
const Dialog = ({ title, message, actions, onClose }: Readonly<DialogProps>) => {
  const titleId = useId()

  return (
    <Modal labelledBy={titleId} onClose={onClose} className='max-w-md px-6 py-6 text-center'>
      <h2 id={titleId} className='font-cinzel text-3xl font-bold text-gold-light'>
        {title}
      </h2>
      {message && <p className='mt-3 text-sm text-cream/85'>{message}</p>}
      <div className='mt-6 flex flex-wrap justify-center gap-3'>
        {actions.map((action) => (
          <button
            key={action.label}
            type='button'
            onClick={action.onClick}
            className={`${ACTION_BASE} ${action.primary ? PRIMARY : SECONDARY}`}
          >
            {action.label}
          </button>
        ))}
      </div>
    </Modal>
  )
}

export default Dialog
