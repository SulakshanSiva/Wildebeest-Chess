import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { ApiError, createGame, getGame, resignGame, submitMove } from '../Api/client'
import { BoardCells, GameResponse, Move, Piece, Square } from '../Api/types'
import { TEXT } from '../Data/content'
import { LAYOUT } from '../Data/layout'
import { AI_MIN_THINKING_MS } from '../Data/settings'
import { Side } from '../Data/types'
import { applyMoveLocally, layoutToBoard, sameSquare, squareKey } from '../Logic/board'
import { addCaptures, CapturedBySide, mergePieces, NO_CAPTURES, piecesById } from '../Logic/captures'
import { describeTurn, HistoryEntry } from '../Logic/history'
import { groupByDestination, movesFor } from '../Logic/moves'
import { Outcome, outcomeFor } from '../Logic/outcome'

// starting: creating the game. yourTurn: waiting for a click. aiThinking: a request is out
// and the AI is choosing. over: the game has ended. error: a request failed.
export type Phase = 'starting' | 'yourTurn' | 'aiThinking' | 'over' | 'error'

const NO_TARGETS = new Map<string, Move[]>()

/**
 * Works out what the game is waiting for after a response.
 *
 * @param game The game as the backend returned it.
 * @returns The phase to show.
 */
const phaseAfter = (game: GameResponse): Phase => {
  if (game.status !== 'active') return 'over'
  return game.side_to_move === game.human_color ? 'yourTurn' : 'aiThinking'
}

/**
 * Gives the phase a new game opens in.
 *
 * @param side The colour the player chose.
 * @returns Playing Black means the AI moves first, inside the create request, so it starts thinking.
 */
const firstPhase = (side: Side): Phase => (side === 'black' ? 'aiThinking' : 'starting')

/**
 * Waits, unless the wait is cancelled.
 *
 * @param ms How long to wait. Zero or less resolves at once.
 * @param signal Rejects the wait when aborted.
 * @returns A promise that resolves after the wait.
 */
const wait = (ms: number, signal: AbortSignal) =>
  new Promise<void>((resolve, reject) => {
    if (ms <= 0) {
      resolve()
      return
    }
    const timer = setTimeout(resolve, ms)
    signal.addEventListener('abort', () => {
      clearTimeout(timer)
      reject(signal.reason)
    })
  })

/**
 * Plays one game against the AI: creates it, tracks selection, sends moves and resignation.
 *
 * @param side The colour the player chose.
 * @param minThinkingMs The shortest time to show the AI as thinking before its reply appears.
 * @returns The game's state and the actions the game screen can take.
 */
export const useGame = (side: Side, minThinkingMs = AI_MIN_THINKING_MS) => {
  const [game, setGame] = useState<GameResponse | null>(null)
  const [board, setBoard] = useState<BoardCells>(() => layoutToBoard(LAYOUT))
  const [phase, setPhase] = useState<Phase>(firstPhase(side))
  const [selected, setSelected] = useState<Square | null>(null)
  const [lastMove, setLastMove] = useState<Move | null>(null)
  const [captured, setCaptured] = useState<CapturedBySide>(NO_CAPTURES)
  const [error, setError] = useState<string | null>(null)
  const [choices, setChoices] = useState<Move[] | null>(null)
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const inFlight = useRef<AbortController | null>(null)

  /**
   * Sends a request and applies the game it returns, cancelling any request still running.
   *
   * @param send Makes the request.
   * @param known The pieces on the board before the request, to colour any captures.
   */
  const run = useCallback(
    async (send: (signal: AbortSignal) => Promise<GameResponse>, known: Map<number, Piece>) => {
      inFlight.current?.abort()
      const controller = new AbortController()
      inFlight.current = controller
      const startedAt = Date.now()

      try {
        const response = await send(controller.signal)
        // Hold the thinking state only when the AI actually played in this request.
        if (response.turns.some((turn) => turn.side !== response.human_color)) {
          await wait(minThinkingMs - (Date.now() - startedAt), controller.signal)
        }
        // Pieces from before the request win; the new board fills in any the old one lacked.
        const lookup = mergePieces(known, piecesById(response.board))
        setGame(response)
        setBoard(response.board)
        setCaptured((current) => addCaptures(current, response.turns, lookup))
        setHistory((current) => [
          ...current,
          ...response.turns.map((turn) => describeTurn(turn, lookup, response.human_color)),
        ])
        const latest = response.turns.at(-1)
        if (latest) setLastMove(latest.move)
        setPhase(phaseAfter(response))
        setError(null)
      } catch (caught) {
        // A cancelled request was replaced or the screen closed, so there is nothing to show.
        if (controller.signal.aborted) return
        setError(caught instanceof ApiError ? caught.message : TEXT.game.connectionError)
        setPhase('error')
      }
    },
    [minThinkingMs],
  )

  /**
   * Starts a fresh game, clearing everything left from any earlier one.
   */
  const start = useCallback(() => {
    setGame(null)
    setBoard(layoutToBoard(LAYOUT))
    setSelected(null)
    setLastMove(null)
    setCaptured(NO_CAPTURES)
    setHistory([])
    setChoices(null)
    setError(null)
    setPhase(firstPhase(side))
    run((signal) => createGame(side, signal), new Map())
  }, [run, side])

  useEffect(() => {
    start()
    return () => inFlight.current?.abort()
  }, [start])

  const legalMoves = game?.legal_moves
  const targets = useMemo(
    () => (selected && legalMoves ? groupByDestination(movesFor(legalMoves, selected)) : NO_TARGETS),
    [selected, legalMoves],
  )

  /**
   * Plays a move: shows it at once, then waits for the server and the AI's reply.
   *
   * @param move One of the player's legal moves.
   */
  const play = (move: Move) => {
    if (!game) return
    const known = piecesById(board)
    setBoard(applyMoveLocally(board, move))
    setLastMove(move)
    setSelected(null)
    setChoices(null)
    setPhase('aiThinking')
    run((signal) => submitMove(game, move, signal), known)
  }

  /**
   * Handles a click on a square: select a piece, play to a highlighted square, or deselect.
   *
   * @param square The clicked square.
   */
  const clickSquare = (square: Square) => {
    if (phase !== 'yourTurn' || !game) return

    const moves = targets.get(squareKey(square))
    if (moves) {
      // Two moves can end on one square, such as a step and a fling; the player picks.
      if (moves.length === 1) play(moves[0])
      else setChoices(moves)
      return
    }

    const isSelectable = !sameSquare(square, selected) && movesFor(game.legal_moves, square).length > 0
    setSelected(isSelectable ? square : null)
  }

  /**
   * Fetches the game again after a failed request, or starts over if there is no game yet.
   */
  const retry = () => {
    if (!game) {
      start()
      return
    }
    setError(null)
    // The failed move may never have reached the server, so its highlight is not trustworthy.
    setLastMove(null)
    setPhase('starting')
    run((signal) => getGame(game.game_id, signal), piecesById(board))
  }

  /**
   * Concedes the game to the AI.
   */
  const resign = () => {
    if (!game) return
    setSelected(null)
    run((signal) => resignGame(game.game_id, signal), piecesById(board))
  }

  const outcome: Outcome | null = game ? outcomeFor(game.status, game.human_color) : null

  return {
    phase,
    board,
    selected,
    targets,
    lastMove,
    captured,
    history,
    error,
    outcome,
    endReason: game?.end_reason ?? null,
    choices,
    clickSquare,
    choose: play,
    cancelChoice: () => setChoices(null),
    retry,
    resign,
  }
}
