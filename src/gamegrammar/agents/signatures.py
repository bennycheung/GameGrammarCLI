"""DSPy signatures for game generation agents."""

from typing import Optional

import dspy
from pydantic import BaseModel, Field


# ============================================================================
# Partial Output Schemas (used by specialized agents)
# ============================================================================


class MechanicsDesign(BaseModel):
    """Output from the Mechanics Architect agent."""

    primary_mechanisms: list[str] = Field(
        ..., description="Primary game mechanisms (use mechanism type values)"
    )
    secondary_mechanisms: list[str] = Field(
        default_factory=list, description="Supporting mechanisms"
    )
    turn_phases: list[str] = Field(..., description="Phases within each turn")
    actions_per_turn: str = Field(..., description="What players do on their turn")
    uncertainty_sources: list[str] = Field(
        ..., description="Sources of randomness/uncertainty"
    )
    agency_justification: str = Field(
        ..., description="Why players feel in control of outcomes"
    )
    reasoning: str = Field(..., description="Explanation of mechanism choices")


class ThematicDesign(BaseModel):
    """Output from the Theme Weaver agent."""

    title: str = Field(..., description="Game title")
    tagline: str = Field(..., description="Short memorable description")
    setting: str = Field(..., description="Detailed theme/setting description")
    narrative_hook: str = Field(..., description="What draws players into the story")
    theme_integration: str = Field(
        ..., description="How theme connects to mechanics"
    )
    goal: str = Field(..., description="What players are trying to achieve")
    end_condition: str = Field(..., description="How the game ends")
    victory_condition: str = Field(..., description="How the winner is determined")
    reasoning: str = Field(default="", description="Explanation of thematic choices")


class ComponentDesign(BaseModel):
    """Output from the Component Designer agent."""

    board_description: Optional[str] = Field(
        None, description="Board description if applicable"
    )
    board_type: str = Field(
        default="none", description="Type of board (none, fixed, modular, etc.)"
    )
    cards: list[dict] = Field(
        default_factory=list,
        description="Card decks [{name, count, purpose, unique}]",
    )
    tokens: list[dict] = Field(
        default_factory=list,
        description="Token types [{name, count, purpose}]",
    )
    dice: list[dict] = Field(
        default_factory=list,
        description="Dice [{type, count, purpose}]",
    )
    other_components: list[str] = Field(
        default_factory=list, description="Other physical components"
    )
    setup_instructions: str = Field(..., description="How to set up the game")
    reasoning: str = Field(..., description="Explanation of component choices")


class BalanceCritique(BaseModel):
    """Output from the Balance Critic agent."""

    issues: list[dict] = Field(
        ...,
        description="Balance issues [{issue, severity, recommendation}]",
    )
    dominant_strategies: list[str] = Field(
        default_factory=list, description="Potentially dominant strategies identified"
    )
    player_count_concerns: list[str] = Field(
        default_factory=list, description="Concerns about different player counts"
    )
    overall_assessment: str = Field(..., description="Overall balance assessment")
    recommendations: list[str] = Field(
        ..., description="Specific recommendations for improvement"
    )


class FunFactorAssessment(BaseModel):
    """Output from the Fun Factor Judge agent."""

    engagement_hooks: list[str] = Field(
        ..., description="What makes the game engaging"
    )
    tension_sources: list[str] = Field(
        ..., description="What creates tension/excitement"
    )
    memorable_moments: list[str] = Field(
        ..., description="Potential memorable moments"
    )
    player_agency_feel: str = Field(
        ..., description="How players feel about their agency"
    )
    fun_rating: int = Field(..., ge=1, le=10, description="Overall fun rating 1-10")
    improvement_suggestions: list[str] = Field(
        ..., description="Suggestions to increase fun"
    )


# ============================================================================
# DSPy Signatures
# ============================================================================


class GenerativeOntologySignature(dspy.Signature):
    """Generate a complete board game design from a theme and constraints.

    You are an expert board game designer. Create a complete, coherent game design
    that integrates theme and mechanics seamlessly. The game should be playable,
    balanced, and fun.
    """

    theme: str = dspy.InputField(desc="The thematic concept for the game")
    constraints: str = dspy.InputField(
        desc="Design constraints (player count, complexity, etc.)"
    )
    mechanism_options: str = dspy.InputField(
        desc="Available game mechanisms to choose from"
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


class MechanicsArchitectSignature(dspy.Signature):
    """Design the core mechanics and turn structure for a game.

    You are a game mechanics expert. Select and justify mechanisms that create
    interesting decisions and player agency. Explain how mechanisms interact.
    """

    theme: str = dspy.InputField(desc="The thematic concept for the game")
    constraints: str = dspy.InputField(desc="Design constraints")
    mechanism_options: str = dspy.InputField(desc="Available mechanisms to choose from")

    design: MechanicsDesign = dspy.OutputField(desc="The mechanics design")


class ThemeWeaverSignature(dspy.Signature):
    """Integrate theme with mechanics to create a cohesive experience.

    You are a thematic game designer. Ensure the theme enhances and is enhanced by
    the mechanics. No mechanism should feel "pasted on" - everything should connect.
    """

    theme: str = dspy.InputField(desc="The thematic concept")
    mechanics: MechanicsDesign = dspy.InputField(desc="The designed mechanics")
    constraints: str = dspy.InputField(desc="Design constraints")

    design: ThematicDesign = dspy.OutputField(desc="The thematic design")


class ComponentDesignerSignature(dspy.Signature):
    """Design the physical components that instantiate the game.

    You are a game component designer. Specify components that are functional,
    tactile, and enhance the player experience. Consider table presence.
    """

    theme: ThematicDesign = dspy.InputField(desc="The thematic design")
    mechanics: MechanicsDesign = dspy.InputField(desc="The mechanics design")
    constraints: str = dspy.InputField(desc="Design constraints")

    design: ComponentDesign = dspy.OutputField(desc="The component design")


class BalanceCriticSignature(dspy.Signature):
    """Analyze the game design for balance issues.

    You are a game balance analyst. Identify potential issues with game balance,
    dominant strategies, and player count scaling. Be constructive but thorough.
    """

    game_summary: str = dspy.InputField(desc="Summary of the game design")
    mechanics: MechanicsDesign = dspy.InputField(desc="The mechanics")
    components: ComponentDesign = dspy.InputField(desc="The components")

    critique: BalanceCritique = dspy.OutputField(desc="The balance critique")


class FunFactorJudgeSignature(dspy.Signature):
    """Assess how fun and engaging the game is likely to be.

    You are a play experience expert. Evaluate what makes the game fun, where
    tension comes from, and what memorable moments might occur.
    """

    game_summary: str = dspy.InputField(desc="Summary of the game design")
    mechanics: MechanicsDesign = dspy.InputField(desc="The mechanics")
    theme: ThematicDesign = dspy.InputField(desc="The theme")

    assessment: FunFactorAssessment = dspy.OutputField(desc="The fun assessment")


class RefinementSignature(dspy.Signature):
    """Refine a game design based on critique.

    You are a senior game designer. Take the feedback from critics and refine
    the design to address issues while preserving what works well.
    """

    current_design: str = dspy.InputField(desc="The current game design summary")
    balance_critique: BalanceCritique = dspy.InputField(desc="Balance feedback")
    fun_assessment: FunFactorAssessment = dspy.InputField(desc="Fun feedback")

    refined_mechanics: str = dspy.OutputField(desc="Refined mechanics description")
    refined_components: str = dspy.OutputField(desc="Refined components description")
    changes_made: str = dspy.OutputField(desc="Summary of changes made")
