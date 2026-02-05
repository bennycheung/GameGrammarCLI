"""Component Designer agent for physical game components."""

import dspy

from .signatures import (
    ComponentDesign,
    ComponentDesignerSignature,
    MechanicsDesign,
    ThematicDesign,
)


class ComponentDesigner(dspy.Module):
    """Agent that designs physical game components.

    Specifies components that are functional, tactile, and enhance
    the player experience. Considers table presence and manipulation.
    """

    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(ComponentDesignerSignature)

    def forward(
        self, theme: ThematicDesign, mechanics: MechanicsDesign, constraints: str
    ) -> ComponentDesign:
        """Generate a component design for the game.

        Args:
            theme: The thematic design from ThemeWeaver
            mechanics: The mechanics design from MechanicsArchitect
            constraints: Design constraints

        Returns:
            ComponentDesign with all physical components specified
        """
        result = self.generate(
            theme=theme,
            mechanics=mechanics,
            constraints=constraints,
        )

        return result.design


def create_component_designer() -> ComponentDesigner:
    """Factory function to create a configured ComponentDesigner."""
    return ComponentDesigner()
