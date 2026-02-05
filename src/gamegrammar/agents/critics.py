"""Critic agents for game balance and fun assessment."""

import dspy

from .signatures import (
    BalanceCritique,
    BalanceCriticSignature,
    ComponentDesign,
    FunFactorAssessment,
    FunFactorJudgeSignature,
    MechanicsDesign,
    ThematicDesign,
)


class BalanceCritic(dspy.Module):
    """Agent that analyzes game balance issues.

    Identifies potential issues with game balance, dominant strategies,
    and player count scaling. Provides constructive recommendations.
    """

    def __init__(self):
        super().__init__()
        self.analyze = dspy.ChainOfThought(BalanceCriticSignature)

    def forward(
        self,
        game_summary: str,
        mechanics: MechanicsDesign,
        components: ComponentDesign,
    ) -> BalanceCritique:
        """Analyze the game design for balance issues.

        Args:
            game_summary: Summary of the game design
            mechanics: The mechanics design
            components: The component design

        Returns:
            BalanceCritique with identified issues and recommendations
        """
        result = self.analyze(
            game_summary=game_summary,
            mechanics=mechanics,
            components=components,
        )

        return result.critique


class FunFactorJudge(dspy.Module):
    """Agent that assesses how fun the game is likely to be.

    Evaluates engagement hooks, tension sources, and memorable moments.
    Provides a fun rating and improvement suggestions.
    """

    def __init__(self):
        super().__init__()
        self.assess = dspy.ChainOfThought(FunFactorJudgeSignature)

    def forward(
        self,
        game_summary: str,
        mechanics: MechanicsDesign,
        theme: ThematicDesign,
    ) -> FunFactorAssessment:
        """Assess the fun factor of the game design.

        Args:
            game_summary: Summary of the game design
            mechanics: The mechanics design
            theme: The thematic design

        Returns:
            FunFactorAssessment with engagement analysis and rating
        """
        result = self.assess(
            game_summary=game_summary,
            mechanics=mechanics,
            theme=theme,
        )

        return result.assessment


def create_balance_critic() -> BalanceCritic:
    """Factory function to create a configured BalanceCritic."""
    return BalanceCritic()


def create_fun_factor_judge() -> FunFactorJudge:
    """Factory function to create a configured FunFactorJudge."""
    return FunFactorJudge()
