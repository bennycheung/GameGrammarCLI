"""Tests for game generation (requires API key for full tests)."""

import os

import pytest

# Skip all tests in this module if no API key is available
pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"),
    reason="No API key available for generation tests",
)


class TestSinglePassGenerator:
    """Tests for SinglePassGenerator (requires API)."""

    @pytest.fixture
    def configured_dspy(self):
        """Configure DSPy for testing."""
        import dspy

        api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
        if os.getenv("ANTHROPIC_API_KEY"):
            lm = dspy.LM("anthropic/claude-3-haiku-20240307", api_key=api_key)
        else:
            lm = dspy.LM("openai/gpt-4o-mini", api_key=api_key)
        dspy.configure(lm=lm)
        return lm

    @pytest.mark.slow
    def test_single_pass_generation(self, configured_dspy):
        """Test single-pass game generation."""
        from gamegrammar.agents.pipeline import SinglePassGenerator
        from gamegrammar.schemas.game import GameOntology

        generator = SinglePassGenerator()
        game = generator(
            theme="Space exploration",
            constraints="2-4 players, competitive, light complexity",
        )

        assert isinstance(game, GameOntology)
        assert len(game.title) > 0
        assert len(game.primary_mechanisms) > 0

    @pytest.mark.slow
    def test_generated_game_validates(self, configured_dspy):
        """Test that generated game passes validation."""
        from gamegrammar.agents.pipeline import SinglePassGenerator
        from gamegrammar.validation.validator import OntologyValidator

        generator = SinglePassGenerator()
        game = generator(
            theme="Medieval trading",
            constraints="2-4 players, competitive, medium complexity",
        )

        validator = OntologyValidator()
        result = validator.validate(game)

        # Should have no errors (warnings are OK)
        assert len(result.errors) == 0


class TestMechanismParsing:
    """Tests for mechanism parsing (no API needed)."""

    def test_parse_mechanisms(self):
        """Test mechanism string parsing."""
        from gamegrammar.agents.pipeline import SinglePassGenerator

        generator = SinglePassGenerator()

        # Test normal parsing
        mechs = generator._parse_mechanisms("deck_building, hand_management")
        assert len(mechs) == 2

        # Test with spaces
        mechs = generator._parse_mechanisms("deck building, hand management")
        assert len(mechs) == 2

        # Test empty
        mechs = generator._parse_mechanisms("")
        assert len(mechs) == 0

        # Test none
        mechs = generator._parse_mechanisms("none")
        assert len(mechs) == 0

    def test_parse_uncertainty_sources(self):
        """Test uncertainty source parsing."""
        from gamegrammar.agents.pipeline import SinglePassGenerator

        generator = SinglePassGenerator()

        sources = generator._parse_uncertainty_sources("dice, cards")
        assert len(sources) == 2

        sources = generator._parse_uncertainty_sources("none")
        assert len(sources) == 0

    def test_parse_list(self):
        """Test comma-separated list parsing."""
        from gamegrammar.agents.pipeline import SinglePassGenerator

        generator = SinglePassGenerator()

        items = generator._parse_list("one, two, three")
        assert items == ["one", "two", "three"]

        items = generator._parse_list("none")
        assert items == []


class TestMultiAgentPipeline:
    """Tests for MultiAgentOntologyPipeline (requires API)."""

    @pytest.fixture
    def configured_dspy(self):
        """Configure DSPy for testing."""
        import dspy

        api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
        if os.getenv("ANTHROPIC_API_KEY"):
            lm = dspy.LM("anthropic/claude-3-haiku-20240307", api_key=api_key)
        else:
            lm = dspy.LM("openai/gpt-4o-mini", api_key=api_key)
        dspy.configure(lm=lm)
        return lm

    @pytest.mark.slow
    def test_multi_agent_pipeline(self, configured_dspy):
        """Test multi-agent pipeline generation."""
        from gamegrammar.agents.pipeline import MultiAgentOntologyPipeline
        from gamegrammar.schemas.game import GameOntology

        pipeline = MultiAgentOntologyPipeline()
        results = pipeline(
            theme="Pirate treasure hunting",
            constraints="2-4 players, competitive, medium complexity",
        )

        assert "ontology" in results
        assert "mechanics" in results
        assert "theme" in results
        assert "components" in results

        game = results["ontology"]
        assert isinstance(game, GameOntology)
        assert len(game.title) > 0

    @pytest.mark.slow
    def test_pipeline_with_callback(self, configured_dspy):
        """Test pipeline with progress callback."""
        from gamegrammar.agents.pipeline import MultiAgentOntologyPipeline

        stages_called = []

        def callback(stage: str, data):
            stages_called.append(stage)

        pipeline = MultiAgentOntologyPipeline()
        pipeline(
            theme="City building",
            constraints="2-4 players",
            progress_callback=callback,
        )

        assert "mechanics" in stages_called
        assert "theme" in stages_called
        assert "components" in stages_called

    def test_parse_player_counts(self):
        """Test player count extraction from constraints."""
        from gamegrammar.agents.pipeline import MultiAgentOntologyPipeline

        pipeline = MultiAgentOntologyPipeline()

        # Test range format
        min_p, max_p = pipeline._parse_player_counts("2-4 players, competitive")
        assert min_p == 2
        assert max_p == 4

        # Test "to" format
        min_p, max_p = pipeline._parse_player_counts("2 to 6 players")
        assert min_p == 2
        assert max_p == 6

        # Test single number
        min_p, max_p = pipeline._parse_player_counts("4 player game")
        assert min_p == 4
        assert max_p == 4

        # Test default
        min_p, max_p = pipeline._parse_player_counts("competitive strategy")
        assert min_p == 2
        assert max_p == 4

    def test_parse_interaction(self):
        """Test interaction type inference from constraints."""
        from gamegrammar.agents.pipeline import MultiAgentOntologyPipeline
        from gamegrammar.schemas.components import InteractionType

        pipeline = MultiAgentOntologyPipeline()

        interaction = pipeline._parse_interaction_from_constraints("cooperative game")
        assert interaction == InteractionType.COOPERATIVE

        interaction = pipeline._parse_interaction_from_constraints("team-based")
        assert interaction == InteractionType.TEAM_BASED

        interaction = pipeline._parse_interaction_from_constraints("solo game")
        assert interaction == InteractionType.SOLO

        interaction = pipeline._parse_interaction_from_constraints("competitive")
        assert interaction == InteractionType.COMPETITIVE
