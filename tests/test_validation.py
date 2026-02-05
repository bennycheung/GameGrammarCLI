"""Tests for the validation system."""

import pytest

from gamegrammar.schemas.components import (
    BoardType,
    CardComponent,
    ComponentSet,
    DiceComponent,
    InteractionType,
    PlayerDynamics,
    TokenComponent,
)
from gamegrammar.schemas.game import (
    Complexity,
    GameOntology,
    GameType,
    TurnStructure,
    UncertaintySource,
)
from gamegrammar.schemas.mechanisms import MechanismType
from gamegrammar.validation.validator import OntologyValidator, Severity


class TestOntologyValidator:
    """Tests for OntologyValidator."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return OntologyValidator()

    @pytest.fixture
    def base_game(self):
        """Create a base valid game for modification."""
        return GameOntology(
            title="Test Game",
            theme="A test game for validation",
            game_type=GameType.STRATEGY,
            complexity=Complexity.MEDIUM,
            goal="Accumulate the most points through strategic card play",
            end_condition="Game ends when the deck is exhausted",
            victory_condition="Highest score wins",
            primary_mechanisms=[MechanismType.HAND_MANAGEMENT],
            turn_structure=TurnStructure(
                phases=["Draw", "Play", "Score"],
                actions_per_turn="Play 1-3 cards",
            ),
            uncertainty_sources=[UncertaintySource.CARDS],
            components=ComponentSet(
                cards=[CardComponent(name="Cards", count=50, purpose="Gameplay")]
            ),
            players=PlayerDynamics(
                min_players=2,
                max_players=4,
                interaction=InteractionType.COMPETITIVE,
            ),
            setup="Shuffle and deal cards",
            core_loop="Draw, play, score",
        )

    def test_valid_game_passes(self, validator, base_game):
        """Test that a valid game passes validation."""
        result = validator.validate(base_game)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_vague_goal_fails(self, validator, base_game):
        """Test that a vague goal triggers error."""
        base_game.goal = "win the game"
        result = validator.validate(base_game)
        assert any(
            "vague" in issue.message.lower()
            for issue in result.issues
            if issue.severity == Severity.ERROR
        )

    def test_deck_building_needs_cards(self, validator, base_game):
        """Test that deck building requires cards."""
        base_game.primary_mechanisms = [MechanismType.DECK_BUILDING]
        base_game.components = ComponentSet()  # No cards
        result = validator.validate(base_game)
        assert result.valid is False
        assert any(
            "deck building" in issue.message.lower() and "cards" in issue.message.lower()
            for issue in result.errors
        )

    def test_dice_driven_needs_dice(self, validator, base_game):
        """Test that dice-driven requires dice."""
        base_game.primary_mechanisms = [MechanismType.DICE_DRIVEN]
        base_game.components = ComponentSet()  # No dice
        result = validator.validate(base_game)
        assert result.valid is False
        assert any("dice" in issue.message.lower() for issue in result.errors)

    def test_card_driven_needs_cards(self, validator, base_game):
        """Test that card-driven requires cards."""
        base_game.primary_mechanisms = [MechanismType.CARD_DRIVEN]
        base_game.components = ComponentSet()  # No cards
        result = validator.validate(base_game)
        assert result.valid is False
        assert any("card" in issue.message.lower() for issue in result.errors)

    def test_area_control_warns_without_board(self, validator, base_game):
        """Test that area control warns without board."""
        base_game.primary_mechanisms = [MechanismType.AREA_CONTROL]
        base_game.components = ComponentSet()  # No board
        result = validator.validate(base_game)
        assert any(
            "board" in issue.message.lower()
            for issue in result.warnings
        )

    def test_cooperative_with_combat_warns(self, validator, base_game):
        """Test cooperative game with combat triggers warning."""
        base_game.players = PlayerDynamics(
            min_players=2,
            max_players=4,
            interaction=InteractionType.COOPERATIVE,
        )
        base_game.primary_mechanisms = [MechanismType.COMBAT]
        result = validator.validate(base_game)
        assert any(
            "cooperative" in issue.message.lower() and "conflict" in issue.message.lower()
            for issue in result.warnings
        )

    def test_no_uncertainty_warns(self, validator, base_game):
        """Test that no uncertainty sources triggers warning."""
        base_game.uncertainty_sources = []
        result = validator.validate(base_game)
        assert any(
            "uncertainty" in issue.message.lower()
            for issue in result.warnings
        )

    def test_dice_uncertainty_without_dice_warns(self, validator, base_game):
        """Test dice uncertainty without dice component warns."""
        base_game.uncertainty_sources = [UncertaintySource.DICE]
        base_game.components = ComponentSet()  # No dice
        result = validator.validate(base_game)
        assert any(
            "dice" in issue.message.lower()
            for issue in result.warnings
        )

    def test_asymmetric_without_roles_warns(self, validator, base_game):
        """Test asymmetric game without roles warns."""
        base_game.players = PlayerDynamics(
            min_players=2,
            max_players=4,
            interaction=InteractionType.ASYMMETRIC,
            roles=None,
        )
        result = validator.validate(base_game)
        assert any(
            "asymmetric" in issue.message.lower() and "roles" in issue.message.lower()
            for issue in result.warnings
        )

    def test_team_based_without_structure_warns(self, validator, base_game):
        """Test team-based game without structure warns."""
        base_game.players = PlayerDynamics(
            min_players=4,
            max_players=6,
            interaction=InteractionType.TEAM_BASED,
            team_structure=None,
        )
        result = validator.validate(base_game)
        assert any(
            "team" in issue.message.lower() and "structure" in issue.message.lower()
            for issue in result.warnings
        )

    def test_solo_game_interaction_warns(self, validator, base_game):
        """Test solo game with wrong interaction type warns."""
        base_game.players = PlayerDynamics(
            min_players=1,
            max_players=1,
            interaction=InteractionType.COMPETITIVE,
        )
        result = validator.validate(base_game)
        assert any(
            "single-player" in issue.message.lower() or "solo" in issue.message.lower()
            for issue in result.warnings
        )

    def test_short_goal_warns(self, validator, base_game):
        """Test that a very short goal triggers warning."""
        base_game.goal = "Score points"  # Less than 20 chars
        result = validator.validate(base_game)
        assert any(
            "short" in issue.message.lower() and "goal" in issue.field.lower()
            for issue in result.warnings
        )

    def test_short_end_condition_warns(self, validator, base_game):
        """Test that a very short end condition triggers warning."""
        base_game.end_condition = "Deck out"  # Less than 10 chars
        result = validator.validate(base_game)
        assert any(
            "brief" in issue.message.lower() and "end_condition" in issue.field
            for issue in result.warnings
        )


class TestValidationResult:
    """Tests for ValidationResult."""

    def test_errors_property(self):
        """Test errors property filters correctly."""
        from gamegrammar.validation.validator import ValidationResult

        result = ValidationResult(valid=True)
        result.add_error("Error message")
        result.add_warning("Warning message")
        result.add_info("Info message")

        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert len(result.issues) == 3

    def test_add_error_sets_invalid(self):
        """Test that adding error sets valid to False."""
        from gamegrammar.validation.validator import ValidationResult

        result = ValidationResult(valid=True)
        assert result.valid is True
        result.add_error("Error")
        assert result.valid is False
