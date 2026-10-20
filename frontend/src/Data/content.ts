import { EndReason, MoveAction } from '../Api/types'
import { Outcome } from '../Logic/outcome'
import { Side } from './types'

const ACTION_LABELS: Record<MoveAction, (piece: string) => string> = {
  move: (piece) => `Move the ${piece}`,
  capture: (piece) => `Capture with the ${piece}`,
  push: (piece) => `Push with the ${piece}`,
  crush: (piece) => `Crush with the ${piece}`,
  fling: (piece) => `Fling the ${piece} with the Catapult`,
}

const END_REASONS: Record<EndReason, Record<Outcome, string>> = {
  // A King can fall to a capture, poison, an explosion, a rampage or a crush, so these stay neutral.
  king_captured: {
    win: 'The AI’s King has fallen.',
    lose: 'Your King has fallen.',
    draw: 'Both Kings fell on the same turn.',
  },
  resignation: {
    win: 'The AI resigned.',
    lose: 'You resigned the game.',
    draw: 'The game was resigned.',
  },
  no_legal_moves: {
    win: 'The AI had no legal move left.',
    lose: 'You had no legal move left.',
    draw: 'A side had no legal move left, so the game is drawn.',
  },
}

// All interface wording lives here so copy can be edited without touching components.
export const TEXT = {
  menu: {
    tagline: 'A custom game of strategy',
    title: 'Wildebeest Chess',
    play: 'Play',
    rules: 'Rules',
    source: 'View source on GitHub',
    sourceUrl: 'https://github.com/SulakshanSiva/Wildebeest-Chess',
  },
  colourSelect: {
    eyebrow: 'Choose your side',
    title: 'Pick a colour',
  },
  game: {
    resign: 'Resign',
    menu: 'Main menu',
    showRules: 'Show rules',
    boardLabel: 'Chess board',
    // The left bar holds your pieces that were removed, the right bar the AI's.
    aiCaptures: 'AI captures',
    yourCaptures: 'Your captures',
    noCaptures: 'None yet',
    youPlay: (side: Side) => `You play ${side}`,
    starting: 'Setting up the board',
    yourMove: 'Your move',
    aiThinking: 'AI is thinking',
    over: 'Game over',
    retry: 'Try again',
    connectionError: 'Could not reach the game server. Is the backend running?',
    possibleMove: 'possible move',
    selected: 'selected',
  },
  resign: {
    title: 'Resign this game?',
    message: 'The AI will be declared the winner.',
    confirm: 'Resign',
    cancel: 'Keep playing',
  },
  outcome: {
    titles: { win: 'You win!', lose: 'You lose', draw: 'Draw' } as Record<Outcome, string>,
    reason: (reason: EndReason, outcome: Outcome) => END_REASONS[reason][outcome],
    playAgain: 'Play again',
    menu: 'Main menu',
    viewBoard: 'View board',
  },
  moveChoice: {
    title: 'Choose a move',
    message: 'More than one move ends on that square.',
    describe: (action: MoveAction, piece: string) => ACTION_LABELS[action](piece),
    cancel: 'Cancel',
  },
  // Move history. Piece phrases arrive ready-made, such as "your Pawn" or "the AI's Rook".
  history: {
    title: 'History',
    empty: 'No moves yet',
    you: 'You',
    ai: 'AI',
    yourPiece: (name: string) => `your ${name}`,
    aiPiece: (name: string) => `the AI’s ${name}`,
    moved: (piece: string, from: string, to: string) => `${piece} ${from} → ${to}`,
    captured: (victim: string) => `Captured ${victim}`,
    crushed: (victim: string) => `Crushed ${victim}`,
    pushed: (victim: string, to: string) => `Pushed ${victim} to ${to}`,
    flung: (catapult: string) => `Flung by the Catapult on ${catapult}`,
    flungOnto: (victim: string) => `Landed on ${victim}, capturing it`,
    poisoned: (victim: string) => `Poison took ${victim}`,
    rampage: (victims: string) => `A Golf Cart rampage destroyed ${victims}`,
    teleported: (piece: string, from: string, to: string) => `Teleported ${piece} ${from} → ${to}`,
    exploded: (joey: string) => `${joey} exploded`,
    explodedTaking: (joey: string, victims: string) => `${joey} exploded, taking ${victims}`,
    // Promotions are named by the kind a piece became; anything unlisted uses becameOther.
    became: {
      jet_pack_king: (piece: string) => `${piece} strapped on the jet pack`,
      time_machine: (piece: string) => `${piece} reached the far row and became a Time Machine`,
      grand_empress: (piece: string) => `${piece} turned the poison back and became a Grand Empress`,
    } as Record<string, (piece: string) => string>,
    becameOther: (piece: string, kind: string) => `${piece} became a ${kind}`,
    and: 'and',
    repeated: (piece: string, count: number) => `${piece} ×${count}`,
  },
  rules: {
    title: 'Rules',
    close: 'Close rules',
    pieces: 'Pieces',
    movement: 'Movement',
    special: 'Special',
    squares: 'Special squares',
  },
  dialog: {
    close: 'Close',
  },
}

export const SIDES: { side: Side; label: string; note: string }[] = [
  { side: 'white', label: 'White', note: 'Moves first' },
  { side: 'black', label: 'Black', note: 'Moves second' },
]
