import { outcomeFor } from './outcome'

describe('outcomeFor', () => {
  it('is null while the game is active', () => {
    expect(outcomeFor('active', 'white')).toBeNull()
  })

  it('reads the result from the player’s side', () => {
    expect(outcomeFor('white_wins', 'white')).toBe('win')
    expect(outcomeFor('white_wins', 'black')).toBe('lose')
    expect(outcomeFor('black_wins', 'black')).toBe('win')
    expect(outcomeFor('draw', 'black')).toBe('draw')
  })
})
