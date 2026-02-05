"""ChromaDB vector storage for game embeddings.

Stores game data as embeddings for semantic search with metadata filtering.
"""

from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from gamegrammar.rag.collector import BGGCollector, BGGGame
from gamegrammar.rag.mapping import BGGMechanismMapping


def weight_to_complexity(weight: float) -> str:
    """Convert BGG weight (1-5) to complexity label.

    Args:
        weight: BGG average weight value (1-5 scale)

    Returns:
        Complexity label: light, medium_light, medium, medium_heavy, heavy
    """
    if weight < 1.5:
        return "light"
    elif weight < 2.25:
        return "medium_light"
    elif weight < 3.0:
        return "medium"
    elif weight < 3.75:
        return "medium_heavy"
    else:
        return "heavy"


class GameRAGStorage:
    """ChromaDB vector storage for game embeddings.

    Uses all-MiniLM-L6-v2 for embeddings (384 dimensions).
    Supports semantic search with metadata filtering.
    """

    COLLECTION_NAME = "gamegrammar_games"

    def __init__(
        self,
        persist_directory: Optional[Path] = None,
        console: Optional[Console] = None,
    ):
        """Initialize the storage.

        Args:
            persist_directory: Directory for ChromaDB persistence.
                              Defaults to data/chroma_db
            console: Rich console for output.
        """
        if persist_directory is None:
            persist_directory = (
                Path(__file__).parent.parent.parent.parent / "data" / "chroma_db"
            )

        self.persist_directory = persist_directory
        self.console = console or Console()

        # Initialize ChromaDB with persistence
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )

        # Get or create collection with sentence-transformers embedding function
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def _create_document(self, game: BGGGame) -> str:
        """Create document text for embedding.

        Structured to align with GameGrammar ontology concepts.

        Args:
            game: BGGGame object

        Returns:
            Document text for embedding
        """
        # Map BGG mechanics to GameGrammar mechanisms
        gg_mechanisms = BGGMechanismMapping.map_bgg_mechanisms(game.mechanics)
        mechanism_strs = [m.value for m in gg_mechanisms]

        # Truncate description
        desc = game.description[:500] if game.description else ""
        if len(game.description) > 500:
            desc += "..."

        # Build document
        parts = [
            f"Title: {game.name}",
        ]

        if game.year:
            parts.append(f"Year: {game.year}")

        if mechanism_strs:
            parts.append(f"Mechanisms: {', '.join(mechanism_strs)}")

        if game.categories:
            parts.append(f"Categories: {', '.join(game.categories[:5])}")

        if game.min_players or game.max_players:
            parts.append(f"Players: {game.min_players}-{game.max_players}")

        if game.weight > 0:
            complexity = weight_to_complexity(game.weight)
            parts.append(f"Complexity: {complexity}")

        if desc:
            parts.append(f"Description: {desc}")

        return "\n".join(parts)

    def _create_metadata(self, game: BGGGame) -> dict:
        """Create metadata for filtering.

        Args:
            game: BGGGame object

        Returns:
            Metadata dict for ChromaDB
        """
        gg_mechanisms = BGGMechanismMapping.map_bgg_mechanisms(game.mechanics)

        return {
            "name": game.name,
            "year": game.year or 0,
            "min_players": game.min_players,
            "max_players": game.max_players,
            "min_playtime": game.min_playtime,
            "max_playtime": game.max_playtime,
            "rating": game.rating,
            "weight": game.weight,
            "rank": game.rank or 99999,
            "complexity": weight_to_complexity(game.weight) if game.weight > 0 else "medium",
            # Store mechanisms as comma-separated string for filtering
            "mechanisms": ",".join(m.value for m in gg_mechanisms),
            # Store categories as comma-separated string
            "categories": ",".join(game.categories[:10]),
        }

    def index_games(
        self,
        games: Optional[list[BGGGame]] = None,
        batch_size: int = 100,
        db_path: Optional[Path] = None,
    ) -> int:
        """Index games into ChromaDB.

        Args:
            games: List of games to index. If None, reads from collector database.
            batch_size: Number of games to process per batch
            db_path: Path to collector database (if games is None)

        Returns:
            Number of games indexed
        """
        if games is None:
            collector = BGGCollector(db_path=db_path, console=self.console)
            games = collector.get_all_games()

        if not games:
            self.console.print("[yellow]No games to index[/yellow]")
            return 0

        self.console.print(f"[cyan]Indexing {len(games)} games...[/cyan]")

        # Get existing IDs to avoid duplicates
        existing_ids = set()
        try:
            result = self.collection.get()
            existing_ids = set(result["ids"])
        except Exception:
            pass

        # Filter out already indexed games
        new_games = [g for g in games if str(g.id) not in existing_ids]

        if not new_games:
            self.console.print("[green]All games already indexed![/green]")
            return 0

        self.console.print(
            f"[dim]Found {len(existing_ids)} existing, indexing {len(new_games)} new[/dim]"
        )

        indexed = 0
        batches = [
            new_games[i:i + batch_size]
            for i in range(0, len(new_games), batch_size)
        ]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task("Indexing...", total=len(new_games))

            for batch in batches:
                ids = [str(g.id) for g in batch]
                documents = [self._create_document(g) for g in batch]
                metadatas = [self._create_metadata(g) for g in batch]

                self.collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas,
                )

                indexed += len(batch)
                progress.update(task, advance=len(batch))

        self.console.print(f"[green]Indexed {indexed} games[/green]")
        return indexed

    def search_similar_games(
        self,
        query: str,
        n_results: int = 5,
        mechanism_filter: Optional[list[str]] = None,
        complexity_filter: Optional[str] = None,
        player_count: Optional[int] = None,
        min_rating: Optional[float] = None,
    ) -> list[dict]:
        """Search for similar games.

        Args:
            query: Search query text
            n_results: Number of results to return
            mechanism_filter: List of mechanism values to filter by (any match)
            complexity_filter: Complexity level to filter by
            player_count: Player count that must be within game's range
            min_rating: Minimum rating filter

        Returns:
            List of result dicts with id, document, metadata, distance
        """
        # Build where filter
        where_filter = None
        filters = []

        if complexity_filter:
            filters.append({"complexity": {"$eq": complexity_filter}})

        if min_rating is not None:
            filters.append({"rating": {"$gte": min_rating}})

        if player_count is not None:
            filters.append({"min_players": {"$lte": player_count}})
            filters.append({"max_players": {"$gte": player_count}})

        if len(filters) == 1:
            where_filter = filters[0]
        elif len(filters) > 1:
            where_filter = {"$and": filters}

        # Query ChromaDB
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter,
        )

        # Format results
        formatted = []
        if results and results["ids"] and results["ids"][0]:
            for i, id_ in enumerate(results["ids"][0]):
                result = {
                    "id": id_,
                    "document": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                }

                # If mechanism filter specified, check if game has any matching mechanism
                if mechanism_filter:
                    game_mechs = result["metadata"].get("mechanisms", "").split(",")
                    if not any(mf in game_mechs for mf in mechanism_filter):
                        continue

                formatted.append(result)

        return formatted[:n_results]

    def get_collection_stats(self) -> dict:
        """Get statistics about the collection.

        Returns:
            Dict with count and other stats
        """
        count = self.collection.count()
        return {
            "count": count,
            "collection_name": self.COLLECTION_NAME,
            "persist_directory": str(self.persist_directory),
        }

    def clear_collection(self) -> None:
        """Clear all data from the collection."""
        self.client.delete_collection(self.COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        self.console.print("[yellow]Collection cleared[/yellow]")
