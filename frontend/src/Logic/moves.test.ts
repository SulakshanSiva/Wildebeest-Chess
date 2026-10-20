import { Move } from '../Api/types'
import { groupByDestination, movesFor } from './moves'

const step: Move = { actor: { row: 0, column: 8 }, origin: { row: 0, column: 8 }, destination: { row: 1, column: 8 }, action: 'move' }
const fling: Move = { actor: { row: 0, column: 8 }, origin: { row: 0, column: 9 }, destination: { row: 0, column: 7 }, action: 'fling' }
const knight: Move = { actor: { row: 0, column: 9 }, origin: { row: 0, column: 9 }, destination: { row: 2, column: 8 }, action: 'move' }

describe('movesFor', () => {
  it('includes moves where the clicked piece is the one moving', () => {
    expect(movesFor([step, fling, knight], { row: 0, column: 9 })).toEqual([fling, knight])
  })

  it('includes flings when the Catapult itself is clicked', () => {
    expect(movesFor([step, fling, knight], { row: 0, column: 8 })).toEqual([step, fling])
  })
})

describe('groupByDestination', () => {
  it('keeps every move that ends on the same square', () => {
    const other = { ...fling, destination: step.destination }
    const groups = groupByDestination([step, other, knight])
    expect(groups.get('1,8')).toEqual([step, other])
    expect(groups.get('2,8')).toEqual([knight])
  })
})
