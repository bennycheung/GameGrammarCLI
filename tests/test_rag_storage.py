"""Tests for ChromaDB vector storage."""

import tempfile
from pathlib import Path

import pytest

from gamegrammar.rag.collector import BGGGame
from gamegrammar.rag.storage import GameRAGStorage, weight_to_complexity
from gamegrammar.schemas.mechanisms import MechanismType


class TestWeightToComplexity:
    """Tests for weight_to_complexity function."""

    def test_light_complexity(self):
        """Low weight should be light."""
        assert weight_to_complexity(1.0) == "light"
        assert weight_to_complexity(1.4) == "light"

    def test_medium_light_complexity(self):
        """Mid-low weight should be medium_light."""
        assert weight_to_complexity(1.5) == "medium_light"
        assert weight_to_complexity(2.0) == "medium_light"
        assert weight_to_complexity(2.24) == "medium_light"

    def test_medium_complexity(self):
        """Middle weight should be medium."""
        assert weight_to_complexity(2.25) == "medium"
        assert weight_to_complexity(2.5) == "medium"
        assert weight_to_complexity(2.99) == "medium"

    def test_medium_heavy_complexity(self):
        """Mid-high weight should be medium_heavy."""
        assert weight_to_complexity(3.0) == "medium_heavy"
        assert weight_to_complexity(3.5) == "medium_heavy"
        assert weight_to_complexity(3.74) == "medium_heavy"

    def test_heavy_complexity(self):
        """High weight should be heavy."""
        assert weight_to_complexity(3.75) == "heavy"
        assert weight_to_complexity(4.0) == "heavy"
        assert weight_to_complexity(5.0) == "heavy"


class TestGameRAGStorage:
    """Tests for GameRAGStorage class."""

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
                description="A cooperative dungeon crawler with tactical combat.",
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
                description="Transform Mars into a habitable planet.",
                mechanics=["Card Drafting", "Tile Placement", "Hand Management"],
                categories=["Science Fiction", "Economic"],
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
                description="Trade and build settlements.",
                mechanics=["Dice Rolling", "Trading"],
                categories=["Negotiation"],
            ),
        ]

    def test_init_creates_collection(self, storage):
        """Should create collection on init."""
        stats = storage.get_collection_stats()
        assert stats["count"] == 0
        assert stats["collection_name"] == "gamegrammar_games"

    def test_create_document(self, storage, sample_games):
        """Should create document from game."""
        game = sample_games[0]  # Gloomhaven
        doc = storage._create_document(game)

        assert "Gloomhaven" in doc
        assert "2017" in doc
        assert "1-4" in doc
        assert "heavy" in doc  # weight 3.8 = heavy
        assert "cooperative" in doc.lower()

    def test_create_metadata(self, storage, sample_games):
        """Should create metadata from game."""
        game = sample_games[0]  # Gloomhaven
        meta = storage._create_metadata(game)

        assert meta["name"] == "Gloomhaven"
        assert meta["year"] == 2017
        assert meta["min_players"] == 1
        assert meta["max_players"] == 4
        assert meta["rating"] == pytest.approx(8.7)
        assert meta["weight"] == pytest.approx(3.8)
        assert meta["rank"] == 1
        assert meta["complexity"] == "heavy"
        # Mechanisms should be GameGrammar values
        assert "cooperative" in meta["mechanisms"]

    def test_index_games(self, storage, sample_games):
        """Should index games into ChromaDB."""
        indexed = storage.index_games(games=sample_games)

        assert indexed == 3
        stats = storage.get_collection_stats()
        assert stats["count"] == 3

    def test_index_games_skip_duplicates(self, storage, sample_games):
        """Should skip already indexed games."""
        # Index once
        storage.index_games(games=sample_games)

        # Index again
        indexed = storage.index_games(games=sample_games)

        assert indexed == 0  # No new games
        stats = storage.get_collection_stats()
        assert stats["count"] == 3

    def test_search_similar_games(self, storage, sample_games):
        """Should find similar games."""
        storage.index_games(games=sample_games)

        results = storage.search_similar_games(
            query="cooperative dungeon crawler",
            n_results=3,
        )

        assert len(results) > 0
        # Gloomhaven should be most similar
        assert results[0]["metadata"]["name"] == "Gloomhaven"

    def test_search_with_complexity_filter(self, storage, sample_games):
        """Should filter by complexity."""
        storage.index_games(games=sample_games)

        # Search for medium complexity games
        results = storage.search_similar_games(
            query="trading game",
            n_results=5,
            complexity_filter="medium",
        )

        for result in results:
            assert result["metadata"]["complexity"] == "medium"

    def test_search_with_player_count_filter(self, storage, sample_games):
        """Should filter by player count."""
        storage.index_games(games=sample_games)

        # Search for 5-player games
        results = storage.search_similar_games(
            query="any game",
            n_results=5,
            player_count=5,
        )

        for result in results:
            assert result["metadata"]["min_players"] <= 5
            assert result["metadata"]["max_players"] >= 5

    def test_search_with_min_rating_filter(self, storage, sample_games):
        """Should filter by minimum rating."""
        storage.index_games(games=sample_games)

        results = storage.search_similar_games(
            query="any game",
            n_results=5,
            min_rating=8.0,
        )

        for result in results:
            assert result["metadata"]["rating"] >= 8.0

    def test_search_empty_collection(self, storage):
        """Should return empty list for empty collection."""
        results = storage.search_similar_games(
            query="any query",
            n_results=5,
        )

        assert results == []

    def test_clear_collection(self, storage, sample_games):
        """Should clear all indexed games."""
        storage.index_games(games=sample_games)
        assert storage.get_collection_stats()["count"] == 3

        storage.clear_collection()

        assert storage.get_collection_stats()["count"] == 0

    def test_get_collection_stats(self, storage, sample_games):
        """Should return collection statistics."""
        stats = storage.get_collection_stats()

        assert "count" in stats
        assert "collection_name" in stats
        assert "persist_directory" in stats
        assert stats["collection_name"] == "gamegrammar_games"
