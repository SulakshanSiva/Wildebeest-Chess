import React, { ReactNode, useEffect, useRef } from 'react'
import { TEXT } from '../Data/content'

interface ModalProps {
  labelledBy: string
  onClose: () => void
  className?: string
  children: ReactNode
}

/**
 * The shared popup shell: a dimmed backdrop, Escape and outside clicks to close, focus moved in.
 *
 * @param labelledBy Id of the heading that names the popup.
 * @param onClose Called when the player dismisses the popup.
 * @param className Extra classes for the popup panel's size and colours.
 * @param children The popup's content.
 */
const Modal = ({ labelledBy, onClose, className = '', children }: Readonly<ModalProps>) => {
  const panel = useRef<HTMLDialogElement>(null)

  // Escape closes the popup, and focus moves inside it so keyboard users start there.
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    panel.current?.focus()
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className='modal-backdrop'>
      {/* The backdrop is a real button, so clicking outside the popup closes it without a div click handler */}
      <button type='button' className='modal-backdrop__dismiss' aria-label={TEXT.dialog.close} tabIndex={-1} onClick={onClose} />
      <dialog open ref={panel} tabIndex={-1} aria-modal='true' aria-labelledby={labelledBy} className={`modal ${className}`}>
        {children}
      </dialog>
    </div>
  )
}

export default Modal
