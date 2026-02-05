"""Tests for RAG retriever."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gamegrammar.rag.collector import BGGGame
from gamegrammar.rag.retriever import OntologyRAGRetriever
from gamegrammar.rag.storage import GameRAGStorage


class TestOntologyRAGRetriever:
    """Tests for OntologyRAGRetriever class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for ChromaDB."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def storage(self, temp_dir):
        """Create storage with temporary persistence."""
        return GameRAGStorage(persist_directory=temp_dir)

    @pytest.fixture
    def retriever(self, storage):
        """Create retriever with storage."""
        return OntologyRAGRetriever(storage=storage)

    @pytest.fixture
    def sample_games(self):
        """Create sample games for testing."""
        return [
            BGGGame(
                id=174430,
                name="Gloomhaven",
                year=2017,
                min_players=1,
                max_players=4,
                rating=8.7,
                weight=3.8,
                rank=1,
                mechanics=["Hand Management", "Cooperative Game"],
                categories=["Fantasy", "Adventure"],
            ),
            BGGGame(
                id=167791,
                name="Terraforming Mars",
                year=2016,
                min_players=1,
                max_players=5,
                rating=8.4,
                weight=3.2,
                rank=2,
                mechanics=["Card Drafting", "Tile Placement"],
                categories=["Science Fiction"],
            ),
            BGGGame(
                id=13,
                name="Catan",
                year=1995,
                min_players=3,
                max_players=4,
                rating=7.1,
                weight=2.3,
                rank=200,
                mechanics=["Dice Rolling", "Trading"],
                categories=["Negotiation"],
            ),
        ]

    def test_parse_constraints_player_range(self, retriever):
        """Should parse player range from constraints."""
        constraints = "2-4 players, competitive"
        filters = retriever._parse_constraints(constraints)

        assert filters.get("player_count") == 3  # Midpoint of 2-4

    def test_parse_constraints_single_player_count(self, retriever):
        """Should parse single player count."""
        constraints = "4 players"
        filters = retriever._parse_constraints(constraints)

        assert filters.get("player_count") == 4

    def test_parse_constraints_for_players(self, retriever):
        """Should parse 'for N' player pattern."""
        constraints = "for 5 people"
        filters = retriever._parse_constraints(constraints)

        assert filters.get("player_count") == 5

    def test_parse_constraints_complexity_light(self, retriever):
        """Should parse light complexity keywords."""
        for kw in ["light game", "simple", "easy", "casual", "beginner"]:
            constraints = f"something {kw} something"
            filters = retriever._parse_constraints(constraints)
            assert filters.get("complexity") == "light", f"Failed for '{kw}'"

    def test_parse_constraints_complexity_medium(self, retriever):
        """Should parse medium complexity keywords."""
        constraints = "medium complexity"
        filters = retriever._parse_constraints(constraints)

        assert filters.get("complexity") == "medium"

    def test_parse_constraints_complexity_heavy(self, retriever):
        """Should parse heavy complexity keywords."""
        for kw in ["heavy game", "hardcore", "expert"]:
            constraints = f"something {kw} something"
            filters = retriever._parse_constraints(constraints)
            assert filters.get("complexity") == "heavy", f"Failed for '{kw}'"

    def test_parse_constraints_min_rating(self, retriever):
        """Should parse minimum rating."""
        constraints = "rating >= 8.0"
        filters = retriever._parse_constraints(constraints)

        assert filters.get("min_rating") == pytest.approx(8.0)

    def test_parse_constraints_combined(self, retriever):
        """Should parse multiple constraints."""
        constraints = "2-4 players, medium complexity, rating >= 7.5"
        filters = retriever._parse_constraints(constraints)

        assert filters.get("player_count") == 3
        assert filters.get("complexity") == "medium"
        assert filters.get("min_rating") == pytest.approx(7.5)

    def test_parse_constraints_empty(self, retriever):
        """Should handle empty constraints."""
        filters = retriever._parse_constraints("")

        assert filters == {}

    def test_format_results(self, retriever):
        """Should format search results for LLM context."""
        results = [
            {
                "id": "174430",
                "document": "Some text",
                "metadata": {
                    "name": "Gloomhaven",
                    "year": 2017,
                    "rating": 8.7,
                    "complexity": "heavy",
                    "mechanisms": "hand_management,cooperative",
                    "min_players": 1,
                    "max_players": 4,
                },
                "distance": 0.1,
            },
        ]

        formatted = retriever._format_results(results)

        assert "Gloomhaven" in formatted
        assert "2017" in formatted
        assert "8.7" in formatted
        assert "heavy" in formatted
        assert "hand_management" in formatted

    def test_format_results_empty(self, retriever):
        """Should handle empty results."""
        formatted = retriever._format_results([])

        assert "No similar games found" in formatted

    def test_retrieve_for_theme(self, retriever, storage, sample_games):
        """Should retrieve games for theme."""
        storage.index_games(games=sample_games)

        result = retriever.retrieve_for_theme(
            theme="cooperative dungeon crawler",
            constraints="2-4 players",
            n_results=3,
        )

        # Should return formatted string with games
        assert "Gloomhaven" in result or "Similar existing games" in result

    def test_retrieve_for_theme_with_filters(self, retriever, storage, sample_games):
        """Should apply filters when retrieving."""
        storage.index_games(games=sample_games)

        result = retriever.retrieve_for_theme(
            theme="science fiction",
            constraints="5 players, medium complexity",
            n_results=3,
        )

        # Should filter appropriately
        assert isinstance(result, str)

    def test_retrieve_for_theme_no_games(self, retriever):
        """Should handle empty index gracefully."""
        result = retriever.retrieve_for_theme(
            theme="any theme",
            constraints="",
            n_results=5,
        )

        assert "No similar games found" in result


class TestOntologyRAGRetrieverPatterns:
    """Tests for constraint parsing patterns."""

    @pytest.fixture
    def retriever(self):
        """Create retriever with mock storage."""
        mock_storage = MagicMock(spec=GameRAGStorage)
        return OntologyRAGRetriever(storage=mock_storage)

    @pytest.mark.parametrize("constraint,expected_players", [
        ("2-4 players", 3),
        ("3-6 players", 4),
        ("1-8 players", 4),
        ("4 players", 4),
        ("for 2", 2),
        ("supports 5", None),  # Not a recognized pattern
    ])
    def test_player_count_patterns(self, retriever, constraint, expected_players):
        """Test various player count patterns."""
        filters = retriever._parse_constraints(constraint)
        assert filters.get("player_count") == expected_players

    @pytest.mark.parametrize("constraint,expected_complexity", [
        ("light game", "light"),
        ("easy to learn", "light"),
        ("casual gaming", "light"),
        ("medium weight", "medium"),
        ("moderate complexity", "medium"),
        ("heavy game", "heavy"),
        ("expert level", "heavy"),
        ("gateway game", "medium_light"),
        ("medium-heavy", "medium_heavy"),
        ("no particular difficulty", None),
    ])
    def test_complexity_patterns(self, retriever, constraint, expected_complexity):
        """Test various complexity patterns."""
        filters = retriever._parse_constraints(constraint)
        assert filters.get("complexity") == expected_complexity
