"""Component and player dynamics schemas for game ontology."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class InteractionType(str, Enum):
    """Types of player interaction."""

    COOPERATIVE = "cooperative"
    COMPETITIVE = "competitive"
    TEAM_BASED = "team_based"
    SEMI_COOPERATIVE = "semi_cooperative"
    ASYMMETRIC = "asymmetric"
    SOLO = "solo"


class BoardType(str, Enum):
    """Types of game boards."""

    NONE = "none"
    FIXED = "fixed"
    MODULAR = "modular"
    PLAYER_BUILT = "player_built"
    TRACK = "track"


class CardComponent(BaseModel):
    """Specification for a deck of cards."""

    name: str = Field(..., description="Name of this card type/deck")
    count: int = Field(..., ge=1, description="Number of cards in deck")
    purpose: str = Field(..., description="What these cards do in the game")
    unique: bool = Field(
        default=False, description="Whether each card is unique or duplicates exist"
    )


class TokenComponent(BaseModel):
    """Specification for tokens/markers."""

    name: str = Field(..., description="Name of this token type")
    count: int = Field(..., ge=1, description="Number of tokens")
    purpose: str = Field(..., description="What these tokens represent")


class DiceComponent(BaseModel):
    """Specification for dice."""

    type: str = Field(..., description="Type of die (d6, d8, custom, etc.)")
    count: int = Field(default=1, ge=1, description="Number of dice")
    purpose: str = Field(..., description="What these dice are used for")


class ComponentSet(BaseModel):
    """Complete set of physical components for a game."""

    board: Optional[str] = Field(
        default=None, description="Description of the game board, if any"
    )
    board_type: BoardType = Field(
        default=BoardType.NONE, description="Type of board used"
    )
    cards: list[CardComponent] = Field(
        default_factory=list, description="Card decks in the game"
    )
    tokens: list[TokenComponent] = Field(
        default_factory=list, description="Token types in the game"
    )
    dice: list[DiceComponent] = Field(
        default_factory=list, description="Dice used in the game"
    )
    other: list[str] = Field(
        default_factory=list, description="Other components (meeples, boards, etc.)"
    )

    @property
    def has_cards(self) -> bool:
        """Check if the game has any cards."""
        return len(self.cards) > 0

    @property
    def has_dice(self) -> bool:
        """Check if the game has any dice."""
        return len(self.dice) > 0

    @property
    def has_board(self) -> bool:
        """Check if the game has a board."""
        return self.board_type != BoardType.NONE


class PlayerDynamics(BaseModel):
    """Player count and interaction model."""

    min_players: int = Field(default=2, ge=1, description="Minimum player count")
    max_players: int = Field(default=4, ge=1, description="Maximum player count")
    recommended: Optional[int] = Field(
        default=None, description="Recommended player count"
    )
    interaction: InteractionType = Field(
        default=InteractionType.COMPETITIVE, description="Primary interaction type"
    )
    roles: Optional[list[str]] = Field(
        default=None, description="Named roles if asymmetric"
    )
    team_structure: Optional[str] = Field(
        default=None, description="Team structure if team-based"
    )

    def model_post_init(self, __context) -> None:
        """Validate player counts."""
        if self.max_players < self.min_players:
            raise ValueError("max_players must be >= min_players")
        if self.recommended is not None:
            if self.recommended < self.min_players or self.recommended > self.max_players:
                raise ValueError("recommended must be within player range")
