import { Side } from './types'

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
    showRules: 'Show rules',
    boardLabel: 'Chess board',
    capturedByYou: 'Your captures',
    capturedByOpponent: 'AI captures',
    noCaptures: 'None yet',
    youPlay: (side: Side) => `You play ${side}`,
  },
  rules: {
    title: 'Rules',
    close: 'Close rules',
    pieces: 'Pieces',
    movement: 'Movement',
    special: 'Special',
    squares: 'Special squares',
  },
}

export const SIDES: { side: Side; label: string; note: string }[] = [
  { side: 'white', label: 'White', note: 'Moves first' },
  { side: 'black', label: 'Black', note: 'Moves second' },
]
