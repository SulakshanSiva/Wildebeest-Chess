import React, { useState } from 'react'
import { Side } from '../Data/types'
import ColourSelect from './ColourSelect'
import Game from './Game'
import Menu from './Menu'
import RulesModal from './RulesModal'

type Stage = { name: 'menu' } | { name: 'colour' } | { name: 'game'; side: Side }

/**
 * Root component: moves between menu, colour choice and game, and hosts the rules popup.
 */
function App() {
  const [stage, setStage] = useState<Stage>({ name: 'menu' })
  const [showRules, setShowRules] = useState(false)

  return (
    <>
      {stage.name === 'menu' && (
        <Menu onPlay={() => setStage({ name: 'colour' })} onRules={() => setShowRules(true)} />
      )}
      {stage.name === 'colour' && (
        <ColourSelect onChoose={(side) => setStage({ name: 'game', side })} />
      )}
      {stage.name === 'game' && (
        <Game
          side={stage.side}
          onExit={() => setStage({ name: 'menu' })}
          onPlayAgain={() => setStage({ name: 'colour' })}
          onShowRules={() => setShowRules(true)}
        />
      )}
      {showRules && <RulesModal onClose={() => setShowRules(false)} />}
    </>
  )
}

export default App;
