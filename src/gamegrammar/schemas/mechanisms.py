"""Mechanism type definitions for game ontology."""

from enum import Enum


class MechanismType(str, Enum):
    """Core game mechanism types organized by category."""

    # Turn Order
    TURN_BASED = "turn_based"
    SIMULTANEOUS = "simultaneous"
    REAL_TIME = "real_time"

    # Action Selection
    WORKER_PLACEMENT = "worker_placement"
    ACTION_POINTS = "action_points"
    CARD_DRIVEN = "card_driven"
    DICE_DRIVEN = "dice_driven"
    ACTION_SELECTION = "action_selection"
    ROLE_SELECTION = "role_selection"

    # Resource / Economy
    RESOURCE_MANAGEMENT = "resource_management"
    TRADING = "trading"
    DRAFTING = "drafting"
    ENGINE_BUILDING = "engine_building"
    MARKET = "market"
    AUCTION = "auction"

    # Conflict / Territory
    AREA_CONTROL = "area_control"
    COMBAT = "combat"
    NEGOTIATION = "negotiation"
    AREA_MOVEMENT = "area_movement"
    ROUTE_BUILDING = "route_building"

    # Cards / Deck
    DECK_BUILDING = "deck_building"
    HAND_MANAGEMENT = "hand_management"
    SET_COLLECTION = "set_collection"
    TABLEAU_BUILDING = "tableau_building"
    TRICK_TAKING = "trick_taking"

    # Information
    HIDDEN_INFORMATION = "hidden_information"
    DEDUCTION = "deduction"
    BLUFFING = "bluffing"
    MEMORY = "memory"

    # Other
    TILE_PLACEMENT = "tile_placement"
    PATTERN_BUILDING = "pattern_building"
    PUSH_YOUR_LUCK = "push_your_luck"
    COOPERATIVE = "cooperative"
    PROGRAMMED_ACTIONS = "programmed_actions"
    VARIABLE_PLAYER_POWERS = "variable_player_powers"

    @classmethod
    def get_category(cls, mechanism: "MechanismType") -> str:
        """Get the category for a mechanism type."""
        categories = {
            # Turn Order
            cls.TURN_BASED: "Turn Order",
            cls.SIMULTANEOUS: "Turn Order",
            cls.REAL_TIME: "Turn Order",
            # Action Selection
            cls.WORKER_PLACEMENT: "Action Selection",
            cls.ACTION_POINTS: "Action Selection",
            cls.CARD_DRIVEN: "Action Selection",
            cls.DICE_DRIVEN: "Action Selection",
            cls.ACTION_SELECTION: "Action Selection",
            cls.ROLE_SELECTION: "Action Selection",
            # Resource / Economy
            cls.RESOURCE_MANAGEMENT: "Resource / Economy",
            cls.TRADING: "Resource / Economy",
            cls.DRAFTING: "Resource / Economy",
            cls.ENGINE_BUILDING: "Resource / Economy",
            cls.MARKET: "Resource / Economy",
            cls.AUCTION: "Resource / Economy",
            # Conflict / Territory
            cls.AREA_CONTROL: "Conflict / Territory",
            cls.COMBAT: "Conflict / Territory",
            cls.NEGOTIATION: "Conflict / Territory",
            cls.AREA_MOVEMENT: "Conflict / Territory",
            cls.ROUTE_BUILDING: "Conflict / Territory",
            # Cards / Deck
            cls.DECK_BUILDING: "Cards / Deck",
            cls.HAND_MANAGEMENT: "Cards / Deck",
            cls.SET_COLLECTION: "Cards / Deck",
            cls.TABLEAU_BUILDING: "Cards / Deck",
            cls.TRICK_TAKING: "Cards / Deck",
            # Information
            cls.HIDDEN_INFORMATION: "Information",
            cls.DEDUCTION: "Information",
            cls.BLUFFING: "Information",
            cls.MEMORY: "Information",
            # Other
            cls.TILE_PLACEMENT: "Other",
            cls.PATTERN_BUILDING: "Other",
            cls.PUSH_YOUR_LUCK: "Other",
            cls.COOPERATIVE: "Other",
            cls.PROGRAMMED_ACTIONS: "Other",
            cls.VARIABLE_PLAYER_POWERS: "Other",
        }
        return categories.get(mechanism, "Unknown")

    @classmethod
    def by_category(cls) -> dict[str, list["MechanismType"]]:
        """Get all mechanisms organized by category."""
        result: dict[str, list[MechanismType]] = {}
        for mechanism in cls:
            category = cls.get_category(mechanism)
            if category not in result:
                result[category] = []
            result[category].append(mechanism)
        return result

    @property
    def description(self) -> str:
        """Get a human-readable description of the mechanism."""
        descriptions = {
            # Turn Order
            self.TURN_BASED: "Players take turns in sequence",
            self.SIMULTANEOUS: "All players act at the same time",
            self.REAL_TIME: "Actions happen continuously without turns",
            # Action Selection
            self.WORKER_PLACEMENT: "Place workers to claim actions",
            self.ACTION_POINTS: "Spend points to perform actions",
            self.CARD_DRIVEN: "Cards determine available actions",
            self.DICE_DRIVEN: "Dice determine available actions",
            self.ACTION_SELECTION: "Choose from available actions each turn",
            self.ROLE_SELECTION: "Select roles that grant special abilities",
            # Resource / Economy
            self.RESOURCE_MANAGEMENT: "Gather, convert, and spend resources",
            self.TRADING: "Exchange resources with other players",
            self.DRAFTING: "Select items from a shared pool",
            self.ENGINE_BUILDING: "Create combos that generate increasing returns",
            self.MARKET: "Buy/sell from a fluctuating market",
            self.AUCTION: "Bid against other players for items",
            # Conflict / Territory
            self.AREA_CONTROL: "Compete for dominance of regions",
            self.COMBAT: "Direct conflict between players",
            self.NEGOTIATION: "Make deals and agreements with players",
            self.AREA_MOVEMENT: "Move units between connected areas",
            self.ROUTE_BUILDING: "Create paths between locations",
            # Cards / Deck
            self.DECK_BUILDING: "Construct your deck during play",
            self.HAND_MANAGEMENT: "Optimize card usage and timing",
            self.SET_COLLECTION: "Gather matching groups of items",
            self.TABLEAU_BUILDING: "Build a personal display of cards",
            self.TRICK_TAKING: "Win rounds by playing highest card",
            # Information
            self.HIDDEN_INFORMATION: "Some information hidden from players",
            self.DEDUCTION: "Logic to discover hidden information",
            self.BLUFFING: "Deceive opponents about your state",
            self.MEMORY: "Remember previously revealed information",
            # Other
            self.TILE_PLACEMENT: "Place tiles to build a shared board",
            self.PATTERN_BUILDING: "Create specific arrangements",
            self.PUSH_YOUR_LUCK: "Risk current gains for more",
            self.COOPERATIVE: "Players work together against the game",
            self.PROGRAMMED_ACTIONS: "Plan multiple actions in advance",
            self.VARIABLE_PLAYER_POWERS: "Each player has unique abilities",
        }
        return descriptions.get(self, "No description available")
