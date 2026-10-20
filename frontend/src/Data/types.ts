import { Terrain } from '../Api/types'

export type Side = 'white' | 'black'

export interface PieceInfo {
  symbol: string
  kind: string
  name: string
  glyph: string
  classic?: boolean
  moves: string
  special?: string
}

export interface TerrainInfo {
  terrain: Terrain
  name: string
  glyph: string
  description: string
}

export interface CapturedPiece {
  id: number
  symbol: string
}
