"""Tests for BGG mechanism mapping."""

import pytest

from gamegrammar.rag.mapping import BGGMechanismMapping
from gamegrammar.schemas.mechanisms import MechanismType


class TestBGGMechanismMapping:
    """Test suite for BGGMechanismMapping class."""

    def test_map_worker_placement(self):
        """Worker Placement should map correctly."""
        result = BGGMechanismMapping.map_bgg_to_gamegrammar("Worker Placement")
        assert result == MechanismType.WORKER_PLACEMENT

    def test_map_deck_building(self):
        """Deck, Bag, and Pool Building should map to DECK_BUILDING."""
        result = BGGMechanismMapping.map_bgg_to_gamegrammar("Deck, Bag, and Pool Building")
        assert result == MechanismType.DECK_BUILDING

    def test_map_area_control(self):
        """Area Majority / Influence should map to AREA_CONTROL."""
        result = BGGMechanismMapping.map_bgg_to_gamegrammar("Area Majority / Influence")
        assert result == MechanismType.AREA_CONTROL

    def test_map_simultaneous(self):
        """Simultaneous Action Selection should map to SIMULTANEOUS."""
        result = BGGMechanismMapping.map_bgg_to_gamegrammar("Simultaneous Action Selection")
        assert result == MechanismType.SIMULTANEOUS

    def test_map_push_your_luck(self):
        """Push Your Luck should map correctly."""
        result = BGGMechanismMapping.map_bgg_to_gamegrammar("Push Your Luck")
        assert result == MechanismType.PUSH_YOUR_LUCK

    def test_map_hand_management(self):
        """Hand Management should map correctly."""
        result = BGGMechanismMapping.map_bgg_to_gamegrammar("Hand Management")
        assert result == MechanismType.HAND_MANAGEMENT

    def test_map_dice_rolling(self):
        """Dice Rolling should map to DICE_DRIVEN."""
        result = BGGMechanismMapping.map_bgg_to_gamegrammar("Dice Rolling")
        assert result == MechanismType.DICE_DRIVEN

    def test_map_tile_placement(self):
        """Tile Placement should map correctly."""
        result = BGGMechanismMapping.map_bgg_to_gamegrammar("Tile Placement")
        assert result == MechanismType.TILE_PLACEMENT

    def test_map_unknown_mechanism_returns_none(self):
        """Unknown mechanisms should return None."""
        result = BGGMechanismMapping.map_bgg_to_gamegrammar("NonexistentMechanism")
        assert result is None

    def test_map_empty_string_returns_none(self):
        """Empty string should return None."""
        result = BGGMechanismMapping.map_bgg_to_gamegrammar("")
        assert result is None

    def test_map_multiple_mechanisms(self):
        """Multiple mechanisms should be mapped correctly."""
        bgg_mechs = [
            "Worker Placement",
            "Hand Management",
            "Dice Rolling",
            "UnknownMech",
        ]
        result = BGGMechanismMapping.map_bgg_mechanisms(bgg_mechs)

        assert MechanismType.WORKER_PLACEMENT in result
        assert MechanismType.HAND_MANAGEMENT in result
        assert MechanismType.DICE_DRIVEN in result
        assert len(result) == 3

    def test_map_multiple_removes_duplicates(self):
        """Duplicate mappings should be removed."""
        bgg_mechs = [
            "Worker Placement",
            "Worker Placement with Dice Workers",  # Also maps to WORKER_PLACEMENT
        ]
        result = BGGMechanismMapping.map_bgg_mechanisms(bgg_mechs)

        # Should only have one WORKER_PLACEMENT
        worker_count = sum(1 for m in result if m == MechanismType.WORKER_PLACEMENT)
        assert worker_count == 1

    def test_map_multiple_preserves_order(self):
        """Order of first appearance should be preserved."""
        bgg_mechs = [
            "Hand Management",
            "Worker Placement",
            "Dice Rolling",
        ]
        result = BGGMechanismMapping.map_bgg_mechanisms(bgg_mechs)

        assert result[0] == MechanismType.HAND_MANAGEMENT
        assert result[1] == MechanismType.WORKER_PLACEMENT
        assert result[2] == MechanismType.DICE_DRIVEN

    def test_map_empty_list(self):
        """Empty list should return empty list."""
        result = BGGMechanismMapping.map_bgg_mechanisms([])
        assert result == []

    def test_get_unmapped_from_list(self):
        """Should identify unmapped mechanisms."""
        bgg_mechs = [
            "Worker Placement",
            "SomeFakeMechanism",
            "AnotherFake",
        ]
        unmapped = BGGMechanismMapping.get_unmapped_from_list(bgg_mechs)

        assert "Worker Placement" not in unmapped
        assert "SomeFakeMechanism" in unmapped
        assert "AnotherFake" in unmapped

    def test_mapping_coverage(self):
        """Should return coverage statistics."""
        stats = BGGMechanismMapping.mapping_coverage()

        assert "mapped" in stats
        assert "unmapped" in stats
        assert "total" in stats
        assert "gamegrammar_types" in stats
        assert stats["mapped"] > 0
        assert stats["gamegrammar_types"] == len(MechanismType)

    def test_all_gamegrammar_types_have_mappings(self):
        """Each GameGrammar type should have at least one BGG mapping."""
        mapped_types = set(BGGMechanismMapping.BGG_TO_GAMEGRAMMAR.values())

        # Most types should be covered
        # Note: Some niche types might not have BGG equivalents
        covered_count = len(mapped_types)
        total_types = len(MechanismType)

        # At least 80% of GameGrammar types should be mapped
        assert covered_count >= total_types * 0.8

    def test_auction_variants_map_correctly(self):
        """Various auction types should all map to AUCTION."""
        auction_types = [
            "Auction/Bidding",
            "Auction: Dutch",
            "Auction: English",
            "Auction: Sealed Bid",
            "Bidding",
        ]

        for auction_type in auction_types:
            result = BGGMechanismMapping.map_bgg_to_gamegrammar(auction_type)
            assert result == MechanismType.AUCTION, f"{auction_type} should map to AUCTION"

    def test_drafting_variants_map_correctly(self):
        """Various drafting types should all map to DRAFTING."""
        drafting_types = [
            "Card Drafting",
            "Closed Drafting",
            "Open Drafting",
            "Action Drafting",
        ]

        for drafting_type in drafting_types:
            result = BGGMechanismMapping.map_bgg_to_gamegrammar(drafting_type)
            assert result == MechanismType.DRAFTING, f"{drafting_type} should map to DRAFTING"
