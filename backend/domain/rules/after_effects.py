from __future__ import annotations

from dataclasses import dataclass, replace

from ..board import Board
from ..coordinates import ALL_DIRECTIONS, Coordinate
from ..enums import Color, PieceKind, Terrain
from ..pieces.base import Piece
from ..pieces.registry import build_rule
from .terrain import TransporterLinks, apply_transporters, jet_pack_landing

IMMUNE_TO_POISON = (PieceKind.GOLF_CART, PieceKind.TIME_MACHINE)
JOEY_EXPLOSION_DIVISOR = 5
PAWN_ADVANCE_TO_CHARGE = 4


@dataclass(frozen=True, slots=True)
class AfterEffectReport:
    """
    What one run of the after-effects pipeline did.

    Attributes:
        board: The board after every phase has run.
        removed: Identity and kind of each piece removed, in phase order.
        promoted: Identity and new kind of each piece that changed kind.
    """

    board: Board
    removed: tuple[tuple[int, PieceKind], ...] = ()
    promoted: tuple[tuple[int, PieceKind], ...] = ()


def _without(board: Board, squares: set[Coordinate]) -> Board:
    """
    Clear several squares at once, keeping their terrain.

    Arguments:
        board: The board to clear from.
        squares: Squares to empty. Already known to be occupied.

    Returns:
        A new board with those squares empty.
    """
    result = board
    for square in squares:
        result = result.without_piece(square)
    return result


def _neighbours(board: Board, square: Coordinate) -> list[Coordinate]:
    """
    Give the on-board squares touching a square.

    Arguments:
        board: The board to read.
        square: The centre square.

    Returns:
        Up to eight adjacent squares.
    """
    found = []
    for direction in ALL_DIRECTIONS:
        neighbour = square.shifted(direction)
        if neighbour is not None and board.contains(neighbour):
            found.append(neighbour)
    return found


def _replace_kind(board: Board, square: Coordinate, kind: PieceKind) -> Board:
    """
    Swap the kind of the piece on a square, rebuilding its movement rule.

    Arguments:
        board: The board to change.
        square: Square holding the piece. Must be occupied.
        kind: The kind it becomes.

    Returns:
        A new board carrying the changed piece on the same square.
    """
    piece = board.require_piece_at(square)
    changed = replace(piece, kind=kind, movement=build_rule(kind))
    return board.without_piece(square).with_piece(square, changed)


def apply_poisoning(
    board: Board,
) -> tuple[Board, list[tuple[int, PieceKind]], list[tuple[int, PieceKind]]]:
    """
    Run phase one: remove pieces standing next to an opposing poisoner.

    A Serpent, and a Grand Empress, poison every adjacent opposing piece.
    Friendly pieces are unaffected, and the Golf Cart and Time Machine cannot
    be poisoned. The Old Woman exception reverses it: if a poisoned piece also
    stands next to an opposing Old Woman, the pieces she shields survive, the
    poisoner dies instead, and she becomes a Grand Empress. She does not shield
    herself.

    Arguments:
        board: The board after a move has been applied.

    Returns:
        The new board, the pieces removed, and the pieces whose kind changed.
    """
    poisoners = [(square, piece) for square, piece in board.pieces() if piece.kind.poisons]
    if not poisoners:
        return board, [], []

    doomed: dict[Coordinate, Piece] = {}
    # Which poisoners are themselves undone by an Old Woman, and which Old
    # Women are promoted for undoing them.
    undone: set[Coordinate] = set()
    rescuers: set[Coordinate] = set()
    shielded: set[Coordinate] = set()

    for poisoner_square, poisoner in poisoners:
        for square in _neighbours(board, poisoner_square):
            victim = board.piece_at(square)
            if victim is None or victim.color is poisoner.color:
                continue
            if victim.kind in IMMUNE_TO_POISON:
                continue

            doomed[square] = victim
            if victim.kind is PieceKind.OLD_WOMAN:
                # She cannot save herself.
                continue

            for guard_square in _neighbours(board, square):
                guard = board.piece_at(guard_square)
                if (
                    guard is not None
                    and guard.kind is PieceKind.OLD_WOMAN
                    and guard.color is victim.color
                ):
                    shielded.add(square)
                    undone.add(poisoner_square)
                    rescuers.add(guard_square)

    removals = {square for square in doomed if square not in shielded}
    removals |= undone

    removed = [
        (doomed[square].piece_id, doomed[square].kind)
        for square in sorted(removals & set(doomed), key=lambda s: (s.row, s.column))
    ]
    for square in sorted(undone, key=lambda s: (s.row, s.column)):
        if square not in doomed:
            piece = board.require_piece_at(square)
            removed.append((piece.piece_id, piece.kind))

    result = _without(board, removals)

    promoted: list[tuple[int, PieceKind]] = []
    for square in sorted(rescuers, key=lambda s: (s.row, s.column)):
        if result.piece_at(square) is None:
            continue
        result = _replace_kind(result, square, PieceKind.GRAND_EMPRESS)
        promoted.append((result.require_piece_at(square).piece_id, PieceKind.GRAND_EMPRESS))

    return result, removed, promoted


def apply_promotion(board: Board) -> tuple[Board, list[tuple[int, PieceKind]]]:
    """
    Run phase two: convert pawns that crossed the board and kings on the pack.

    A Pawn reaching the far end becomes a Time Machine, by any means, so a
    flung or transported pawn promotes too. A King on the jet pack becomes a
    King with a Jet Pack, and the square is not consumed.

    Arguments:
        board: The board after poisoning.

    Returns:
        The new board and the pieces whose kind changed.
    """
    promoted: list[tuple[int, PieceKind]] = []
    result = board
    far_row = {Color.WHITE: board.rows - 1, Color.BLACK: 0}

    for square, piece in list(board.pieces()):
        if piece.kind is PieceKind.PAWN and square.row == far_row[piece.color]:
            result = _replace_kind(result, square, PieceKind.TIME_MACHINE)
            promoted.append((piece.piece_id, PieceKind.TIME_MACHINE))
            continue

        if piece.kind is PieceKind.KING and board.cell_at(square).terrain is Terrain.JET_PACK:
            upgraded = jet_pack_landing(piece)
            result = result.without_piece(square).with_piece(square, upgraded)
            promoted.append((piece.piece_id, upgraded.kind))

    return result, promoted


def _charged_carts(board: Board) -> set[Color]:
    """
    Decide whose Golf Carts are fully charged.

    A pawn of either side standing on the middle row charges the opposing
    player's cart. A Time Machine on the board charges its own side's cart.

    Arguments:
        board: The board to read.

    Returns:
        The colours whose carts rampage this turn.
    """
    charged: set[Color] = set()
    middle = board.rows // 2

    for square, piece in board.pieces():
        if piece.kind is PieceKind.PAWN:
            start_row = 1 if piece.color is Color.WHITE else board.rows - 2
            advanced = start_row + piece.color.forward * PAWN_ADVANCE_TO_CHARGE
            if square.row == advanced == middle:
                charged.add(piece.color.opponent)
        elif piece.kind is PieceKind.TIME_MACHINE:
            charged.add(piece.color)

    return charged


def apply_golf_cart_rampage(board: Board) -> tuple[Board, list[tuple[int, PieceKind]]]:
    """
    Run phase three: send every charged Golf Cart down its own column.

    A charged cart runs to the opposite end of its column, capturing everything
    it passes including friendly pieces and Gorillas. A cart already on the
    middle row has no opposite end and does not move. If both carts are charged
    in one column, that whole column is cleared, carts included.

    Arguments:
        board: The board after promotion.

    Returns:
        The new board and the pieces removed.
    """
    charged = _charged_carts(board)
    if not charged:
        return board, []

    carts = [
        (square, piece)
        for square, piece in board.pieces()
        if piece.kind is PieceKind.GOLF_CART and piece.color in charged
    ]
    if not carts:
        return board, []

    middle = board.rows // 2
    doomed: set[Coordinate] = set()
    moves: list[tuple[Coordinate, Coordinate, Piece]] = []

    columns: dict[int, list[Coordinate]] = {}
    for square, _ in carts:
        columns.setdefault(square.column, []).append(square)

    for column, squares in columns.items():
        if len(squares) > 1:
            # Both carts charged in one column: everything in it is removed.
            for row in range(board.rows):
                here = Coordinate(row, column)
                if board.piece_at(here) is not None:
                    doomed.add(here)
            continue

        origin = squares[0]
        if origin.row == middle:
            continue

        target_row = 0 if origin.row > middle else board.rows - 1
        step = 1 if target_row > origin.row else -1
        for row in range(origin.row + step, target_row + step, step):
            here = Coordinate(row, column)
            if board.piece_at(here) is not None:
                doomed.add(here)
        moves.append((origin, Coordinate(target_row, column), board.require_piece_at(origin)))

    removed = [
        (board.require_piece_at(square).piece_id, board.require_piece_at(square).kind)
        for square in sorted(doomed, key=lambda s: (s.row, s.column))
    ]

    result = _without(board, doomed)
    for origin, target, cart in moves:
        result = result.without_piece(origin).with_piece(target, cart)

    return result, removed


def apply_joey_explosions(board: Board) -> tuple[Board, list[tuple[int, PieceKind]]]:
    """
    Run phase five: detonate any Prince Joey whose row holds a multiple of five.

    Joey and every adjacent piece are removed, friendly or enemy. With two
    Joeys in one row, both are judged before either detonates, so one cannot
    spare the other by thinning the row first.

    Arguments:
        board: The board after energizing.

    Returns:
        The new board and the pieces removed.
    """
    joeys = [square for square, piece in board.pieces() if piece.kind is PieceKind.JOEY]
    if not joeys:
        return board, []

    occupancy_by_row: dict[int, int] = {}
    for square, _ in board.pieces():
        occupancy_by_row[square.row] = occupancy_by_row.get(square.row, 0) + 1

    # Judged for every Joey first, then applied, so one blast cannot spare another.
    detonating = [
        square for square in joeys if occupancy_by_row[square.row] % JOEY_EXPLOSION_DIVISOR == 0
    ]
    if not detonating:
        return board, []

    doomed: set[Coordinate] = set()
    for square in detonating:
        doomed.add(square)
        for neighbour in _neighbours(board, square):
            if board.piece_at(neighbour) is not None:
                doomed.add(neighbour)

    removed = [
        (board.require_piece_at(square).piece_id, board.require_piece_at(square).kind)
        for square in sorted(doomed, key=lambda s: (s.row, s.column))
    ]
    return _without(board, doomed), removed


def run_after_effects(board: Board, links: TransporterLinks) -> AfterEffectReport:
    """
    Run all five after-effect phases in the order the rules require.

    The order is itself a rule: a piece removed by poisoning cannot explode, and
    a rampaging Golf Cart can clear a transporter pad before it energizes.

    Arguments:
        board: The board immediately after a player's move.
        links: The variant's transporter pad mapping.

    Returns:
        A report carrying the final board and what each phase did.
    """
    removed: list[tuple[int, PieceKind]] = []
    promoted: list[tuple[int, PieceKind]] = []

    board, poisoned, empresses = apply_poisoning(board)
    removed.extend(poisoned)
    promoted.extend(empresses)

    board, promotions = apply_promotion(board)
    promoted.extend(promotions)

    board, rampaged = apply_golf_cart_rampage(board)
    removed.extend(rampaged)

    board = apply_transporters(board, links)

    board, exploded = apply_joey_explosions(board)
    removed.extend(exploded)

    return AfterEffectReport(board=board, removed=tuple(removed), promoted=tuple(promoted))
