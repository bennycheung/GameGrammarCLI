"""Main GameOntology schema for complete game definitions."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .components import ComponentSet, PlayerDynamics
from .mechanisms import MechanismType


class GameType(str, Enum):
    """High-level game type classification."""

    STRATEGY = "strategy"
    PARTY = "party"
    FAMILY = "family"
    THEMATIC = "thematic"
    ABSTRACT = "abstract"
    WAR = "war"
    DEXTERITY = "dexterity"
    EURO = "euro"
    AMERITRASH = "ameritrash"


class UncertaintySource(str, Enum):
    """Sources of uncertainty/randomness in games."""

    NONE = "none"
    DICE = "dice"
    CARDS = "cards"
    HIDDEN_INFORMATION = "hidden_information"
    PLAYER_ACTIONS = "player_actions"
    RANDOMIZED_SETUP = "randomized_setup"
    SHUFFLE = "shuffle"


class Complexity(str, Enum):
    """Game complexity level."""

    LIGHT = "light"
    MEDIUM_LIGHT = "medium_light"
    MEDIUM = "medium"
    MEDIUM_HEAVY = "medium_heavy"
    HEAVY = "heavy"


class TurnStructure(BaseModel):
    """Definition of how turns work in the game."""

    phases: list[str] = Field(
        ..., min_length=1, description="Named phases within a turn"
    )
    actions_per_turn: Optional[str] = Field(
        default=None, description="How many/which actions players take per turn"
    )
    round_structure: Optional[str] = Field(
        default=None, description="How rounds are structured if applicable"
    )


class GameOntology(BaseModel):
    """Complete ontological definition of a board game."""

    # Identity
    title: str = Field(..., min_length=1, description="Name of the game")
    tagline: Optional[str] = Field(
        default=None, description="Short memorable description"
    )

    # Theme & Setting
    theme: str = Field(..., description="Thematic setting and narrative")
    theme_integration: Optional[str] = Field(
        default=None, description="How theme connects to mechanics"
    )

    # Classification
    game_type: GameType = Field(..., description="Primary game type classification")
    complexity: Complexity = Field(
        default=Complexity.MEDIUM, description="Complexity level"
    )

    # Goals & Victory
    goal: str = Field(..., description="What players are trying to achieve")
    end_condition: str = Field(..., description="How the game ends")
    victory_condition: str = Field(..., description="How winners are determined")

    # Core Mechanics
    primary_mechanisms: list[MechanismType] = Field(
        ..., min_length=1, description="Primary game mechanisms"
    )
    secondary_mechanisms: list[MechanismType] = Field(
        default_factory=list, description="Supporting mechanisms"
    )
    turn_structure: TurnStructure = Field(..., description="How turns work")
    uncertainty_sources: list[UncertaintySource] = Field(
        default_factory=list, description="Sources of randomness/uncertainty"
    )

    # Physical Components
    components: ComponentSet = Field(..., description="Physical game components")

    # Players
    players: PlayerDynamics = Field(..., description="Player configuration")

    # Gameplay
    setup: str = Field(..., description="How to set up the game")
    core_loop: str = Field(..., description="The primary gameplay loop")
    strategic_depth: Optional[str] = Field(
        default=None, description="Key strategic considerations"
    )

    # Play Time
    play_time_minutes: Optional[int] = Field(
        default=None, ge=1, description="Expected play time in minutes"
    )

    # Designer Notes
    design_notes: Optional[str] = Field(
        default=None, description="Designer commentary on design choices"
    )
    agency_justification: Optional[str] = Field(
        default=None, description="Why players feel in control of outcomes"
    )

    @property
    def all_mechanisms(self) -> list[MechanismType]:
        """Get all mechanisms (primary + secondary)."""
        return self.primary_mechanisms + self.secondary_mechanisms

    def to_summary(self) -> str:
        """Generate a brief summary of the game."""
        mechanisms = ", ".join(m.value.replace("_", " ") for m in self.primary_mechanisms[:3])
        return (
            f"{self.title}: A {self.complexity.value} {self.game_type.value} game "
            f"for {self.players.min_players}-{self.players.max_players} players "
            f"featuring {mechanisms}. {self.tagline or ''}"
        ).strip()
