import React, { useEffect, useRef } from 'react'
import { TEXT } from '../Data/content'
import { HistoryEntry, HistoryEventKind } from '../Logic/history'

interface MoveHistoryProps {
  entries: HistoryEntry[]
}

// One small marker per kind of event, so the unusual ones stand out in the list.
const EVENT_ICONS: Record<HistoryEventKind, string> = {
  capture: '⚔︎',
  crush: '✖︎',
  push: '➜︎',
  fling: '🏹︎',
  poison: '☠︎',
  power: '★︎',
  rampage: '🛺︎',
  teleport: '✦',
  explosion: '✸',
}

/**
 * The panel listing every turn played, newest at the bottom, with its captures and effects.
 *
 * @param entries The turns so far, oldest first.
 */
const MoveHistory = ({ entries }: Readonly<MoveHistoryProps>) => {
  const list = useRef<HTMLOListElement>(null)

  // Keep the latest turn in view by scrolling only the list, never the page around it.
  useEffect(() => {
    if (list.current) list.current.scrollTop = list.current.scrollHeight
  }, [entries.length])

  return (
    <aside className='history' aria-label={TEXT.history.title}>
      <h2 className='captured__title'>{TEXT.history.title}</h2>
      {entries.length === 0 ? (
        <p className='captured__empty'>{TEXT.history.empty}</p>
      ) : (
        <ol ref={list} className='history__list'>
          {entries.map((entry) => (
            <li key={entry.ply} className={`history__entry history__entry--${entry.side}`}>
              <div className='history__summary'>
                <span className='history__number'>{Math.floor(entry.ply / 2) + 1}.</span>
                <span className='history__who'>{entry.byPlayer ? TEXT.history.you : TEXT.history.ai}</span>
                <span>{entry.summary}</span>
              </div>
              {entry.events.length > 0 && (
                <ul className='history__events'>
                  {entry.events.map((event) => (
                    <li key={`${event.kind}-${event.text}`} className={`history__event history__event--${event.kind}`}>
                      <span className='history__icon' aria-hidden='true'>
                        {EVENT_ICONS[event.kind]}
                      </span>
                      {event.text}
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ol>
      )}
    </aside>
  )
}

export default MoveHistory
