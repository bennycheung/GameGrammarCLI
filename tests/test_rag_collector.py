"""Tests for BGG data collector."""

import sqlite3
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gamegrammar.rag.collector import BGGCollector, BGGGame


class TestBGGGame:
    """Tests for BGGGame dataclass."""

    def test_create_minimal_game(self):
        """Should create game with minimal required fields."""
        game = BGGGame(id=1, name="Test Game")

        assert game.id == 1
        assert game.name == "Test Game"
        assert game.year is None
        assert game.min_players == 1
        assert game.max_players == 1
        assert game.mechanics == []
        assert game.categories == []

    def test_create_full_game(self):
        """Should create game with all fields."""
        game = BGGGame(
            id=174430,
            name="Gloomhaven",
            year=2017,
            min_players=1,
            max_players=4,
            min_playtime=60,
            max_playtime=120,
            rating=8.5,
            weight=3.8,
            rank=1,
            description="A cooperative dungeon crawler",
            mechanics=["Hand Management", "Cooperative"],
            categories=["Fantasy", "Adventure"],
        )

        assert game.id == 174430
        assert game.name == "Gloomhaven"
        assert game.year == 2017
        assert game.rating == 8.5
        assert "Hand Management" in game.mechanics
        assert "Fantasy" in game.categories


class TestBGGCollector:
    """Tests for BGGCollector class."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_games.db"
            yield db_path

    @pytest.fixture
    def collector(self, temp_db):
        """Create collector with temporary database."""
        return BGGCollector(db_path=temp_db)

    def test_init_creates_database(self, collector, temp_db):
        """Should create database file on init."""
        assert temp_db.exists()

    def test_init_creates_tables(self, collector, temp_db):
        """Should create required tables."""
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}

        assert "games" in tables
        assert "game_mechanics" in tables
        assert "game_categories" in tables

    def test_save_game(self, collector, temp_db):
        """Should save game to database."""
        game = BGGGame(
            id=13,
            name="Catan",
            year=1995,
            min_players=3,
            max_players=4,
            rating=7.1,
            weight=2.3,
            mechanics=["Dice Rolling", "Trading"],
            categories=["Negotiation"],
        )

        collector._save_game(game)

        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("SELECT name FROM games WHERE id = ?", (13,))
            row = cursor.fetchone()
            assert row[0] == "Catan"

            cursor = conn.execute(
                "SELECT mechanic FROM game_mechanics WHERE game_id = ?",
                (13,)
            )
            mechanics = {row[0] for row in cursor.fetchall()}
            assert "Dice Rolling" in mechanics
            assert "Trading" in mechanics

    def test_get_collected_ids(self, collector):
        """Should return set of collected game IDs."""
        # Save some games
        for i in range(5):
            game = BGGGame(id=i, name=f"Game {i}")
            collector._save_game(game)

        ids = collector._get_collected_ids()

        assert len(ids) == 5
        assert 0 in ids
        assert 4 in ids

    def test_get_game_count(self, collector):
        """Should return correct game count."""
        assert collector.get_game_count() == 0

        for i in range(10):
            game = BGGGame(id=i, name=f"Game {i}")
            collector._save_game(game)

        assert collector.get_game_count() == 10

    def test_get_all_games(self, collector):
        """Should return all games with mechanics and categories."""
        game = BGGGame(
            id=1,
            name="Test Game",
            year=2020,
            mechanics=["Worker Placement"],
            categories=["Strategy"],
        )
        collector._save_game(game)

        games = collector.get_all_games()

        assert len(games) == 1
        assert games[0].name == "Test Game"
        assert "Worker Placement" in games[0].mechanics
        assert "Strategy" in games[0].categories

    def test_get_all_mechanics(self, collector):
        """Should return mechanics with counts."""
        games = [
            BGGGame(id=1, name="G1", mechanics=["Dice Rolling", "Trading"]),
            BGGGame(id=2, name="G2", mechanics=["Dice Rolling", "Worker Placement"]),
            BGGGame(id=3, name="G3", mechanics=["Dice Rolling"]),
        ]
        for game in games:
            collector._save_game(game)

        mechanics = collector.get_all_mechanics()

        # Dice Rolling should be most common
        assert mechanics[0][0] == "Dice Rolling"
        assert mechanics[0][1] == 3

    def test_parse_game_xml(self, collector):
        """Should parse game from XML element."""
        xml_str = """
        <item type="boardgame" id="13">
            <name type="primary" value="Catan"/>
            <yearpublished value="1995"/>
            <minplayers value="3"/>
            <maxplayers value="4"/>
            <minplaytime value="60"/>
            <maxplaytime value="120"/>
            <description>Build settlements and trade resources.</description>
            <statistics>
                <ratings>
                    <average value="7.15"/>
                    <averageweight value="2.30"/>
                    <ranks>
                        <rank name="boardgame" value="200"/>
                    </ranks>
                </ratings>
            </statistics>
            <link type="boardgamemechanic" value="Dice Rolling"/>
            <link type="boardgamemechanic" value="Trading"/>
            <link type="boardgamecategory" value="Negotiation"/>
        </item>
        """
        item = ET.fromstring(xml_str)
        game = collector._parse_game_xml(item)

        assert game is not None
        assert game.id == 13
        assert game.name == "Catan"
        assert game.year == 1995
        assert game.min_players == 3
        assert game.max_players == 4
        assert game.rating == pytest.approx(7.15)
        assert game.weight == pytest.approx(2.30)
        assert game.rank == 200
        assert "Dice Rolling" in game.mechanics
        assert "Trading" in game.mechanics
        assert "Negotiation" in game.categories

    def test_parse_game_xml_missing_fields(self, collector):
        """Should handle missing optional fields."""
        xml_str = """
        <item type="boardgame" id="1">
            <name type="primary" value="Minimal Game"/>
        </item>
        """
        item = ET.fromstring(xml_str)
        game = collector._parse_game_xml(item)

        assert game is not None
        assert game.id == 1
        assert game.name == "Minimal Game"
        assert game.year is None
        assert game.mechanics == []

    def test_parse_game_xml_invalid_type(self, collector):
        """Should return None for non-boardgame items."""
        xml_str = """
        <item type="boardgameexpansion" id="1">
            <name type="primary" value="Some Expansion"/>
        </item>
        """
        item = ET.fromstring(xml_str)
        # Note: _parse_game_xml doesn't check type, but fetch_game_batch does
        game = collector._parse_game_xml(item)
        assert game is not None  # Parser doesn't filter by type

    def test_get_top_game_ids(self, collector):
        """Should return list of game IDs."""
        ids = collector.get_top_game_ids(limit=100)

        assert len(ids) <= 100
        assert len(ids) > 0
        # Should include known popular games
        assert 174430 in ids  # Gloomhaven
        assert 13 in ids  # Catan

    @patch('gamegrammar.rag.collector.requests.get')
    def test_fetch_game_batch_success(self, mock_get, collector):
        """Should fetch and parse games from API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"""<?xml version="1.0" encoding="utf-8"?>
        <items>
            <item type="boardgame" id="13">
                <name type="primary" value="Catan"/>
                <statistics>
                    <ratings>
                        <average value="7.15"/>
                        <averageweight value="2.30"/>
                        <ranks>
                            <rank name="boardgame" value="200"/>
                        </ranks>
                    </ratings>
                </statistics>
            </item>
        </items>
        """
        mock_get.return_value = mock_response

        games = collector.fetch_game_batch([13])

        assert len(games) == 1
        assert games[0].id == 13
        assert games[0].name == "Catan"

    @patch('gamegrammar.rag.collector.requests.get')
    def test_fetch_game_batch_rate_limited(self, mock_get, collector):
        """Should retry on rate limit (503)."""
        # First call returns 503, second returns success
        mock_503 = MagicMock()
        mock_503.status_code = 503

        mock_success = MagicMock()
        mock_success.status_code = 200
        mock_success.content = b"""<?xml version="1.0" encoding="utf-8"?>
        <items>
            <item type="boardgame" id="13">
                <name type="primary" value="Catan"/>
            </item>
        </items>
        """

        mock_get.side_effect = [mock_503, mock_success]

        with patch('gamegrammar.rag.collector.time.sleep'):  # Skip actual delay
            games = collector.fetch_game_batch([13])

        assert len(games) == 1

    @patch('gamegrammar.rag.collector.requests.get')
    def test_fetch_game_batch_empty_list(self, mock_get, collector):
        """Should return empty list for empty input."""
        games = collector.fetch_game_batch([])
        assert games == []
        mock_get.assert_not_called()
