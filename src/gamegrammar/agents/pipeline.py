"""Multi-agent orchestration pipeline for game generation."""

import json
from typing import Any, Callable, Optional

import dspy

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

from .components import ComponentDesigner
from .critics import BalanceCritic, FunFactorJudge
from .mechanics import MechanicsArchitect
from .signatures import (
    BalanceCritique,
    ComponentDesign,
    FunFactorAssessment,
    GenerativeOntologySignature,
    MechanicsDesign,
    ThematicDesign,
)
from .theme import ThemeWeaver


class SinglePassGenerator(dspy.Module):
    """Single-pass game generator using one comprehensive prompt.

    Faster than the multi-agent pipeline but less nuanced.
    Good for quick iterations or when resources are limited.
    """

    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(GenerativeOntologySignature)

    def forward(
        self,
        theme: str,
        constraints: str,
        mechanism_options: str | None = None,
    ) -> GameOntology:
        """Generate a complete game ontology in a single pass.

        Args:
            theme: The thematic concept for the game
            constraints: Design constraints
            mechanism_options: Available mechanisms (defaults to all)

        Returns:
            Complete GameOntology
        """
        if mechanism_options is None:
            mechanism_options = self._get_mechanism_options()

        result = self.generate(
            theme=theme,
            constraints=constraints,
            mechanism_options=mechanism_options,
        )

        return self._build_ontology(result)

    @staticmethod
    def _get_mechanism_options() -> str:
        """Get formatted string of available mechanism options."""
        categories = MechanismType.by_category()
        lines = []
        for category, mechanisms in categories.items():
            mechs = ", ".join(m.value for m in mechanisms)
            lines.append(f"{category}: {mechs}")
        return "\n".join(lines)

    def _build_ontology(self, result: Any) -> GameOntology:
        """Build GameOntology from generator output."""
        # Parse mechanisms
        primary_mechanisms = self._parse_mechanisms(result.primary_mechanisms)
        secondary_mechanisms = self._parse_mechanisms(result.secondary_mechanisms)

        # Parse uncertainty sources
        uncertainty_sources = self._parse_uncertainty_sources(
            result.uncertainty_sources
        )

        # Parse components
        components = self._parse_components(
            board_type=result.board_type,
            board_description=result.board_description,
            cards_json=result.cards_json,
            tokens_json=result.tokens_json,
            dice_json=result.dice_json,
            other_components=result.other_components,
        )

        # Parse player dynamics
        players = PlayerDynamics(
            min_players=result.min_players,
            max_players=result.max_players,
            interaction=self._parse_interaction(result.interaction_type),
        )

        # Parse turn structure
        turn_structure = TurnStructure(
            phases=self._parse_list(result.turn_phases),
            actions_per_turn=result.actions_per_turn,
        )

        return GameOntology(
            title=result.title,
            tagline=result.tagline,
            theme=result.theme_description,
            theme_integration=result.theme_integration,
            game_type=self._parse_game_type(result.game_type),
            complexity=self._parse_complexity(result.complexity),
            goal=result.goal,
            end_condition=result.end_condition,
            victory_condition=result.victory_condition,
            primary_mechanisms=primary_mechanisms,
            secondary_mechanisms=secondary_mechanisms,
            turn_structure=turn_structure,
            uncertainty_sources=uncertainty_sources,
            components=components,
            players=players,
            setup=result.setup,
            core_loop=result.core_loop,
            strategic_depth=result.strategic_depth,
            agency_justification=result.agency_justification,
            play_time_minutes=result.play_time_minutes,
        )

    def _parse_mechanisms(self, mech_str: str) -> list[MechanismType]:
        """Parse comma-separated mechanism string."""
        if not mech_str or mech_str.lower() in ("none", "n/a", ""):
            return []
        mechanisms = []
        for m in mech_str.split(","):
            m = m.strip().lower().replace(" ", "_").replace("-", "_")
            try:
                mechanisms.append(MechanismType(m))
            except ValueError:
                # Try to find partial match
                for mtype in MechanismType:
                    if m in mtype.value or mtype.value in m:
                        mechanisms.append(mtype)
                        break
        return mechanisms

    def _parse_uncertainty_sources(self, source_str: str) -> list[UncertaintySource]:
        """Parse comma-separated uncertainty sources."""
        if not source_str or source_str.lower() in ("none", "n/a", ""):
            return []
        sources = []
        for s in source_str.split(","):
            s = s.strip().lower().replace(" ", "_").replace("-", "_")
            try:
                sources.append(UncertaintySource(s))
            except ValueError:
                for stype in UncertaintySource:
                    if s in stype.value or stype.value in s:
                        sources.append(stype)
                        break
        return sources

    def _parse_components(
        self,
        board_type: str,
        board_description: str,
        cards_json: str,
        tokens_json: str,
        dice_json: str,
        other_components: str,
    ) -> ComponentSet:
        """Parse component specifications."""
        # Parse board type
        try:
            bt = BoardType(board_type.lower().replace(" ", "_"))
        except ValueError:
            bt = BoardType.NONE if board_type.lower() == "none" else BoardType.FIXED

        # Parse cards
        cards = []
        try:
            cards_data = json.loads(cards_json) if cards_json else []
            for c in cards_data:
                cards.append(
                    CardComponent(
                        name=c.get("name", "Cards"),
                        count=c.get("count", 50),
                        purpose=c.get("purpose", "Gameplay"),
                        unique=c.get("unique", False),
                    )
                )
        except (json.JSONDecodeError, TypeError):
            pass

        # Parse tokens
        tokens = []
        try:
            tokens_data = json.loads(tokens_json) if tokens_json else []
            for t in tokens_data:
                tokens.append(
                    TokenComponent(
                        name=t.get("name", "Tokens"),
                        count=t.get("count", 20),
                        purpose=t.get("purpose", "Tracking"),
                    )
                )
        except (json.JSONDecodeError, TypeError):
            pass

        # Parse dice
        dice = []
        try:
            dice_data = json.loads(dice_json) if dice_json else []
            for d in dice_data:
                dice.append(
                    DiceComponent(
                        type=d.get("type", "d6"),
                        count=d.get("count", 1),
                        purpose=d.get("purpose", "Randomness"),
                    )
                )
        except (json.JSONDecodeError, TypeError):
            pass

        # Parse other components
        other = self._parse_list(other_components)

        return ComponentSet(
            board=board_description if board_description.lower() != "none" else None,
            board_type=bt,
            cards=cards,
            tokens=tokens,
            dice=dice,
            other=other,
        )

    def _parse_interaction(self, interaction_str: str) -> InteractionType:
        """Parse interaction type."""
        interaction_str = interaction_str.lower().replace(" ", "_").replace("-", "_")
        try:
            return InteractionType(interaction_str)
        except ValueError:
            return InteractionType.COMPETITIVE

    def _parse_game_type(self, type_str: str) -> GameType:
        """Parse game type."""
        type_str = type_str.lower().replace(" ", "_").replace("-", "_")
        try:
            return GameType(type_str)
        except ValueError:
            return GameType.STRATEGY

    def _parse_complexity(self, complexity_str: str) -> Complexity:
        """Parse complexity level."""
        complexity_str = complexity_str.lower().replace(" ", "_").replace("-", "_")
        try:
            return Complexity(complexity_str)
        except ValueError:
            return Complexity.MEDIUM

    def _parse_list(self, list_str: str) -> list[str]:
        """Parse comma-separated list."""
        if not list_str or list_str.lower() in ("none", "n/a", ""):
            return []
        return [s.strip() for s in list_str.split(",") if s.strip()]


class MultiAgentOntologyPipeline(dspy.Module):
    """Multi-agent pipeline for game generation.

    Orchestrates specialized agents in sequence:
    1. MechanicsArchitect - Core mechanics
    2. ThemeWeaver - Thematic integration
    3. ComponentDesigner - Physical components
    4. BalanceCritic - Balance analysis
    5. FunFactorJudge - Fun assessment

    Optionally refines design based on critic feedback.
    """

    def __init__(self, enable_refinement: bool = False):
        super().__init__()
        self.mechanics_architect = MechanicsArchitect()
        self.theme_weaver = ThemeWeaver()
        self.component_designer = ComponentDesigner()
        self.balance_critic = BalanceCritic()
        self.fun_factor_judge = FunFactorJudge()
        self.enable_refinement = enable_refinement

    def forward(
        self,
        theme: str,
        constraints: str,
        progress_callback: Optional[Callable[[str, Any], None]] = None,
    ) -> dict[str, Any]:
        """Generate a game design through the multi-agent pipeline.

        Args:
            theme: The thematic concept for the game
            constraints: Design constraints
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary containing all design outputs and the final GameOntology
        """
        results: dict[str, Any] = {}

        # Step 1: Mechanics
        if progress_callback:
            progress_callback("mechanics", "Starting mechanics design...")
        mechanics = self.mechanics_architect(theme=theme, constraints=constraints)
        results["mechanics"] = mechanics
        if progress_callback:
            progress_callback("mechanics", mechanics)

        # Step 2: Theme
        if progress_callback:
            progress_callback("theme", "Starting thematic design...")
        thematic = self.theme_weaver(
            theme=theme, mechanics=mechanics, constraints=constraints
        )
        results["theme"] = thematic
        if progress_callback:
            progress_callback("theme", thematic)

        # Step 3: Components
        if progress_callback:
            progress_callback("components", "Starting component design...")
        components = self.component_designer(
            theme=thematic, mechanics=mechanics, constraints=constraints
        )
        results["components"] = components
        if progress_callback:
            progress_callback("components", components)

        # Create game summary for critics
        game_summary = self._create_game_summary(thematic, mechanics, components)
        results["game_summary"] = game_summary

        # Step 4: Balance critique
        if progress_callback:
            progress_callback("balance", "Analyzing balance...")
        balance = self.balance_critic(
            game_summary=game_summary, mechanics=mechanics, components=components
        )
        results["balance_critique"] = balance
        if progress_callback:
            progress_callback("balance", balance)

        # Step 5: Fun assessment
        if progress_callback:
            progress_callback("fun", "Assessing fun factor...")
        fun = self.fun_factor_judge(
            game_summary=game_summary, mechanics=mechanics, theme=thematic
        )
        results["fun_assessment"] = fun
        if progress_callback:
            progress_callback("fun", fun)

        # Build final ontology
        ontology = self._build_ontology(
            mechanics=mechanics,
            theme=thematic,
            components=components,
            constraints=constraints,
        )
        results["ontology"] = ontology

        return results

    def _create_game_summary(
        self,
        theme: ThematicDesign,
        mechanics: MechanicsDesign,
        components: ComponentDesign,
    ) -> str:
        """Create a summary for critic agents."""
        return f"""
Title: {theme.title}
Tagline: {theme.tagline}
Setting: {theme.setting}

Primary Mechanisms: {', '.join(mechanics.primary_mechanisms)}
Secondary Mechanisms: {', '.join(mechanics.secondary_mechanisms)}
Turn Phases: {', '.join(mechanics.turn_phases)}
Actions Per Turn: {mechanics.actions_per_turn}

Components:
- Board: {components.board_type} - {components.board_description or 'N/A'}
- Cards: {len(components.cards)} types
- Tokens: {len(components.tokens)} types
- Dice: {len(components.dice)} types

Theme Integration: {theme.theme_integration}
Agency Justification: {mechanics.agency_justification}
"""

    def _build_ontology(
        self,
        mechanics: MechanicsDesign,
        theme: ThematicDesign,
        components: ComponentDesign,
        constraints: str,
    ) -> GameOntology:
        """Build GameOntology from agent outputs."""
        # Parse mechanisms
        primary_mechanisms = self._parse_mechanisms(mechanics.primary_mechanisms)
        secondary_mechanisms = self._parse_mechanisms(mechanics.secondary_mechanisms)

        # Parse uncertainty sources from mechanics
        uncertainty_sources = self._parse_uncertainty_sources(
            mechanics.uncertainty_sources
        )

        # Infer additional uncertainty sources from components
        inferred_sources = self._infer_uncertainty_from_components(components)
        for source in inferred_sources:
            if source not in uncertainty_sources:
                uncertainty_sources.append(source)

        # Build component set
        component_set = self._build_component_set(components)

        # Parse player counts from constraints
        min_players, max_players = self._parse_player_counts(constraints)

        # Determine interaction type from constraints
        interaction = self._parse_interaction_from_constraints(constraints)

        # Build turn structure
        turn_structure = TurnStructure(
            phases=mechanics.turn_phases,
            actions_per_turn=mechanics.actions_per_turn,
        )

        # Determine game type and complexity from constraints
        game_type = self._infer_game_type(mechanics, theme)
        complexity = self._infer_complexity(constraints)

        return GameOntology(
            title=theme.title,
            tagline=theme.tagline,
            theme=theme.setting,
            theme_integration=theme.theme_integration,
            game_type=game_type,
            complexity=complexity,
            goal=theme.goal,
            end_condition=theme.end_condition,
            victory_condition=theme.victory_condition,
            primary_mechanisms=primary_mechanisms,
            secondary_mechanisms=secondary_mechanisms,
            turn_structure=turn_structure,
            uncertainty_sources=uncertainty_sources,
            components=component_set,
            players=PlayerDynamics(
                min_players=min_players,
                max_players=max_players,
                interaction=interaction,
            ),
            setup=components.setup_instructions,
            core_loop=f"Each turn: {' -> '.join(mechanics.turn_phases)}",
            strategic_depth=mechanics.reasoning,
            agency_justification=mechanics.agency_justification,
        )

    def _parse_mechanisms(self, mech_list: list[str]) -> list[MechanismType]:
        """Parse mechanism strings to enums."""
        mechanisms = []
        for m in mech_list:
            m_normalized = m.strip().lower().replace(" ", "_").replace("-", "_")
            try:
                mechanisms.append(MechanismType(m_normalized))
            except ValueError:
                for mtype in MechanismType:
                    if m_normalized in mtype.value or mtype.value in m_normalized:
                        mechanisms.append(mtype)
                        break
        return mechanisms

    def _parse_uncertainty_sources(
        self, source_list: list[str]
    ) -> list[UncertaintySource]:
        """Parse uncertainty source strings to enums."""
        sources = []
        for s in source_list:
            s_normalized = s.strip().lower().replace(" ", "_").replace("-", "_")
            try:
                sources.append(UncertaintySource(s_normalized))
            except ValueError:
                for stype in UncertaintySource:
                    if s_normalized in stype.value or stype.value in s_normalized:
                        sources.append(stype)
                        break
        return sources

    def _build_component_set(self, components: ComponentDesign) -> ComponentSet:
        """Build ComponentSet from ComponentDesign."""
        # Parse board type
        try:
            board_type = BoardType(
                components.board_type.lower().replace(" ", "_")
            )
        except ValueError:
            board_type = (
                BoardType.NONE
                if components.board_type.lower() == "none"
                else BoardType.FIXED
            )

        # Build cards
        cards = []
        for c in components.cards:
            cards.append(
                CardComponent(
                    name=c.get("name", "Cards"),
                    count=c.get("count", 50),
                    purpose=c.get("purpose", "Gameplay"),
                    unique=c.get("unique", False),
                )
            )

        # Build tokens
        tokens = []
        for t in components.tokens:
            tokens.append(
                TokenComponent(
                    name=t.get("name", "Tokens"),
                    count=t.get("count", 20),
                    purpose=t.get("purpose", "Tracking"),
                )
            )

        # Build dice
        dice = []
        for d in components.dice:
            dice.append(
                DiceComponent(
                    type=d.get("type", "d6"),
                    count=d.get("count", 1),
                    purpose=d.get("purpose", "Randomness"),
                )
            )

        return ComponentSet(
            board=components.board_description,
            board_type=board_type,
            cards=cards,
            tokens=tokens,
            dice=dice,
            other=components.other_components,
        )

    def _parse_player_counts(self, constraints: str) -> tuple[int, int]:
        """Extract player counts from constraints string."""
        import re

        # Try to find patterns like "2-4 players" or "2 to 4 players"
        pattern = r"(\d+)\s*[-to]+\s*(\d+)\s*player"
        match = re.search(pattern, constraints.lower())
        if match:
            return int(match.group(1)), int(match.group(2))

        # Try single number "4 players"
        single_pattern = r"(\d+)\s*player"
        match = re.search(single_pattern, constraints.lower())
        if match:
            count = int(match.group(1))
            return count, count

        # Default
        return 2, 4

    def _parse_interaction_from_constraints(self, constraints: str) -> InteractionType:
        """Infer interaction type from constraints."""
        constraints_lower = constraints.lower()
        if "cooperative" in constraints_lower or "co-op" in constraints_lower:
            return InteractionType.COOPERATIVE
        if "team" in constraints_lower:
            return InteractionType.TEAM_BASED
        if "solo" in constraints_lower:
            return InteractionType.SOLO
        return InteractionType.COMPETITIVE

    def _infer_game_type(
        self, mechanics: MechanicsDesign, theme: ThematicDesign
    ) -> GameType:
        """Infer game type from mechanics and theme."""
        mech_set = {m.lower() for m in mechanics.primary_mechanisms}

        if "engine_building" in mech_set or "resource_management" in mech_set:
            return GameType.EURO
        if "combat" in mech_set or "area_control" in mech_set:
            return GameType.WAR
        if "bluffing" in mech_set or "negotiation" in mech_set:
            return GameType.PARTY

        return GameType.STRATEGY

    def _infer_complexity(self, constraints: str) -> Complexity:
        """Infer complexity from constraints."""
        constraints_lower = constraints.lower()
        # Check compound terms first (most specific)
        if "medium_heavy" in constraints_lower or "medium-heavy" in constraints_lower:
            return Complexity.MEDIUM_HEAVY
        if "medium_light" in constraints_lower or "medium-light" in constraints_lower:
            return Complexity.MEDIUM_LIGHT
        # Check for "medium complexity" before checking for "complex" alone
        if "medium complexity" in constraints_lower or "medium weight" in constraints_lower:
            return Complexity.MEDIUM
        # Now check single terms
        if "light" in constraints_lower or "simple" in constraints_lower:
            return Complexity.LIGHT
        if "heavy" in constraints_lower:
            return Complexity.HEAVY
        if "medium" in constraints_lower:
            return Complexity.MEDIUM
        return Complexity.MEDIUM

    def _infer_uncertainty_from_components(
        self, components: ComponentDesign
    ) -> list[UncertaintySource]:
        """Infer uncertainty sources from component design."""
        sources = []

        # Dice → DICE uncertainty
        if components.dice:
            sources.append(UncertaintySource.DICE)

        # Cards → CARDS and SHUFFLE uncertainty
        if components.cards:
            sources.append(UncertaintySource.CARDS)
            sources.append(UncertaintySource.SHUFFLE)

        return sources
