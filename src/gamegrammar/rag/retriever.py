"""RAG retriever and DSPy integration for game generation.

Provides OntologyRAGRetriever for semantic game retrieval and
RAGSinglePassGenerator for RAG-enhanced game generation.
"""

import re
from pathlib import Path
from typing import Optional

import dspy
from pydantic import Field

from gamegrammar.rag.storage import GameRAGStorage
from gamegrammar.schemas.game import GameOntology


class OntologyRAGRetriever:
    """Retrieves similar games from the vector store for generation context.

    Parses constraints to apply ontology-aligned filters before semantic search.
    """

    # Patterns for parsing constraints
    PLAYER_PATTERNS = [
        r"(\d+)\s*-\s*(\d+)\s*players?",  # "2-4 players"
        r"(\d+)\s*players?",  # "4 players"
        r"for\s*(\d+)",  # "for 4"
    ]

    # Ordered list to check more specific patterns first
    # Each tuple is (complexity_level, keywords_list)
    COMPLEXITY_PATTERNS = [
        ("medium_heavy", ["medium heavy", "medium-heavy"]),
        ("medium_light", ["medium light", "medium-light", "gateway"]),
        ("heavy", ["heavy complexity", "heavy weight", "heavy game", "hardcore", "expert"]),
        ("light", ["light complexity", "light weight", "light game", "simple", "easy", "casual", "beginner"]),
        ("medium", ["medium complexity", "medium weight", "medium game", "moderate"]),
    ]

    def __init__(
        self,
        storage: Optional[GameRAGStorage] = None,
        persist_directory: Optional[Path] = None,
    ):
        """Initialize the retriever.

        Args:
            storage: Existing GameRAGStorage instance
            persist_directory: Directory for ChromaDB (if storage not provided)
        """
        self.storage = storage or GameRAGStorage(persist_directory=persist_directory)

    def _parse_constraints(self, constraints: str) -> dict:
        """Parse constraint string to extract filters.

        Args:
            constraints: Natural language constraints string

        Returns:
            Dict with extracted filter values
        """
        filters = {}
        constraints_lower = constraints.lower()

        # Parse player count
        for pattern in self.PLAYER_PATTERNS:
            match = re.search(pattern, constraints_lower)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    # Range: use midpoint
                    filters["player_count"] = (int(groups[0]) + int(groups[1])) // 2
                else:
                    filters["player_count"] = int(groups[0])
                break

        # Parse complexity (check more specific patterns first)
        for complexity, keywords in self.COMPLEXITY_PATTERNS:
            if any(kw in constraints_lower for kw in keywords):
                filters["complexity"] = complexity
                break

        # Parse minimum rating (if specified)
        rating_match = re.search(r"rating\s*[>>=]+\s*(\d+(?:\.\d+)?)", constraints_lower)
        if rating_match:
            filters["min_rating"] = float(rating_match.group(1))

        return filters

    def _format_results(self, results: list[dict]) -> str:
        """Format search results for LLM context.

        Args:
            results: List of search result dicts

        Returns:
            Formatted string for inclusion in prompt
        """
        if not results:
            return "No similar games found in database."

        lines = ["Similar existing games for inspiration:"]
        lines.append("")

        for i, result in enumerate(results, 1):
            meta = result.get("metadata", {})
            name = meta.get("name", "Unknown")
            year = meta.get("year", "")
            rating = meta.get("rating", 0)
            complexity = meta.get("complexity", "")
            mechanisms = meta.get("mechanisms", "")
            players = f"{meta.get('min_players', 1)}-{meta.get('max_players', 1)}"

            lines.append(f"{i}. {name}" + (f" ({year})" if year else ""))
            lines.append(f"   Rating: {rating:.1f}/10 | Players: {players} | Complexity: {complexity}")
            if mechanisms:
                lines.append(f"   Mechanisms: {mechanisms}")
            lines.append("")

        return "\n".join(lines)

    def retrieve_for_theme(
        self,
        theme: str,
        constraints: str = "",
        n_results: int = 5,
    ) -> str:
        """Retrieve similar games for a theme and constraints.

        Args:
            theme: The thematic concept for the game
            constraints: Design constraints string
            n_results: Number of games to retrieve

        Returns:
            Formatted string of similar games for LLM context
        """
        # Parse constraints for filters
        filters = self._parse_constraints(constraints)

        # Build query from theme and any mechanism hints in constraints
        query = theme

        # Search
        results = self.storage.search_similar_games(
            query=query,
            n_results=n_results,
            complexity_filter=filters.get("complexity"),
            player_count=filters.get("player_count"),
            min_rating=filters.get("min_rating"),
        )

        return self._format_results(results)


class RAGOntologySignature(dspy.Signature):
    """Generate a complete board game design informed by similar existing games.

    You are an expert board game designer. Create a complete, coherent game design
    that integrates theme and mechanics seamlessly. The game should be playable,
    balanced, and fun.

    Use the similar games provided as inspiration for proven design patterns,
    but create something original that doesn't copy any existing game.
    """

    theme: str = dspy.InputField(desc="The thematic concept for the game")
    constraints: str = dspy.InputField(
        desc="Design constraints (player count, complexity, etc.)"
    )
    mechanism_options: str = dspy.InputField(
        desc="Available game mechanisms to choose from"
    )
    similar_games: str = dspy.InputField(
        desc="Similar existing games for design inspiration"
    )

    title: str = dspy.OutputField(desc="Name of the game")
    tagline: str = dspy.OutputField(desc="Short memorable description")
    theme_description: str = dspy.OutputField(desc="Detailed theme and setting")
    game_type: str = dspy.OutputField(
        desc="Game type: strategy, party, family, thematic, abstract, euro"
    )
    complexity: str = dspy.OutputField(
        desc="Complexity: light, medium_light, medium, medium_heavy, heavy"
    )
    goal: str = dspy.OutputField(desc="What players are trying to achieve")
    end_condition: str = dspy.OutputField(desc="How the game ends")
    victory_condition: str = dspy.OutputField(desc="How winners are determined")
    primary_mechanisms: str = dspy.OutputField(
        desc="Comma-separated list of primary mechanisms"
    )
    secondary_mechanisms: str = dspy.OutputField(
        desc="Comma-separated list of secondary mechanisms"
    )
    turn_phases: str = dspy.OutputField(desc="Comma-separated phases within each turn")
    actions_per_turn: str = dspy.OutputField(desc="What players do on their turn")
    uncertainty_sources: str = dspy.OutputField(
        desc="Comma-separated sources of randomness"
    )
    min_players: int = dspy.OutputField(desc="Minimum player count")
    max_players: int = dspy.OutputField(desc="Maximum player count")
    interaction_type: str = dspy.OutputField(
        desc="Interaction: competitive, cooperative, team_based, semi_cooperative"
    )
    board_type: str = dspy.OutputField(
        desc="Board type: none, fixed, modular, player_built, track"
    )
    board_description: str = dspy.OutputField(
        desc="Board description or 'none' if no board"
    )
    cards_json: str = dspy.OutputField(
        desc='JSON array of card decks: [{"name": "...", "count": N, "purpose": "...", "unique": bool}]'
    )
    tokens_json: str = dspy.OutputField(
        desc='JSON array of tokens: [{"name": "...", "count": N, "purpose": "..."}]'
    )
    dice_json: str = dspy.OutputField(
        desc='JSON array of dice: [{"type": "d6", "count": N, "purpose": "..."}] or []'
    )
    other_components: str = dspy.OutputField(
        desc="Comma-separated list of other components"
    )
    setup: str = dspy.OutputField(desc="How to set up the game")
    core_loop: str = dspy.OutputField(desc="The primary gameplay loop")
    strategic_depth: str = dspy.OutputField(desc="Key strategic considerations")
    theme_integration: str = dspy.OutputField(
        desc="How theme connects to mechanics"
    )
    agency_justification: str = dspy.OutputField(
        desc="Why players feel in control"
    )
    play_time_minutes: int = dspy.OutputField(desc="Expected play time in minutes")


class RAGSinglePassGenerator(dspy.Module):
    """Single-pass game generator with RAG enhancement.

    Retrieves similar games from the vector store and uses them as
    context for generation.
    """

    def __init__(
        self,
        retriever: Optional[OntologyRAGRetriever] = None,
        n_results: int = 5,
    ):
        """Initialize the generator.

        Args:
            retriever: OntologyRAGRetriever instance
            n_results: Number of similar games to retrieve
        """
        super().__init__()
        self.retriever = retriever or OntologyRAGRetriever()
        self.n_results = n_results
        self.generator = dspy.ChainOfThought(RAGOntologySignature)

    def _get_mechanism_options(self) -> str:
        """Get formatted mechanism options string."""
        from gamegrammar.schemas.mechanisms import MechanismType

        categories = MechanismType.by_category()
        lines = []
        for category, mechanisms in categories.items():
            mech_strs = [f"{m.value} ({m.description})" for m in mechanisms]
            lines.append(f"{category}: {', '.join(mech_strs)}")
        return "\n".join(lines)

    def _parse_output(self, result) -> GameOntology:
        """Parse DSPy output into GameOntology."""
        import json

        from gamegrammar.schemas.game import (
            BoardType,
            ComponentSet,
            Complexity,
            GameType,
            InteractionType,
            PlayerDynamics,
            TurnStructure,
            UncertaintySource,
        )
        from gamegrammar.schemas.mechanisms import MechanismType

        def parse_list(s: str) -> list[str]:
            if not s or s.lower() in ("none", "n/a", ""):
                return []
            return [x.strip() for x in s.split(",") if x.strip()]

        def parse_mechanisms(s: str) -> list[MechanismType]:
            items = parse_list(s)
            result = []
            for item in items:
                # Try to match to MechanismType
                item_lower = item.lower().replace(" ", "_").replace("-", "_")
                for mt in MechanismType:
                    if mt.value == item_lower or mt.name.lower() == item_lower:
                        result.append(mt)
                        break
            return result

        def parse_json(s: str, default: list) -> list:
            if not s or s.lower() in ("none", "n/a", "[]", ""):
                return default
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                return default

        def parse_uncertainty(s: str) -> list[UncertaintySource]:
            items = parse_list(s)
            result = []
            for item in items:
                item_upper = item.upper().replace(" ", "_")
                for us in UncertaintySource:
                    if us.value == item_upper or us.name == item_upper:
                        result.append(us)
                        break
            return result

        # Parse complexity
        complexity_map = {
            "light": Complexity.LIGHT,
            "medium_light": Complexity.MEDIUM_LIGHT,
            "medium-light": Complexity.MEDIUM_LIGHT,
            "medium": Complexity.MEDIUM,
            "medium_heavy": Complexity.MEDIUM_HEAVY,
            "medium-heavy": Complexity.MEDIUM_HEAVY,
            "heavy": Complexity.HEAVY,
        }
        complexity = complexity_map.get(
            result.complexity.lower().replace(" ", "_"),
            Complexity.MEDIUM
        )

        # Parse game type
        game_type_map = {
            "strategy": GameType.STRATEGY,
            "party": GameType.PARTY,
            "family": GameType.FAMILY,
            "thematic": GameType.THEMATIC,
            "abstract": GameType.ABSTRACT,
            "euro": GameType.EURO,
        }
        game_type = game_type_map.get(result.game_type.lower(), GameType.STRATEGY)

        # Parse interaction type
        interaction_map = {
            "competitive": InteractionType.COMPETITIVE,
            "cooperative": InteractionType.COOPERATIVE,
            "team_based": InteractionType.TEAM_BASED,
            "team-based": InteractionType.TEAM_BASED,
            "semi_cooperative": InteractionType.SEMI_COOPERATIVE,
            "semi-cooperative": InteractionType.SEMI_COOPERATIVE,
        }
        interaction = interaction_map.get(
            result.interaction_type.lower().replace(" ", "_"),
            InteractionType.COMPETITIVE
        )

        # Parse board type
        board_type_map = {
            "none": BoardType.NONE,
            "fixed": BoardType.FIXED,
            "modular": BoardType.MODULAR,
            "player_built": BoardType.PLAYER_BUILT,
            "player-built": BoardType.PLAYER_BUILT,
            "track": BoardType.TRACK,
        }
        board_type = board_type_map.get(
            result.board_type.lower().replace(" ", "_"),
            BoardType.NONE
        )

        # Build components
        components = ComponentSet(
            board_description=(
                result.board_description
                if result.board_description.lower() not in ("none", "n/a")
                else None
            ),
            board_type=board_type,
            cards=parse_json(result.cards_json, []),
            tokens=parse_json(result.tokens_json, []),
            dice=parse_json(result.dice_json, []),
            other=parse_list(result.other_components),
        )

        # Build turn structure
        turn_structure = TurnStructure(
            phases=parse_list(result.turn_phases),
            actions_per_turn=result.actions_per_turn,
        )

        # Build player dynamics
        players = PlayerDynamics(
            min_players=result.min_players,
            max_players=result.max_players,
            interaction_type=interaction,
        )

        # Build ontology
        return GameOntology(
            title=result.title,
            tagline=result.tagline,
            theme=result.theme_description,
            game_type=game_type,
            complexity=complexity,
            goal=result.goal,
            end_condition=result.end_condition,
            victory_condition=result.victory_condition,
            primary_mechanisms=parse_mechanisms(result.primary_mechanisms),
            secondary_mechanisms=parse_mechanisms(result.secondary_mechanisms),
            turn_structure=turn_structure,
            uncertainty_sources=parse_uncertainty(result.uncertainty_sources),
            components=components,
            players=players,
            setup=result.setup,
            core_loop=result.core_loop,
            strategic_depth=result.strategic_depth,
            theme_integration=result.theme_integration,
            agency_justification=result.agency_justification,
            play_time_minutes=result.play_time_minutes,
        )

    def forward(self, theme: str, constraints: str) -> GameOntology:
        """Generate a game design with RAG enhancement.

        Args:
            theme: The thematic concept for the game
            constraints: Design constraints string

        Returns:
            Generated GameOntology
        """
        # Retrieve similar games
        similar_games = self.retriever.retrieve_for_theme(
            theme=theme,
            constraints=constraints,
            n_results=self.n_results,
        )

        # Get mechanism options
        mechanism_options = self._get_mechanism_options()

        # Generate
        result = self.generator(
            theme=theme,
            constraints=constraints,
            mechanism_options=mechanism_options,
            similar_games=similar_games,
        )

        # Parse to GameOntology
        return self._parse_output(result)
