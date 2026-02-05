"""Output formatting for game ontologies."""

import json
from enum import Enum
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from gamegrammar.schemas.game import GameOntology
from gamegrammar.validation.validator import ValidationResult, Severity


class OutputFormat(str, Enum):
    """Available output formats."""

    JSON = "json"
    MARKDOWN = "markdown"
    CONSOLE = "console"


class OutputFormatter:
    """Formats game ontologies for different output types."""

    def __init__(self):
        self.console = Console()

    def format(self, game: GameOntology, fmt: OutputFormat) -> str:
        """Format a game ontology.

        Args:
            game: The game ontology to format
            fmt: Output format

        Returns:
            Formatted string
        """
        if fmt == OutputFormat.JSON:
            return self.to_json(game)
        elif fmt == OutputFormat.MARKDOWN:
            return self.to_markdown(game)
        else:
            return self.to_console_string(game)

    def to_json(self, game: GameOntology) -> str:
        """Export game ontology as JSON."""
        return game.model_dump_json(indent=2)

    def to_markdown(self, game: GameOntology) -> str:
        """Export game ontology as Markdown document."""
        lines = [
            f"# {game.title}",
            "",
            f"*{game.tagline}*" if game.tagline else "",
            "",
            "## Overview",
            "",
            f"**Type:** {game.game_type.value.title()}  ",
            f"**Complexity:** {game.complexity.value.replace('_', ' ').title()}  ",
            f"**Players:** {game.players.min_players}-{game.players.max_players}  ",
            f"**Interaction:** {game.players.interaction.value.replace('_', ' ').title()}  ",
            f"**Play Time:** {game.play_time_minutes} minutes"
            if game.play_time_minutes
            else "",
            "",
            "## Theme",
            "",
            game.theme,
            "",
        ]

        if game.theme_integration:
            lines.extend(
                [
                    "### Theme Integration",
                    "",
                    game.theme_integration,
                    "",
                ]
            )

        lines.extend(
            [
                "## Goals",
                "",
                f"**Objective:** {game.goal}  ",
                f"**End Condition:** {game.end_condition}  ",
                f"**Victory:** {game.victory_condition}",
                "",
                "## Mechanisms",
                "",
                "### Primary Mechanisms",
                "",
            ]
        )

        for mech in game.primary_mechanisms:
            lines.append(f"- **{mech.value.replace('_', ' ').title()}**: {mech.description}")

        if game.secondary_mechanisms:
            lines.extend(
                [
                    "",
                    "### Secondary Mechanisms",
                    "",
                ]
            )
            for mech in game.secondary_mechanisms:
                lines.append(f"- **{mech.value.replace('_', ' ').title()}**: {mech.description}")

        lines.extend(
            [
                "",
                "## Turn Structure",
                "",
                f"**Actions per turn:** {game.turn_structure.actions_per_turn or 'Variable'}",
                "",
                "### Phases",
                "",
            ]
        )

        for i, phase in enumerate(game.turn_structure.phases, 1):
            lines.append(f"{i}. {phase}")

        if game.uncertainty_sources:
            lines.extend(
                [
                    "",
                    "## Uncertainty Sources",
                    "",
                ]
            )
            for source in game.uncertainty_sources:
                lines.append(f"- {source.value.replace('_', ' ').title()}")

        lines.extend(
            [
                "",
                "## Components",
                "",
            ]
        )

        if game.components.board:
            lines.append(f"**Board:** {game.components.board}")
            lines.append(f"**Board Type:** {game.components.board_type.value.replace('_', ' ').title()}")
            lines.append("")

        if game.components.cards:
            lines.extend(["### Cards", ""])
            for card in game.components.cards:
                lines.append(
                    f"- **{card.name}** ({card.count} cards): {card.purpose}"
                )
            lines.append("")

        if game.components.tokens:
            lines.extend(["### Tokens", ""])
            for token in game.components.tokens:
                lines.append(
                    f"- **{token.name}** ({token.count}): {token.purpose}"
                )
            lines.append("")

        if game.components.dice:
            lines.extend(["### Dice", ""])
            for die in game.components.dice:
                lines.append(f"- **{die.type}** x{die.count}: {die.purpose}")
            lines.append("")

        if game.components.other:
            lines.extend(["### Other Components", ""])
            for comp in game.components.other:
                lines.append(f"- {comp}")
            lines.append("")

        lines.extend(
            [
                "## Setup",
                "",
                game.setup,
                "",
                "## Gameplay",
                "",
                "### Core Loop",
                "",
                game.core_loop,
                "",
            ]
        )

        if game.strategic_depth:
            lines.extend(
                [
                    "### Strategic Depth",
                    "",
                    game.strategic_depth,
                    "",
                ]
            )

        if game.agency_justification:
            lines.extend(
                [
                    "### Player Agency",
                    "",
                    game.agency_justification,
                    "",
                ]
            )

        if game.design_notes:
            lines.extend(
                [
                    "## Designer Notes",
                    "",
                    game.design_notes,
                    "",
                ]
            )

        return "\n".join(lines)

    def to_console_string(self, game: GameOntology) -> str:
        """Format for console output (plain text)."""
        return self.to_markdown(game)

    def print_console(self, game: GameOntology) -> None:
        """Print game ontology to console with rich formatting."""
        # Title panel
        title_text = Text()
        title_text.append(game.title, style="bold magenta")
        if game.tagline:
            title_text.append(f"\n{game.tagline}", style="italic cyan")

        self.console.print(Panel(title_text, title="Game Design", border_style="magenta"))
        self.console.print()

        # Overview table
        overview_table = Table(title="Overview", show_header=False, border_style="cyan")
        overview_table.add_column("Property", style="bold")
        overview_table.add_column("Value")

        overview_table.add_row("Type", game.game_type.value.title())
        overview_table.add_row("Complexity", game.complexity.value.replace("_", " ").title())
        overview_table.add_row(
            "Players",
            f"{game.players.min_players}-{game.players.max_players}",
        )
        overview_table.add_row(
            "Interaction",
            game.players.interaction.value.replace("_", " ").title(),
        )
        if game.play_time_minutes:
            overview_table.add_row("Play Time", f"{game.play_time_minutes} min")

        self.console.print(overview_table)
        self.console.print()

        # Theme
        self.console.print(Panel(game.theme, title="Theme", border_style="green"))
        self.console.print()

        # Mechanisms
        mech_table = Table(title="Mechanisms", border_style="yellow")
        mech_table.add_column("Type", style="bold")
        mech_table.add_column("Mechanism")
        mech_table.add_column("Description")

        for mech in game.primary_mechanisms:
            mech_table.add_row(
                "Primary",
                mech.value.replace("_", " ").title(),
                mech.description,
            )
        for mech in game.secondary_mechanisms:
            mech_table.add_row(
                "Secondary",
                mech.value.replace("_", " ").title(),
                mech.description,
            )

        self.console.print(mech_table)
        self.console.print()

        # Turn structure
        phases_text = "\n".join(
            f"  {i}. {phase}" for i, phase in enumerate(game.turn_structure.phases, 1)
        )
        turn_text = f"Actions per turn: {game.turn_structure.actions_per_turn or 'Variable'}\n\nPhases:\n{phases_text}"
        self.console.print(
            Panel(turn_text, title="Turn Structure", border_style="blue")
        )
        self.console.print()

        # Goals
        goals_text = f"Objective: {game.goal}\n\nEnd Condition: {game.end_condition}\n\nVictory: {game.victory_condition}"
        self.console.print(Panel(goals_text, title="Goals", border_style="red"))
        self.console.print()

        # Components summary
        comp_parts = []
        if game.components.board:
            comp_parts.append(f"Board: {game.components.board_type.value}")
        if game.components.cards:
            comp_parts.append(f"Cards: {len(game.components.cards)} deck(s)")
        if game.components.tokens:
            comp_parts.append(f"Tokens: {len(game.components.tokens)} type(s)")
        if game.components.dice:
            comp_parts.append(f"Dice: {len(game.components.dice)} type(s)")

        self.console.print(
            Panel("\n".join(comp_parts), title="Components", border_style="white")
        )

    def print_validation(self, result: ValidationResult) -> None:
        """Print validation results to console."""
        if result.valid:
            self.console.print("[green]Validation passed[/green]")
        else:
            self.console.print("[red]Validation failed[/red]")

        if result.issues:
            table = Table(title="Validation Issues", border_style="yellow")
            table.add_column("Severity", style="bold")
            table.add_column("Field")
            table.add_column("Message")
            table.add_column("Suggestion")

            for issue in result.issues:
                severity_style = {
                    Severity.ERROR: "red",
                    Severity.WARNING: "yellow",
                    Severity.INFO: "blue",
                }[issue.severity]

                table.add_row(
                    Text(issue.severity.value.upper(), style=severity_style),
                    issue.field or "-",
                    issue.message,
                    issue.suggestion or "-",
                )

            self.console.print(table)

    def print_mechanisms_list(self) -> None:
        """Print available mechanisms organized by category."""
        from gamegrammar.schemas.mechanisms import MechanismType

        categories = MechanismType.by_category()

        self.console.print(
            Panel("Available Game Mechanisms", style="bold magenta")
        )
        self.console.print()

        for category, mechanisms in categories.items():
            table = Table(title=category, border_style="cyan")
            table.add_column("Mechanism", style="bold")
            table.add_column("Value")
            table.add_column("Description")

            for mech in mechanisms:
                table.add_row(
                    mech.value.replace("_", " ").title(),
                    mech.value,
                    mech.description,
                )

            self.console.print(table)
            self.console.print()
