from __future__ import annotations

from dataclasses import replace

from ..board import Board
from ..coordinates import Coordinate
from ..enums import PieceKind, Terrain
from ..errors import InvariantViolation
from ..pieces.base import Piece
from ..pieces.registry import build_rule

TransporterLinks = dict[Coordinate, Coordinate]


def jet_pack_landing(piece: Piece) -> Piece:
    """
    Give the piece as it stands after landing on a jet pack square.

    A King becomes a Jet Pack King, keeping its identity, colour and
    first-move state. Its movement rule is rebuilt, because the new kind moves
    differently. Every other piece is returned unchanged.

    The jet pack is not consumed. This function takes a piece and returns a
    piece, touching no board state, so the square it came from is unaffected
    and the other player's King can be upgraded by it later.

    Arguments:
        piece: The piece that landed on the jet pack.

    Returns:
        The upgraded piece, or the same piece when no upgrade applies.
    """
    if piece.kind is not PieceKind.KING:
        return piece

    return replace(
        piece,
        kind=PieceKind.JET_PACK_KING,
        movement=build_rule(PieceKind.JET_PACK_KING),
    )


def occupied_pads(board: Board, links: TransporterLinks) -> TransporterLinks:
    """
    Give the subset of transporter links whose source square holds a piece.

    Arguments:
        board: The board to read.
        links: Every pad on this board and where it leads.

    Returns:
        Only the links that will actually move a piece.
    """
    return {
        source: target for source, target in links.items() if board.piece_at(source) is not None
    }


def apply_transporters(board: Board, links: TransporterLinks) -> Board:
    """
    Move every piece resting on a transporter pad, all at once.

    Simultaneity is why this cannot be a sequence of individual relocations: a
    piece moving to a pad that is still occupied would collide, even though the
    occupant is about to leave. Every piece is lifted first, then every piece is
    placed.

    Arguments:
        board: The board to transport pieces on. Never modified.
        links: Every pad on this board and where it leads.

    Returns:
        A new board with the pad occupants relocated. The same board when no
        pad is occupied.
    """
    moving = occupied_pads(board, links)
    if not moving:
        return board

    travellers = {target: board.require_piece_at(source) for source, target in moving.items()}

    lifted = board
    for source in moving:
        lifted = lifted.without_piece(source)

    landed = lifted
    for target, piece in travellers.items():
        if not landed.is_empty(target):
            raise InvariantViolation(
                f"transporter target {target} is occupied after lifting; "
                "links must be a permutation of the pad squares"
            )
        landed = landed.with_piece(target, piece)

    return landed


def validate_links(board: Board, links: TransporterLinks) -> None:
    """
    Assert that a set of transporter links is usable on a board.

    Three properties must hold. Every square involved must be in bounds and be
    a transporter pad, and the links must form a permutation: each pad appears
    exactly once as a source and exactly once as a target. Without the
    permutation property, two pieces could be sent to one square.

    Arguments:
        board: The board the links describe.
        links: Every pad on this board and where it leads.
    """
    sources = set(links)
    targets = set(links.values())

    if len(targets) != len(links):
        raise InvariantViolation("two transporter pads lead to the same square")

    if sources != targets:
        raise InvariantViolation(
            f"transporter links are not a permutation: sources {sorted_squares(sources)} "
            f"but targets {sorted_squares(targets)}"
        )

    for square in sources:
        if not board.contains(square):
            raise InvariantViolation(f"transporter link references off-board square {square}")
        terrain = board.cell_at(square).terrain
        if terrain is not Terrain.TRANSPORTER_PAD:
            raise InvariantViolation(f"transporter link references {terrain.name} square {square}")

    pads = {
        square
        for square in board.dimensions.squares()
        if board.cell_at(square).terrain is Terrain.TRANSPORTER_PAD
    }
    if pads != sources:
        raise InvariantViolation(
            f"board has pads {sorted_squares(pads)} but links cover {sorted_squares(sources)}"
        )


def sorted_squares(squares: set[Coordinate]) -> list[tuple[int, int]]:
    """
    Render a set of squares in a stable order for error messages.

    Arguments:
        squares: The squares to render.

    Returns:
        Row and column pairs sorted in reading order.
    """
    return sorted((square.row, square.column) for square in squares)
