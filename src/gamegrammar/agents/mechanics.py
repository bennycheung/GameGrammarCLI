"""Mechanics Architect agent for game mechanism design."""

import dspy

from gamegrammar.schemas.mechanisms import MechanismType

from .signatures import MechanicsArchitectSignature, MechanicsDesign


class MechanicsArchitect(dspy.Module):
    """Agent that designs game mechanics and turn structure.

    Uses chain-of-thought reasoning to select appropriate mechanisms
    and justify how they create player agency.
    """

    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(MechanicsArchitectSignature)

    def forward(
        self, theme: str, constraints: str, mechanism_options: str | None = None
    ) -> MechanicsDesign:
        """Generate a mechanics design for the given theme and constraints.

        Args:
            theme: The thematic concept for the game
            constraints: Design constraints (player count, complexity, etc.)
            mechanism_options: Available mechanisms (defaults to all)

        Returns:
            MechanicsDesign with selected mechanisms and justification
        """
        if mechanism_options is None:
            mechanism_options = self._get_mechanism_options()

        result = self.generate(
            theme=theme,
            constraints=constraints,
            mechanism_options=mechanism_options,
        )

        return result.design

    @staticmethod
    def _get_mechanism_options() -> str:
        """Get formatted string of available mechanism options."""
        categories = MechanismType.by_category()
        lines = []
        for category, mechanisms in categories.items():
            mechs = ", ".join(m.value for m in mechanisms)
            lines.append(f"{category}: {mechs}")
        return "\n".join(lines)


def create_mechanics_architect() -> MechanicsArchitect:
    """Factory function to create a configured MechanicsArchitect."""
    return MechanicsArchitect()
