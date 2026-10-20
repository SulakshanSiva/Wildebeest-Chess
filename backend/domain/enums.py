from __future__ import annotations

from enum import Enum, StrEnum, auto


class Color(StrEnum):
    """
    The two sides, serialised as "white" and "black".
    """

    WHITE = "white"
    BLACK = "black"

    @property
    def opponent(self) -> Color:
        """
        Give the opposing colour.

        Returns:
            The other member of this enum.
        """
        return Color.BLACK if self is Color.WHITE else Color.WHITE

    @property
    def forward(self) -> int:
        """
        Give the row delta a pawn of this colour advances by.

        White starts on rows 0-1 and advances toward row 10, so white is +1.

        Returns:
            1 for white, -1 for black.
        """
        return 1 if self is Color.WHITE else -1


class PieceKind(StrEnum):
    """
    Stable identity of a piece type, independent of its layout character.
    """

    PAWN = "pawn"
    BISHOP = "bishop"
    KNIGHT = "knight"
    ROOK = "rook"
    KING = "king"
    JET_PACK_KING = "jet_pack_king"
    JOEY = "joey"
    TIME_MACHINE = "time_machine"
    SERPENT = "serpent"
    OLD_WOMAN = "old_woman"
    GRAND_EMPRESS = "grand_empress"
    GOLF_CART = "golf_cart"
    BEEKEEPER = "beekeeper"
    GORILLA = "gorilla"
    CATAPULT = "catapult"

    @property
    def is_royal(self) -> bool:
        """
        Say whether capturing this piece ends the game.

        "King" in the rules covers the King with a Jet Pack, so both count for
        the win condition and for the fling protection that spares a King.

        Returns:
            True for the King and the Jet Pack King.
        """
        return self in (PieceKind.KING, PieceKind.JET_PACK_KING)

    @property
    def can_be_captured(self) -> bool:
        """
        Say whether a move can capture this piece.

        The rules say a Gorilla "does not capture, nor can it be captured". No
        move, step or fling may land on one to take it; only poison and a Golf
        Cart rampage, which are after-effects rather than moves, remove one.

        Returns:
            False for the Gorilla, True for every other kind.
        """
        return self is not PieceKind.GORILLA

    @property
    def is_hovering(self) -> bool:
        """
        Say whether this piece hovers above the board.

        A hovering piece cannot be pushed by a Gorilla, and a flung piece
        passes over it rather than being stopped by it.

        Returns:
            True for the Jet Pack King, which is the only hovering piece.
        """
        return self is PieceKind.JET_PACK_KING

    @property
    def poisons(self) -> bool:
        """
        Say whether this piece poisons adjacent opposing pieces.

        Poisoning is the first after-effect phase. The Grand Empress inherits
        it from the Serpent she is built from.

        Returns:
            True for the Serpent and the Grand Empress.
        """
        return self in (PieceKind.SERPENT, PieceKind.GRAND_EMPRESS)


class Terrain(Enum):
    """
    What a square is, independent of what stands on it.

    All three terrains are passable; the special squares act on a piece that
    lands on them rather than restricting which pieces may enter.

    JET_PACK upgrades a King that lands on it into a Jet Pack King. That is how
    a Jet Pack King enters play, which is why no "W" appears in the starting
    layout. The square is not consumed: both players' Kings can take it, and it
    stays a jet pack afterwards, so this terrain never changes during a game.

    TRANSPORTER_PAD relocates the piece resting on it. Where each pad leads is
    a property of the board rather than of the terrain, so the mapping lives on
    the Variant.
    """

    NORMAL = "."
    JET_PACK = "#"
    TRANSPORTER_PAD = "*"

    @property
    def symbol(self) -> str:
        """
        Give the layout character for this terrain.

        Returns:
            The single character used in a starting layout.
        """
        return self.value

    @property
    def is_passable(self) -> bool:
        """
        Say whether a piece may occupy this square at all.

        Returns:
            True for every terrain. The special squares act on a piece that
            lands on them; they never block entry.
        """
        return True


class MoveAction(Enum):
    """
    How a move changes the board.

    The applier reads this to decide what to resolve; see the Move docstring
    for how each action populates the move's squares.

    CRUSH is the Gorilla's push into a square whose own destination is blocked.
    The rules say the pushed piece is captured rather than relocated, so it is
    a distinct outcome from PUSH and not a kind of CAPTURE: the Gorilla never
    captures by moving onto a piece.
    """

    MOVE = auto()
    CAPTURE = auto()
    PUSH = auto()
    CRUSH = auto()
    FLING = auto()


class RemovalCause(Enum):
    """
    How a piece left the board during a turn.

    The first three come from the move itself; the rest from the after-effect
    phases, which can remove pieces of either colour. FLING is a capture by a
    flung piece landing on its victim.
    """

    CAPTURE = auto()
    CRUSH = auto()
    FLING = auto()
    POISON = auto()
    RAMPAGE = auto()
    EXPLOSION = auto()


class GameStatus(Enum):
    """
    Outcome state of a game.

    A side wins by capturing the opposing King. A draw is both Kings falling
    together, or a side left with no legal move.
    """

    ACTIVE = auto()
    WHITE_WINS = auto()
    BLACK_WINS = auto()
    DRAW = auto()

    @property
    def is_over(self) -> bool:
        """
        Say whether the game has finished.

        Returns:
            True for every status except ACTIVE.
        """
        return self is not GameStatus.ACTIVE


class EndReason(Enum):
    """
    Why a game finished.

    KING_CAPTURED covers every way a King can fall, including poison, a Golf
    Cart rampage, an explosion and a crush, and a simultaneous loss of both
    Kings, which is a draw. NO_LEGAL_MOVES is the one ending the rules never
    mention. It is treated as a draw so a game cannot hang.
    """

    KING_CAPTURED = auto()
    RESIGNATION = auto()
    NO_LEGAL_MOVES = auto()
