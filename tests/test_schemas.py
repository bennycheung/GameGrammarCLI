"""Tests for game schema definitions."""

import pytest
from pydantic import ValidationError

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


class TestMechanismType:
    """Tests for MechanismType enum."""

    def test_mechanism_values(self):
        """Test that mechanism values are strings."""
        assert MechanismType.DECK_BUILDING.value == "deck_building"
        assert MechanismType.WORKER_PLACEMENT.value == "worker_placement"

    def test_get_category(self):
        """Test category lookup."""
        assert MechanismType.get_category(MechanismType.DECK_BUILDING) == "Cards / Deck"
        assert MechanismType.get_category(MechanismType.WORKER_PLACEMENT) == "Action Selection"
        assert MechanismType.get_category(MechanismType.AREA_CONTROL) == "Conflict / Territory"

    def test_by_category(self):
        """Test grouping by category."""
        categories = MechanismType.by_category()
        assert "Cards / Deck" in categories
        assert MechanismType.DECK_BUILDING in categories["Cards / Deck"]

    def test_description(self):
        """Test mechanism descriptions."""
        assert "deck" in MechanismType.DECK_BUILDING.description.lower()
        assert "workers" in MechanismType.WORKER_PLACEMENT.description.lower()


class TestComponents:
    """Tests for component schemas."""

    def test_card_component(self):
        """Test CardComponent creation."""
        card = CardComponent(
            name="Action Cards",
            count=52,
            purpose="Drive player actions",
            unique=True,
        )
        assert card.name == "Action Cards"
        assert card.count == 52
        assert card.unique is True

    def test_card_component_validation(self):
        """Test CardComponent validation."""
        with pytest.raises(ValidationError):
            CardComponent(name="Cards", count=0, purpose="Test")  # count must be >= 1

    def test_token_component(self):
        """Test TokenComponent creation."""
        token = TokenComponent(
            name="Victory Points",
            count=50,
            purpose="Track scores",
        )
        assert token.name == "Victory Points"
        assert token.count == 50

    def test_dice_component(self):
        """Test DiceComponent creation."""
        dice = DiceComponent(
            type="d6",
            count=2,
            purpose="Determine actions",
        )
        assert dice.type == "d6"
        assert dice.count == 2

    def test_component_set(self):
        """Test ComponentSet creation."""
        components = ComponentSet(
            board="A hexagonal grid representing the cosmos",
            board_type=BoardType.MODULAR,
            cards=[
                CardComponent(name="Star Cards", count=60, purpose="Discoveries")
            ],
            tokens=[
                TokenComponent(name="Discovery Tokens", count=30, purpose="Claim")
            ],
        )
        assert components.has_board is True
        assert components.has_cards is True
        assert components.has_dice is False

    def test_component_set_empty(self):
        """Test empty ComponentSet."""
        components = ComponentSet()
        assert components.has_board is False
        assert components.has_cards is False
        assert components.has_dice is False


class TestPlayerDynamics:
    """Tests for PlayerDynamics schema."""

    def test_player_dynamics(self):
        """Test PlayerDynamics creation."""
        players = PlayerDynamics(
            min_players=2,
            max_players=4,
            recommended=3,
            interaction=InteractionType.COMPETITIVE,
        )
        assert players.min_players == 2
        assert players.max_players == 4
        assert players.recommended == 3

    def test_player_dynamics_validation(self):
        """Test PlayerDynamics validation."""
        # max < min should fail
        with pytest.raises(ValueError):
            PlayerDynamics(min_players=4, max_players=2)

        # recommended outside range should fail
        with pytest.raises(ValueError):
            PlayerDynamics(min_players=2, max_players=4, recommended=5)

    def test_player_dynamics_defaults(self):
        """Test PlayerDynamics defaults."""
        players = PlayerDynamics()
        assert players.min_players == 2
        assert players.max_players == 4
        assert players.interaction == InteractionType.COMPETITIVE


class TestGameOntology:
    """Tests for GameOntology schema."""

    @pytest.fixture
    def valid_game(self):
        """Create a valid game ontology."""
        return GameOntology(
            title="Stellar Cartographers",
            tagline="Chart the cosmos, claim your fame",
            theme="Rival astronomers racing to name celestial objects",
            game_type=GameType.STRATEGY,
            complexity=Complexity.MEDIUM,
            goal="Accumulate the most prestige by naming celestial objects",
            end_condition="Game ends when the star deck is exhausted",
            victory_condition="Player with most prestige points wins",
            primary_mechanisms=[
                MechanismType.SET_COLLECTION,
                MechanismType.HAND_MANAGEMENT,
            ],
            turn_structure=TurnStructure(
                phases=["Draw", "Play", "Score"],
                actions_per_turn="2 actions from: Draw, Play, or Discover",
            ),
            uncertainty_sources=[UncertaintySource.CARDS],
            components=ComponentSet(
                cards=[
                    CardComponent(
                        name="Star Cards",
                        count=60,
                        purpose="Celestial objects to discover",
                    )
                ],
                tokens=[
                    TokenComponent(
                        name="Prestige",
                        count=50,
                        purpose="Track victory points",
                    )
                ],
            ),
            players=PlayerDynamics(
                min_players=2,
                max_players=4,
                interaction=InteractionType.COMPETITIVE,
            ),
            setup="Shuffle star deck, deal 5 cards to each player",
            core_loop="Draw cards, form constellations, claim discoveries",
        )

    def test_game_creation(self, valid_game):
        """Test valid game creation."""
        assert valid_game.title == "Stellar Cartographers"
        assert GameType.STRATEGY == valid_game.game_type
        assert len(valid_game.primary_mechanisms) == 2

    def test_all_mechanisms(self, valid_game):
        """Test all_mechanisms property."""
        valid_game.secondary_mechanisms = [MechanismType.DRAFTING]
        all_mechs = valid_game.all_mechanisms
        assert len(all_mechs) == 3
        assert MechanismType.DRAFTING in all_mechs

    def test_to_summary(self, valid_game):
        """Test summary generation."""
        summary = valid_game.to_summary()
        assert "Stellar Cartographers" in summary
        assert "2-4 players" in summary
        assert "strategy" in summary.lower()

    def test_game_validation_missing_title(self):
        """Test that missing title fails validation."""
        with pytest.raises(ValidationError):
            GameOntology(
                title="",  # Empty title
                theme="Test theme",
                game_type=GameType.STRATEGY,
                goal="Test goal",
                end_condition="Test end",
                victory_condition="Test victory",
                primary_mechanisms=[MechanismType.DECK_BUILDING],
                turn_structure=TurnStructure(phases=["Test"]),
                components=ComponentSet(),
                players=PlayerDynamics(),
                setup="Test setup",
                core_loop="Test loop",
            )

    def test_game_validation_no_mechanisms(self):
        """Test that no mechanisms fails validation."""
        with pytest.raises(ValidationError):
            GameOntology(
                title="Test Game",
                theme="Test theme",
                game_type=GameType.STRATEGY,
                goal="Test goal",
                end_condition="Test end",
                victory_condition="Test victory",
                primary_mechanisms=[],  # Empty
                turn_structure=TurnStructure(phases=["Test"]),
                components=ComponentSet(),
                players=PlayerDynamics(),
                setup="Test setup",
                core_loop="Test loop",
            )


class TestTurnStructure:
    """Tests for TurnStructure schema."""

    def test_turn_structure(self):
        """Test TurnStructure creation."""
        turn = TurnStructure(
            phases=["Draw", "Action", "End"],
            actions_per_turn="2 actions",
        )
        assert len(turn.phases) == 3
        assert turn.actions_per_turn == "2 actions"

    def test_turn_structure_no_phases(self):
        """Test that empty phases fails."""
        with pytest.raises(ValidationError):
            TurnStructure(phases=[])
