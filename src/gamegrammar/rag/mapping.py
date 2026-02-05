"""BGG mechanism to GameGrammar MechanismType mapping.

BoardGameGeek uses ~192 distinct mechanism names. GameGrammar has 32 MechanismTypes.
This module provides mapping between the two systems.
"""

from typing import Optional

from gamegrammar.schemas.mechanisms import MechanismType


class BGGMechanismMapping:
    """Maps BoardGameGeek mechanism names to GameGrammar MechanismTypes.

    BGG has ~192 mechanisms while GameGrammar has 32. Not all BGG mechanisms
    map directly - some are too specific or represent categories we don't have.
    """

    # Primary mappings: BGG mechanism name -> GameGrammar MechanismType
    # This covers ~100 of the most common/important BGG mechanisms
    BGG_TO_GAMEGRAMMAR: dict[str, MechanismType] = {
        # Turn Order mappings
        "Turn Order: Claim Action": MechanismType.TURN_BASED,
        "Turn Order: Progressive": MechanismType.TURN_BASED,
        "Turn Order: Random": MechanismType.TURN_BASED,
        "Turn Order: Pass Order": MechanismType.TURN_BASED,
        "Turn Order: Stat-Based": MechanismType.TURN_BASED,
        "Turn Order: Role Order": MechanismType.TURN_BASED,
        "Turn Order: Auction": MechanismType.TURN_BASED,
        "Simultaneous Action Selection": MechanismType.SIMULTANEOUS,
        "Real-Time": MechanismType.REAL_TIME,
        "Speed Matching": MechanismType.REAL_TIME,
        # Worker Placement variants
        "Worker Placement": MechanismType.WORKER_PLACEMENT,
        "Worker Placement with Dice Workers": MechanismType.WORKER_PLACEMENT,
        "Worker Placement, Different Worker Types": MechanismType.WORKER_PLACEMENT,
        # Action Points / Selection
        "Action Points": MechanismType.ACTION_POINTS,
        "Action Queue": MechanismType.ACTION_POINTS,
        "Action Retrieval": MechanismType.ACTION_POINTS,
        "Action Timer": MechanismType.ACTION_POINTS,
        "Once-Per-Game Abilities": MechanismType.ACTION_SELECTION,
        "Action/Event": MechanismType.ACTION_SELECTION,
        "Multi-Use Cards": MechanismType.ACTION_SELECTION,
        "Follow": MechanismType.ACTION_SELECTION,
        "Impulse Movement": MechanismType.ACTION_SELECTION,
        # Card-driven
        "Card Play Conflict Resolution": MechanismType.CARD_DRIVEN,
        "Command Cards": MechanismType.CARD_DRIVEN,
        "Events": MechanismType.CARD_DRIVEN,
        # Dice-driven
        "Dice Rolling": MechanismType.DICE_DRIVEN,
        "Die Icon Resolution": MechanismType.DICE_DRIVEN,
        "Re-rolling and Locking": MechanismType.DICE_DRIVEN,
        "Worker Placement with Dice Workers": MechanismType.DICE_DRIVEN,
        # Role Selection
        "Role Playing": MechanismType.ROLE_SELECTION,
        "Variable Phase Order": MechanismType.ROLE_SELECTION,
        # Resource Management
        "Enclosure": MechanismType.RESOURCE_MANAGEMENT,
        "Income": MechanismType.RESOURCE_MANAGEMENT,
        "Investment": MechanismType.RESOURCE_MANAGEMENT,
        "Loans": MechanismType.RESOURCE_MANAGEMENT,
        "Resource to Move": MechanismType.RESOURCE_MANAGEMENT,
        "Automatic Resource Growth": MechanismType.RESOURCE_MANAGEMENT,
        "Ratio / Combat Results Table": MechanismType.RESOURCE_MANAGEMENT,
        "Bribery": MechanismType.RESOURCE_MANAGEMENT,
        "Delayed Purchase": MechanismType.RESOURCE_MANAGEMENT,
        # Trading
        "Trading": MechanismType.TRADING,
        "Negotiation": MechanismType.NEGOTIATION,
        # Drafting variants
        "Card Drafting": MechanismType.DRAFTING,
        "Closed Drafting": MechanismType.DRAFTING,
        "Open Drafting": MechanismType.DRAFTING,
        "Action Drafting": MechanismType.DRAFTING,
        # Engine Building
        "Tech Trees / Tech Tracks": MechanismType.ENGINE_BUILDING,
        "Rondel": MechanismType.ENGINE_BUILDING,
        "Chaining": MechanismType.ENGINE_BUILDING,
        "Increase Value of Unchosen Resources": MechanismType.ENGINE_BUILDING,
        "Contracts": MechanismType.ENGINE_BUILDING,
        # Market / Economy
        "Market": MechanismType.MARKET,
        "Stock Holding": MechanismType.MARKET,
        "Commodity Speculation": MechanismType.MARKET,
        # Auction variants
        "Auction/Bidding": MechanismType.AUCTION,
        "Auction: Dexterity": MechanismType.AUCTION,
        "Auction: Dutch": MechanismType.AUCTION,
        "Auction: Dutch Priority": MechanismType.AUCTION,
        "Auction: English": MechanismType.AUCTION,
        "Auction: Fixed Placement": MechanismType.AUCTION,
        "Auction: Once Around": MechanismType.AUCTION,
        "Auction: Sealed Bid": MechanismType.AUCTION,
        "Auction: Turn Order Until Pass": MechanismType.AUCTION,
        "Bidding": MechanismType.AUCTION,
        # Area Control / Conflict
        "Area Majority / Influence": MechanismType.AREA_CONTROL,
        "Area-Impulse": MechanismType.AREA_CONTROL,
        "Zone of Control": MechanismType.AREA_CONTROL,
        "King of the Hill": MechanismType.AREA_CONTROL,
        # Combat
        "Advantage Token": MechanismType.COMBAT,
        "Chit-Pull System": MechanismType.COMBAT,
        "Critical Hits and Failures": MechanismType.COMBAT,
        "Deck Construction": MechanismType.COMBAT,
        "Dice Battle": MechanismType.COMBAT,
        "Line of Sight": MechanismType.COMBAT,
        "Rock-Paper-Scissors": MechanismType.COMBAT,
        "Simulation": MechanismType.COMBAT,
        "Stacking Limit": MechanismType.COMBAT,
        "Stat Check Resolution": MechanismType.COMBAT,
        "Tug of War": MechanismType.COMBAT,
        "Bias": MechanismType.COMBAT,
        # Movement
        "Area Movement": MechanismType.AREA_MOVEMENT,
        "Grid Movement": MechanismType.AREA_MOVEMENT,
        "Hexagon Grid": MechanismType.AREA_MOVEMENT,
        "Square Grid": MechanismType.AREA_MOVEMENT,
        "Movement Points": MechanismType.AREA_MOVEMENT,
        "Movement Template": MechanismType.AREA_MOVEMENT,
        "Mancala": MechanismType.AREA_MOVEMENT,
        "Map Addition": MechanismType.AREA_MOVEMENT,
        "Map Deformation": MechanismType.AREA_MOVEMENT,
        "Map Reduction": MechanismType.AREA_MOVEMENT,
        "Pieces as Map": MechanismType.AREA_MOVEMENT,
        "Point to Point Movement": MechanismType.AREA_MOVEMENT,
        "Relative Movement": MechanismType.AREA_MOVEMENT,
        # Route Building
        "Network and Route Building": MechanismType.ROUTE_BUILDING,
        "Pick-up and Deliver": MechanismType.ROUTE_BUILDING,
        "Race": MechanismType.ROUTE_BUILDING,
        "Track Movement": MechanismType.ROUTE_BUILDING,
        "Cube Tower": MechanismType.ROUTE_BUILDING,
        "Layering": MechanismType.ROUTE_BUILDING,
        # Deck Building
        "Deck, Bag, and Pool Building": MechanismType.DECK_BUILDING,
        "Deck Construction": MechanismType.DECK_BUILDING,
        # Hand Management
        "Hand Management": MechanismType.HAND_MANAGEMENT,
        "Highest-Lowest Scoring": MechanismType.HAND_MANAGEMENT,
        "Kill Steal": MechanismType.HAND_MANAGEMENT,
        # Set Collection
        "Set Collection": MechanismType.SET_COLLECTION,
        "Connections": MechanismType.SET_COLLECTION,
        "Pattern Recognition": MechanismType.SET_COLLECTION,
        # Tableau Building
        "Tableau Building": MechanismType.TABLEAU_BUILDING,
        "Tags": MechanismType.TABLEAU_BUILDING,
        "Matching": MechanismType.TABLEAU_BUILDING,
        # Trick-taking
        "Trick-taking": MechanismType.TRICK_TAKING,
        "Ladder Climbing": MechanismType.TRICK_TAKING,
        "Lose a Turn": MechanismType.TRICK_TAKING,
        # Hidden Information
        "Hidden Roles": MechanismType.HIDDEN_INFORMATION,
        "Hidden Victory Points": MechanismType.HIDDEN_INFORMATION,
        "Hidden Movement": MechanismType.HIDDEN_INFORMATION,
        "Secret Unit Deployment": MechanismType.HIDDEN_INFORMATION,
        "Traitor Game": MechanismType.HIDDEN_INFORMATION,
        "Roles with Asymmetric Information": MechanismType.HIDDEN_INFORMATION,
        "Scenario / Mission / Campaign Game": MechanismType.HIDDEN_INFORMATION,
        # Deduction
        "Deduction": MechanismType.DEDUCTION,
        "I Cut, You Choose": MechanismType.DEDUCTION,
        "Induction": MechanismType.DEDUCTION,
        "Narrative Choice / Paragraph": MechanismType.DEDUCTION,
        # Bluffing
        "Bluffing": MechanismType.BLUFFING,
        "Betting and Bluffing": MechanismType.BLUFFING,
        "Player Judge": MechanismType.BLUFFING,
        # Memory
        "Memory": MechanismType.MEMORY,
        # Tile Placement
        "Tile Placement": MechanismType.TILE_PLACEMENT,
        "Modular Board": MechanismType.TILE_PLACEMENT,
        # Pattern Building
        "Pattern Building": MechanismType.PATTERN_BUILDING,
        # Push Your Luck
        "Push Your Luck": MechanismType.PUSH_YOUR_LUCK,
        "Press Your Luck": MechanismType.PUSH_YOUR_LUCK,
        # Cooperative
        "Cooperative Game": MechanismType.COOPERATIVE,
        "Solo / Solitaire Game": MechanismType.COOPERATIVE,
        "Team-Based Game": MechanismType.COOPERATIVE,
        "Passed Action Token": MechanismType.COOPERATIVE,
        # Programmed Actions
        "Programmed Movement": MechanismType.PROGRAMMED_ACTIONS,
        "Predictive Bid": MechanismType.PROGRAMMED_ACTIONS,
        "Crayon Rail System": MechanismType.PROGRAMMED_ACTIONS,
        # Variable Player Powers
        "Variable Player Powers": MechanismType.VARIABLE_PLAYER_POWERS,
        "Variable Set-up": MechanismType.VARIABLE_PLAYER_POWERS,
        "Legacy Game": MechanismType.VARIABLE_PLAYER_POWERS,
        "Campaign / Battle Card Driven": MechanismType.VARIABLE_PLAYER_POWERS,
        "Ownership": MechanismType.VARIABLE_PLAYER_POWERS,
        "Alliances": MechanismType.VARIABLE_PLAYER_POWERS,
        "Asymmetric Powers": MechanismType.VARIABLE_PLAYER_POWERS,
        "Score-and-Reset Game": MechanismType.VARIABLE_PLAYER_POWERS,
        "Finale Ending": MechanismType.VARIABLE_PLAYER_POWERS,
        "Physical Removal": MechanismType.VARIABLE_PLAYER_POWERS,
        # Additional common BGG mechanisms
        "End Game Bonuses": MechanismType.SET_COLLECTION,
        "Grid Coverage": MechanismType.TILE_PLACEMENT,
        "Player Elimination": MechanismType.COMBAT,
        "Semi-Cooperative Game": MechanismType.COOPERATIVE,
        "Storytelling": MechanismType.HIDDEN_INFORMATION,
        "Time Track": MechanismType.ACTION_POINTS,
        "Voting": MechanismType.NEGOTIATION,
        "Communication Limits": MechanismType.HIDDEN_INFORMATION,
        "Take That": MechanismType.COMBAT,
        "Catch the Leader": MechanismType.AREA_CONTROL,
        "Different Dice Movement": MechanismType.DICE_DRIVEN,
        "Dice Throw": MechanismType.DICE_DRIVEN,
        "Slide/Push": MechanismType.AREA_MOVEMENT,
        "Deck Deconstruction": MechanismType.DECK_BUILDING,
        "Force Commitment": MechanismType.PROGRAMMED_ACTIONS,
        "Victory Points as a Resource": MechanismType.RESOURCE_MANAGEMENT,
        "Multiple-Lot Auction": MechanismType.AUCTION,
        "Selection Order Bid": MechanismType.AUCTION,
        "Singing": MechanismType.COOPERATIVE,
        "Spelling": MechanismType.PATTERN_BUILDING,
    }

    # BGG mechanisms that don't map to any GameGrammar MechanismType
    # These are too specific, dexterity-based, or represent categories we don't cover
    UNMAPPED_BGG_MECHANISMS: set[str] = {
        "Acting",
        "Bingo",
        "Elapsed Real Time Ending",
        "Flicking",
        "Hot Potato",
        "Measurement Movement",
        "Minimap Resolution",
        "Paper-and-Pencil",
        "Roll / Spin and Move",
        "Single Loser Game",
        "Three Dimensional Movement",
        "Targeted Clues",
        "Sudden Death Ending",
        "Static Capture",
        "Stalemate Removal",
        "Relative Movement",
        "Random Production",
        "Questions and Answers",
        "Progressive",
        "Player Judge",
        "Physical Removal",
        "Pattern Movement",
        "Move Through Deck",
        "Melding and Splaying",
        "Line Drawing",
        "Interrupts",
        "Impulse",
        "Fixed List",
        "Finale Ending",
        "Drafting: Neighbor",
        "Critical Hits and Failures",
        "Constrained Bidding",
        "Closed Economy",
        "Chop",
        "Beat'em Up",
        "Auction: Priority",
        "Auction Compensation",
        "Attrition",
        "Anti-Clockwise Order",
        "Campaign",
        "Category",
        "Betting",
        "Closed",
        "Endowment",
        "Fair Division",
        "Freeform",
        "Gate",
        "Guided",
        "Learning the Game",
        "Learning",
        "Limited",
        "Lose a Turn",
        "Meet in the Middle",
        "Multiplayer Elimination",
        "Order Counters",
        "Ownership",
        "Physics Engine",
        "Poolbuilding",
        "Random Draw",
        "Real Time",
        "Safety",
        "Skip",
        "Skirmish",
        "Sprint",
        "Starting",
        "Token",
        "Tournament",
        "Tutorial",
        "Versus",
        "Wargame Chaos",
    }

    @classmethod
    def map_bgg_to_gamegrammar(
        cls, bgg_mechanism: str
    ) -> Optional[MechanismType]:
        """Map a single BGG mechanism name to a GameGrammar MechanismType.

        Args:
            bgg_mechanism: The BoardGameGeek mechanism name (e.g., "Worker Placement")

        Returns:
            The corresponding GameGrammar MechanismType, or None if no mapping exists
        """
        return cls.BGG_TO_GAMEGRAMMAR.get(bgg_mechanism)

    @classmethod
    def map_bgg_mechanisms(
        cls, bgg_mechanisms: list[str]
    ) -> list[MechanismType]:
        """Map a list of BGG mechanism names to GameGrammar MechanismTypes.

        Filters out unmapped mechanisms and removes duplicates while preserving order.

        Args:
            bgg_mechanisms: List of BGG mechanism names

        Returns:
            List of unique GameGrammar MechanismTypes (in order of first appearance)
        """
        seen: set[MechanismType] = set()
        result: list[MechanismType] = []

        for bgg_mech in bgg_mechanisms:
            gg_mech = cls.map_bgg_to_gamegrammar(bgg_mech)
            if gg_mech is not None and gg_mech not in seen:
                seen.add(gg_mech)
                result.append(gg_mech)

        return result

    @classmethod
    def get_unmapped_from_list(cls, bgg_mechanisms: list[str]) -> list[str]:
        """Get BGG mechanisms from a list that don't have GameGrammar mappings.

        Useful for identifying gaps in the mapping or mechanisms to track separately.

        Args:
            bgg_mechanisms: List of BGG mechanism names

        Returns:
            List of mechanism names that don't map to GameGrammar types
        """
        return [m for m in bgg_mechanisms if m not in cls.BGG_TO_GAMEGRAMMAR]

    @classmethod
    def mapping_coverage(cls) -> dict[str, int]:
        """Get statistics about the mechanism mapping.

        Returns:
            Dict with 'mapped' count, 'unmapped' count, and 'total' count
        """
        return {
            "mapped": len(cls.BGG_TO_GAMEGRAMMAR),
            "unmapped": len(cls.UNMAPPED_BGG_MECHANISMS),
            "total": len(cls.BGG_TO_GAMEGRAMMAR) + len(cls.UNMAPPED_BGG_MECHANISMS),
            "gamegrammar_types": len(MechanismType),
        }
