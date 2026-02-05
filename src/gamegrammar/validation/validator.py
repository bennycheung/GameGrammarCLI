"""Validation system for game ontologies."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from gamegrammar.schemas.components import InteractionType
from gamegrammar.schemas.game import GameOntology, UncertaintySource
from gamegrammar.schemas.mechanisms import MechanismType


class Severity(str, Enum):
    """Severity of validation issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A single validation issue."""

    message: str
    severity: Severity
    field: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of validating a game ontology."""

    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        """Get only error-level issues."""
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """Get only warning-level issues."""
        return [i for i in self.issues if i.severity == Severity.WARNING]

    def add_error(
        self, message: str, field: Optional[str] = None, suggestion: Optional[str] = None
    ) -> None:
        """Add an error."""
        self.issues.append(
            ValidationIssue(message, Severity.ERROR, field, suggestion)
        )
        self.valid = False

    def add_warning(
        self, message: str, field: Optional[str] = None, suggestion: Optional[str] = None
    ) -> None:
        """Add a warning."""
        self.issues.append(
            ValidationIssue(message, Severity.WARNING, field, suggestion)
        )

    def add_info(
        self, message: str, field: Optional[str] = None, suggestion: Optional[str] = None
    ) -> None:
        """Add an info."""
        self.issues.append(
            ValidationIssue(message, Severity.INFO, field, suggestion)
        )


class OntologyValidator:
    """Validates game ontologies for consistency and playability."""

    def validate(self, game: GameOntology) -> ValidationResult:
        """Run all validation checks on a game ontology."""
        result = ValidationResult(valid=True)

        self._check_goal_clarity(game, result)
        self._check_mechanism_requirements(game, result)
        self._check_type_consistency(game, result)
        self._check_playability(game, result)
        self._check_component_consistency(game, result)
        self._check_player_consistency(game, result)

        return result

    def _check_goal_clarity(self, game: GameOntology, result: ValidationResult) -> None:
        """Check that the goal is specific and actionable."""
        vague_terms = ["win", "beat", "best", "most", "highest"]
        goal_lower = game.goal.lower()

        if len(game.goal) < 20:
            result.add_warning(
                "Goal description is very short",
                field="goal",
                suggestion="Add more detail about what players are trying to achieve",
            )

        # Check if goal is just "win the game" or similar
        if any(goal_lower == f"{term} the game" for term in vague_terms):
            result.add_error(
                "Goal is too vague - it just says to win",
                field="goal",
                suggestion="Describe the specific objective players pursue",
            )

    def _check_mechanism_requirements(
        self, game: GameOntology, result: ValidationResult
    ) -> None:
        """Check that mechanisms have required components."""
        all_mechs = game.all_mechanisms

        # Deck building requires cards
        if MechanismType.DECK_BUILDING in all_mechs:
            if not game.components.has_cards:
                result.add_error(
                    "Deck building mechanism requires cards",
                    field="components.cards",
                    suggestion="Add at least one card deck to components",
                )

        # Hand management requires cards
        if MechanismType.HAND_MANAGEMENT in all_mechs:
            if not game.components.has_cards:
                result.add_error(
                    "Hand management mechanism requires cards",
                    field="components.cards",
                    suggestion="Add cards to components",
                )

        # Card-driven requires cards
        if MechanismType.CARD_DRIVEN in all_mechs:
            if not game.components.has_cards:
                result.add_error(
                    "Card-driven mechanism requires cards",
                    field="components.cards",
                    suggestion="Add cards to components",
                )

        # Dice-driven requires dice
        if MechanismType.DICE_DRIVEN in all_mechs:
            if not game.components.has_dice:
                result.add_error(
                    "Dice-driven mechanism requires dice",
                    field="components.dice",
                    suggestion="Add dice to components",
                )

        # Dice uncertainty should have dice
        if UncertaintySource.DICE in game.uncertainty_sources:
            if not game.components.has_dice:
                result.add_warning(
                    "Dice listed as uncertainty source but no dice in components",
                    field="components.dice",
                    suggestion="Add dice to components or remove dice from uncertainty sources",
                )

        # Area control/movement typically needs a board
        area_mechs = {
            MechanismType.AREA_CONTROL,
            MechanismType.AREA_MOVEMENT,
            MechanismType.WORKER_PLACEMENT,
        }
        if any(m in all_mechs for m in area_mechs):
            if not game.components.has_board:
                result.add_warning(
                    "Area-based mechanisms typically require a board",
                    field="components.board_type",
                    suggestion="Consider adding a board or explain how areas are represented",
                )

    def _check_type_consistency(
        self, game: GameOntology, result: ValidationResult
    ) -> None:
        """Check that game type is consistent with mechanisms."""
        all_mechs = game.all_mechanisms

        # Cooperative games shouldn't have direct conflict
        if game.players.interaction == InteractionType.COOPERATIVE:
            conflict_mechs = {MechanismType.COMBAT, MechanismType.AREA_CONTROL}
            if any(m in all_mechs for m in conflict_mechs):
                result.add_warning(
                    "Cooperative game has direct conflict mechanisms",
                    field="players.interaction",
                    suggestion="Consider if conflict is against the game or between players",
                )

            # Should have cooperative mechanism
            if MechanismType.COOPERATIVE not in all_mechs:
                result.add_info(
                    "Cooperative game type but no cooperative mechanism listed",
                    field="primary_mechanisms",
                    suggestion="Consider adding COOPERATIVE to mechanisms",
                )

        # Competitive games with negotiation
        if (
            game.players.interaction == InteractionType.COMPETITIVE
            and MechanismType.NEGOTIATION in all_mechs
        ):
            result.add_info(
                "Competitive game with negotiation - ensure betrayal is possible",
                field="primary_mechanisms",
            )

    def _check_playability(self, game: GameOntology, result: ValidationResult) -> None:
        """Check basic playability requirements."""
        # Must have an end condition
        if len(game.end_condition) < 10:
            result.add_warning(
                "End condition is very brief",
                field="end_condition",
                suggestion="Describe how and when the game ends",
            )

        # Must have uncertainty for interesting play
        if not game.uncertainty_sources:
            result.add_warning(
                "No uncertainty sources listed - game may be solvable",
                field="uncertainty_sources",
                suggestion="Add at least one source of uncertainty for replayability",
            )

        # Turn structure should have actions
        if not game.turn_structure.actions_per_turn:
            result.add_info(
                "Turn structure doesn't specify actions per turn",
                field="turn_structure.actions_per_turn",
                suggestion="Consider specifying what players do on their turn",
            )

    def _check_component_consistency(
        self, game: GameOntology, result: ValidationResult
    ) -> None:
        """Check that components are consistent with game description."""
        # Card uncertainty should have cards
        if UncertaintySource.CARDS in game.uncertainty_sources:
            if not game.components.has_cards:
                result.add_warning(
                    "Cards listed as uncertainty source but no cards in components",
                    field="components.cards",
                )

        # Shuffle uncertainty implies cards
        if UncertaintySource.SHUFFLE in game.uncertainty_sources:
            if not game.components.has_cards:
                result.add_warning(
                    "Shuffle listed as uncertainty but no cards to shuffle",
                    field="uncertainty_sources",
                )

    def _check_player_consistency(
        self, game: GameOntology, result: ValidationResult
    ) -> None:
        """Check player configuration consistency."""
        # Solo games
        if game.players.max_players == 1:
            if game.players.interaction not in {InteractionType.SOLO, InteractionType.COOPERATIVE}:
                result.add_warning(
                    "Single-player game should be solo or cooperative (vs game)",
                    field="players.interaction",
                )

        # Asymmetric games should have roles
        if game.players.interaction == InteractionType.ASYMMETRIC:
            if not game.players.roles:
                result.add_warning(
                    "Asymmetric game should define player roles",
                    field="players.roles",
                    suggestion="List the different roles players can have",
                )

        # Team games should have structure
        if game.players.interaction == InteractionType.TEAM_BASED:
            if not game.players.team_structure:
                result.add_warning(
                    "Team-based game should define team structure",
                    field="players.team_structure",
                    suggestion="Describe how teams are formed/divided",
                )
