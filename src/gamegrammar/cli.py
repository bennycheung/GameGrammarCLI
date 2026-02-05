"""Command-line interface for GameGrammar."""

import json
import os
import sys
from pathlib import Path
from typing import List, Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from gamegrammar.output.formatter import OutputFormat, OutputFormatter
from gamegrammar.schemas.game import GameOntology
from gamegrammar.validation.validator import OntologyValidator

# Load environment variables
load_dotenv()

# Default model (can be overridden via GAMEGRAMMAR_MODEL env var)
DEFAULT_MODEL = "anthropic/claude-sonnet-4-20250514"


def get_default_model() -> str:
    """Get the default model from env var or fallback."""
    return os.getenv("GAMEGRAMMAR_MODEL", DEFAULT_MODEL)


app = typer.Typer(
    name="gamegrammar",
    help="Generative Ontology for Board Game Design using DSPy",
    no_args_is_help=True,
)

# RAG command group
rag_app = typer.Typer(
    name="rag",
    help="RAG (Retrieval-Augmented Generation) commands for game knowledge",
)
app.add_typer(rag_app, name="rag")

console = Console()
formatter = OutputFormatter()


def get_format_extension(fmt: OutputFormat) -> str:
    """Get file extension for an output format."""
    return {
        OutputFormat.JSON: ".json",
        OutputFormat.MARKDOWN: ".md",
        OutputFormat.CONSOLE: ".txt",
    }[fmt]


def resolve_input(value: str) -> str:
    """Resolve input value - if it's a file path, read the file contents.

    Args:
        value: Either a direct string value or a path to a file

    Returns:
        The string value (either as-is or read from file)
    """
    path = Path(value)
    if path.exists() and path.is_file():
        content = path.read_text().strip()
        console.print(f"[dim]Read input from {path}[/dim]")
        return content
    return value


def configure_dspy(model: str) -> None:
    """Configure DSPy with the specified model."""
    import dspy

    # Check for API keys
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if model.startswith("anthropic/") or model.startswith("claude"):
        if not anthropic_key:
            console.print(
                "[red]Error: ANTHROPIC_API_KEY environment variable not set[/red]"
            )
            raise typer.Exit(1)
        lm = dspy.LM(model, api_key=anthropic_key)
    elif model.startswith("openai/") or model.startswith("gpt"):
        if not openai_key:
            console.print(
                "[red]Error: OPENAI_API_KEY environment variable not set[/red]"
            )
            raise typer.Exit(1)
        lm = dspy.LM(model, api_key=openai_key)
    else:
        # Try with available key
        if anthropic_key:
            lm = dspy.LM(model, api_key=anthropic_key)
        elif openai_key:
            lm = dspy.LM(model, api_key=openai_key)
        else:
            console.print(
                "[red]Error: No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY[/red]"
            )
            raise typer.Exit(1)

    dspy.configure(lm=lm)


@app.command()
def generate(
    theme: str = typer.Option(
        ...,
        "--theme",
        "-t",
        help="The thematic concept for the game (or path to a file containing it)",
    ),
    constraints: str = typer.Option(
        "2-4 players, competitive, medium complexity",
        "--constraints",
        "-c",
        help="Design constraints (or path to a file containing them)",
    ),
    output: List[OutputFormat] = typer.Option(
        [OutputFormat.CONSOLE],
        "--output",
        "-o",
        help="Output format(s) - can be specified multiple times (e.g., -o json -o markdown)",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help=f"LLM model to use (default: $GAMEGRAMMAR_MODEL or {DEFAULT_MODEL})",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show agent reasoning",
    ),
    multi_agent: bool = typer.Option(
        False,
        "--multi-agent",
        help="Use multi-agent pipeline instead of single-pass",
    ),
    rag: bool = typer.Option(
        False,
        "--rag",
        help="Use RAG to inform generation with similar existing games",
    ),
    output_file: Optional[Path] = typer.Option(
        None,
        "--file",
        "-f",
        help="Write output to file instead of stdout",
    ),
) -> None:
    """Generate a board game design from a theme and constraints."""
    # Resolve file inputs if provided as paths
    theme = resolve_input(theme)
    constraints = resolve_input(constraints)

    # Resolve model: CLI flag > env var > default
    resolved_model = model or get_default_model()
    console.print(f"[dim]Using model: {resolved_model}[/dim]")
    configure_dspy(resolved_model)

    from gamegrammar.agents.pipeline import (
        MultiAgentOntologyPipeline,
        SinglePassGenerator,
    )

    try:
        if rag:
            # Check if RAG is available
            try:
                from gamegrammar.rag import RAGSinglePassGenerator
                from gamegrammar.rag.storage import GameRAGStorage

                storage = GameRAGStorage()
                stats = storage.get_collection_stats()

                if stats["count"] == 0:
                    console.print(
                        "[yellow]Warning: No games indexed for RAG. "
                        "Run 'gamegrammar rag collect' and 'gamegrammar rag index' first.[/yellow]"
                    )
                    console.print("[cyan]Falling back to single-pass generator...[/cyan]")
                    generator = SinglePassGenerator()
                else:
                    console.print(
                        f"[cyan]Using RAG with {stats['count']} indexed games...[/cyan]"
                    )
                    generator = RAGSinglePassGenerator()
            except ImportError as e:
                console.print(
                    f"[yellow]Warning: RAG dependencies not available: {e}[/yellow]"
                )
                console.print("[cyan]Falling back to single-pass generator...[/cyan]")
                generator = SinglePassGenerator()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Generating game design with RAG...", total=None)
                game = generator(theme=theme, constraints=constraints)
                progress.update(task, completed=True, description="Complete!")

        elif multi_agent:
            console.print("[cyan]Using multi-agent pipeline...[/cyan]")
            pipeline = MultiAgentOntologyPipeline()

            def progress_callback(stage: str, data) -> None:
                if verbose and isinstance(data, str):
                    console.print(f"[dim]{stage}: {data}[/dim]")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Generating game design...", total=None)

                results = pipeline(
                    theme=theme,
                    constraints=constraints,
                    progress_callback=progress_callback if verbose else None,
                )

                progress.update(task, completed=True, description="Complete!")

            game = results["ontology"]

            if verbose:
                console.print()
                console.print("[bold]Balance Critique:[/bold]")
                critique = results.get("balance_critique")
                if critique:
                    console.print(f"  Issues: {len(critique.issues)}")
                    for issue in critique.issues[:3]:
                        console.print(f"    - {issue.get('issue', 'N/A')}")

                console.print()
                console.print("[bold]Fun Assessment:[/bold]")
                fun = results.get("fun_assessment")
                if fun:
                    console.print(f"  Rating: {fun.fun_rating}/10")
                    console.print(f"  Hooks: {', '.join(fun.engagement_hooks[:3])}")
                console.print()

        else:
            console.print("[cyan]Using single-pass generator...[/cyan]")
            generator = SinglePassGenerator()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Generating game design...", total=None)
                game = generator(theme=theme, constraints=constraints)
                progress.update(task, completed=True, description="Complete!")

        # Validate the generated game
        validator = OntologyValidator()
        validation = validator.validate(game)

        if not validation.valid:
            console.print()
            console.print("[yellow]Warning: Generated design has validation issues[/yellow]")
            if verbose:
                formatter.print_validation(validation)

        # Output the result(s)
        # Determine base filename for multi-format file output
        base_path = output_file.with_suffix("") if output_file else None

        for fmt in output:
            formatted = formatter.format(game, fmt)

            if output_file:
                # When writing to file, use appropriate extension for each format
                if len(output) > 1:
                    # Multiple formats: append extension to base name
                    file_path = Path(str(base_path) + get_format_extension(fmt))
                else:
                    # Single format: use provided filename as-is
                    file_path = output_file
                file_path.write_text(formatted)
                console.print(f"[green]Written {fmt.value} to {file_path}[/green]")
            elif fmt == OutputFormat.CONSOLE:
                console.print()
                formatter.print_console(game)
            else:
                # Print to stdout for non-console formats when no file specified
                console.print(formatted)

    except Exception as e:
        console.print(f"[red]Error generating game: {e}[/red]")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command()
def validate(
    file: Path = typer.Option(
        ...,
        "--file",
        "-f",
        help="Path to game JSON file to validate",
        exists=True,
        readable=True,
    ),
) -> None:
    """Validate a game design from a JSON file."""
    try:
        with open(file) as f:
            data = json.load(f)

        game = GameOntology.model_validate(data)
        validator = OntologyValidator()
        result = validator.validate(game)

        formatter.print_validation(result)

        if not result.valid:
            raise typer.Exit(1)

    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Validation error: {e}[/red]")
        raise typer.Exit(1)


@app.command("list-mechanisms")
def list_mechanisms() -> None:
    """List all available game mechanisms organized by category."""
    formatter.print_mechanisms_list()


@app.command()
def info() -> None:
    """Show information about GameGrammar."""
    from gamegrammar import __version__

    console.print(f"[bold magenta]GameGrammar[/bold magenta] v{__version__}")
    console.print()
    console.print("Generative Ontology for Board Game Design using DSPy")
    console.print()
    console.print("[bold]Available Commands:[/bold]")
    console.print("  generate        Generate a new game design")
    console.print("  validate        Validate a game design file")
    console.print("  list-mechanisms List available game mechanisms")
    console.print("  rag             RAG commands (collect, index, search)")
    console.print()
    console.print("[bold]Environment Variables:[/bold]")

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    model_env = os.getenv("GAMEGRAMMAR_MODEL")
    bgg_token = os.getenv("BGG_API_TOKEN")

    console.print(
        f"  ANTHROPIC_API_KEY:  {'[green]Set[/green]' if anthropic_key else '[red]Not set[/red]'}"
    )
    console.print(
        f"  OPENAI_API_KEY:     {'[green]Set[/green]' if openai_key else '[red]Not set[/red]'}"
    )
    console.print(
        f"  BGG_API_TOKEN:      {'[green]Set[/green]' if bgg_token else '[yellow]Not set (required for rag collect)[/yellow]'}"
    )
    console.print(
        f"  GAMEGRAMMAR_MODEL:  {f'[green]{model_env}[/green]' if model_env else f'[dim](default: {DEFAULT_MODEL})[/dim]'}"
    )

    # RAG status
    console.print()
    console.print("[bold]RAG Status:[/bold]")
    try:
        from gamegrammar.rag.collector import BGGCollector
        from gamegrammar.rag.storage import GameRAGStorage

        collector = BGGCollector()
        game_count = collector.get_game_count()

        storage = GameRAGStorage()
        stats = storage.get_collection_stats()

        console.print(f"  Games collected:  {game_count}")
        console.print(f"  Games indexed:    {stats['count']}")
    except ImportError:
        console.print("  [yellow]RAG dependencies not installed[/yellow]")
    except Exception as e:
        console.print(f"  [yellow]RAG not configured: {e}[/yellow]")


# ============================================================================
# RAG Commands
# ============================================================================


@rag_app.command()
def collect(
    limit: int = typer.Option(
        5000,
        "--limit",
        "-l",
        help="Maximum number of games to collect",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Re-collect games even if already in database",
    ),
) -> None:
    """Collect game data from BoardGameGeek API."""
    try:
        from gamegrammar.rag.collector import BGGCollector

        collector = BGGCollector(console=console)

        console.print("[bold]BGG Data Collection[/bold]")
        console.print(f"Limit: {limit} games")
        console.print(f"Rate limit: {collector.RATE_LIMIT_DELAY}s between requests")
        console.print()

        collected = collector.collect(limit=limit, skip_existing=not force)

        console.print()
        console.print(f"[bold green]Collection complete![/bold green]")
        console.print(f"Total games in database: {collector.get_game_count()}")

    except ImportError as e:
        console.print(f"[red]Error: Missing dependencies for RAG: {e}[/red]")
        console.print("Install with: uv add chromadb sentence-transformers requests")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error collecting games: {e}[/red]")
        raise typer.Exit(1)


@rag_app.command()
def index(
    force: bool = typer.Option(
        False,
        "--force",
        help="Clear and re-index all games",
    ),
) -> None:
    """Index collected games into ChromaDB for semantic search."""
    try:
        from gamegrammar.rag.collector import BGGCollector
        from gamegrammar.rag.storage import GameRAGStorage

        collector = BGGCollector(console=console)
        storage = GameRAGStorage(console=console)

        game_count = collector.get_game_count()
        if game_count == 0:
            console.print(
                "[yellow]No games in database. Run 'gamegrammar rag collect' first.[/yellow]"
            )
            raise typer.Exit(1)

        console.print("[bold]Game Indexing[/bold]")
        console.print(f"Games in database: {game_count}")
        console.print()

        if force:
            console.print("[yellow]Clearing existing index...[/yellow]")
            storage.clear_collection()

        indexed = storage.index_games()

        stats = storage.get_collection_stats()
        console.print()
        console.print(f"[bold green]Indexing complete![/bold green]")
        console.print(f"Total games in index: {stats['count']}")

    except ImportError as e:
        console.print(f"[red]Error: Missing dependencies for RAG: {e}[/red]")
        console.print("Install with: uv add chromadb sentence-transformers")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error indexing games: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        raise typer.Exit(1)


@rag_app.command()
def search(
    query: str = typer.Option(
        ...,
        "--query",
        "-q",
        help="Search query (e.g., 'deck building area control')",
    ),
    limit: int = typer.Option(
        5,
        "--limit",
        "-n",
        help="Number of results to return",
    ),
    complexity: Optional[str] = typer.Option(
        None,
        "--complexity",
        help="Filter by complexity (light, medium_light, medium, medium_heavy, heavy)",
    ),
    players: Optional[int] = typer.Option(
        None,
        "--players",
        "-p",
        help="Filter by player count",
    ),
    min_rating: Optional[float] = typer.Option(
        None,
        "--min-rating",
        help="Minimum BGG rating",
    ),
) -> None:
    """Search indexed games by semantic similarity."""
    try:
        from gamegrammar.rag.storage import GameRAGStorage

        storage = GameRAGStorage(console=console)
        stats = storage.get_collection_stats()

        if stats["count"] == 0:
            console.print(
                "[yellow]No games indexed. Run 'gamegrammar rag index' first.[/yellow]"
            )
            raise typer.Exit(1)

        console.print(f"[dim]Searching {stats['count']} games...[/dim]")
        console.print()

        results = storage.search_similar_games(
            query=query,
            n_results=limit,
            complexity_filter=complexity,
            player_count=players,
            min_rating=min_rating,
        )

        if not results:
            console.print("[yellow]No matching games found.[/yellow]")
            return

        # Display results in a table
        table = Table(title=f"Search Results for: {query}")
        table.add_column("Rank", style="dim", width=4)
        table.add_column("Name", style="bold")
        table.add_column("Rating", justify="right")
        table.add_column("Players", justify="center")
        table.add_column("Complexity")
        table.add_column("Mechanisms", max_width=40)

        for i, result in enumerate(results, 1):
            meta = result.get("metadata", {})
            table.add_row(
                str(i),
                meta.get("name", "Unknown"),
                f"{meta.get('rating', 0):.1f}",
                f"{meta.get('min_players', 1)}-{meta.get('max_players', 1)}",
                meta.get("complexity", "?"),
                meta.get("mechanisms", "")[:40],
            )

        console.print(table)

    except ImportError as e:
        console.print(f"[red]Error: Missing dependencies for RAG: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error searching games: {e}[/red]")
        raise typer.Exit(1)


@rag_app.command()
def stats() -> None:
    """Show RAG system statistics."""
    try:
        from gamegrammar.rag.collector import BGGCollector
        from gamegrammar.rag.mapping import BGGMechanismMapping
        from gamegrammar.rag.storage import GameRAGStorage

        console.print("[bold]RAG System Statistics[/bold]")
        console.print()

        # Collector stats
        collector = BGGCollector(console=console)
        game_count = collector.get_game_count()
        console.print(f"[bold]Database:[/bold]")
        console.print(f"  Games collected: {game_count}")
        console.print(f"  Database path:   {collector.db_path}")

        # Top mechanics
        if game_count > 0:
            mechanics = collector.get_all_mechanics()[:10]
            console.print()
            console.print("[bold]Top 10 Mechanics (BGG):[/bold]")
            for mech, count in mechanics:
                console.print(f"  {mech}: {count}")

        # Storage stats
        console.print()
        storage = GameRAGStorage(console=console)
        stats = storage.get_collection_stats()
        console.print(f"[bold]Vector Index:[/bold]")
        console.print(f"  Games indexed:    {stats['count']}")
        console.print(f"  Index path:       {stats['persist_directory']}")

        # Mapping stats
        console.print()
        mapping_stats = BGGMechanismMapping.mapping_coverage()
        console.print(f"[bold]Mechanism Mapping:[/bold]")
        console.print(f"  BGG mechanisms mapped:   {mapping_stats['mapped']}")
        console.print(f"  BGG mechanisms unmapped: {mapping_stats['unmapped']}")
        console.print(f"  GameGrammar types:       {mapping_stats['gamegrammar_types']}")

    except ImportError as e:
        console.print(f"[red]Error: Missing dependencies for RAG: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error getting stats: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
