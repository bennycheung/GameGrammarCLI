"""Theme Weaver agent for thematic integration."""

import dspy

from .signatures import MechanicsDesign, ThematicDesign, ThemeWeaverSignature


class ThemeWeaver(dspy.Module):
    """Agent that integrates theme with mechanics.

    Ensures the theme enhances the mechanics and no mechanism
    feels "pasted on" - everything should connect thematically.
    """

    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(ThemeWeaverSignature)

    def forward(
        self, theme: str, mechanics: MechanicsDesign, constraints: str
    ) -> ThematicDesign:
        """Generate a thematic design that integrates with mechanics.

        Args:
            theme: The thematic concept
            mechanics: The designed mechanics from MechanicsArchitect
            constraints: Design constraints

        Returns:
            ThematicDesign with title, setting, and theme integration
        """
        result = self.generate(
            theme=theme,
            mechanics=mechanics,
            constraints=constraints,
        )

        return result.design


def create_theme_weaver() -> ThemeWeaver:
    """Factory function to create a configured ThemeWeaver."""
    return ThemeWeaver()
