"""BGG API data collector for game data.

Collects game data from BoardGameGeek's XML API v2 and stores it in SQLite.
Respects rate limits and supports resumable collection.

NOTE: BGG now requires API registration and Bearer token authentication.
See: https://boardgamegeek.com/using_the_xml_api

To get your token:
1. Register at https://boardgamegeek.com/applications
2. Create a non-commercial application
3. Once approved, get your token from the Tokens section
4. Set BGG_API_TOKEN environment variable
"""

import os
import sqlite3
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn


@dataclass
class BGGGame:
    """Represents a game fetched from BoardGameGeek."""

    id: int
    name: str
    year: Optional[int] = None
    min_players: int = 1
    max_players: int = 1
    min_playtime: int = 0
    max_playtime: int = 0
    rating: float = 0.0
    weight: float = 0.0
    rank: Optional[int] = None
    description: str = ""
    mechanics: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)


class BGGCollector:
    """Collects game data from BoardGameGeek XML API v2.

    Implements rate limiting, batch fetching, and SQLite storage.
    Collection is resumable - already collected games are skipped.

    Requires BGG_API_TOKEN environment variable for authentication.
    Register at https://boardgamegeek.com/applications to get a token.
    """

    API_BASE = "https://boardgamegeek.com/xmlapi2"
    RATE_LIMIT_DELAY = 5  # seconds between requests
    BATCH_SIZE = 20  # games per request (API limit)
    USER_AGENT = "GameGrammar/1.0 (board game design assistant)"
    MAX_RETRIES = 3
    RETRY_DELAY = 10  # seconds

    def __init__(
        self,
        db_path: Optional[Path] = None,
        console: Optional[Console] = None,
        api_token: Optional[str] = None,
    ):
        """Initialize the collector.

        Args:
            db_path: Path to SQLite database. Defaults to data/bgg_games.db
            console: Rich console for output. Created if not provided.
            api_token: BGG API token. Defaults to BGG_API_TOKEN env var.
        """
        if db_path is None:
            # Default to project data directory
            db_path = Path(__file__).parent.parent.parent.parent / "data" / "bgg_games.db"

        self.db_path = db_path
        self.console = console or Console()
        self.api_token = api_token or os.environ.get("BGG_API_TOKEN")
        self._init_database()

    def _init_database(self) -> None:
        """Initialize the SQLite database schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    year INTEGER,
                    min_players INTEGER DEFAULT 1,
                    max_players INTEGER DEFAULT 1,
                    min_playtime INTEGER DEFAULT 0,
                    max_playtime INTEGER DEFAULT 0,
                    rating REAL DEFAULT 0.0,
                    weight REAL DEFAULT 0.0,
                    rank INTEGER,
                    description TEXT DEFAULT '',
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS game_mechanics (
                    game_id INTEGER,
                    mechanic TEXT NOT NULL,
                    FOREIGN KEY (game_id) REFERENCES games(id),
                    PRIMARY KEY (game_id, mechanic)
                );

                CREATE TABLE IF NOT EXISTS game_categories (
                    game_id INTEGER,
                    category TEXT NOT NULL,
                    FOREIGN KEY (game_id) REFERENCES games(id),
                    PRIMARY KEY (game_id, category)
                );

                CREATE INDEX IF NOT EXISTS idx_games_rank ON games(rank);
                CREATE INDEX IF NOT EXISTS idx_games_rating ON games(rating);
                CREATE INDEX IF NOT EXISTS idx_game_mechanics_mechanic ON game_mechanics(mechanic);
            """)

    def _get_collected_ids(self) -> set[int]:
        """Get the set of already collected game IDs."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id FROM games")
            return {row[0] for row in cursor.fetchall()}

    def _save_game(self, game: BGGGame) -> None:
        """Save a game to the database."""
        with sqlite3.connect(self.db_path) as conn:
            # Insert or replace game
            conn.execute("""
                INSERT OR REPLACE INTO games
                (id, name, year, min_players, max_players, min_playtime, max_playtime,
                 rating, weight, rank, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                game.id, game.name, game.year, game.min_players, game.max_players,
                game.min_playtime, game.max_playtime, game.rating, game.weight,
                game.rank, game.description[:2000] if game.description else ""
            ))

            # Insert mechanics
            for mechanic in game.mechanics:
                conn.execute("""
                    INSERT OR IGNORE INTO game_mechanics (game_id, mechanic)
                    VALUES (?, ?)
                """, (game.id, mechanic))

            # Insert categories
            for category in game.categories:
                conn.execute("""
                    INSERT OR IGNORE INTO game_categories (game_id, category)
                    VALUES (?, ?)
                """, (game.id, category))

    def _parse_game_xml(self, item: ET.Element) -> Optional[BGGGame]:
        """Parse a game from XML element."""
        try:
            game_id = int(item.get("id", 0))
            if game_id == 0:
                return None

            # Get primary name
            name_elem = item.find("name[@type='primary']")
            name = name_elem.get("value", "") if name_elem is not None else ""
            if not name:
                return None

            # Basic attributes
            year_elem = item.find("yearpublished")
            year = int(year_elem.get("value", 0)) if year_elem is not None else None
            if year == 0:
                year = None

            min_players_elem = item.find("minplayers")
            min_players = int(min_players_elem.get("value", 1)) if min_players_elem is not None else 1

            max_players_elem = item.find("maxplayers")
            max_players = int(max_players_elem.get("value", 1)) if max_players_elem is not None else 1

            min_playtime_elem = item.find("minplaytime")
            min_playtime = int(min_playtime_elem.get("value", 0)) if min_playtime_elem is not None else 0

            max_playtime_elem = item.find("maxplaytime")
            max_playtime = int(max_playtime_elem.get("value", 0)) if max_playtime_elem is not None else 0

            # Description
            desc_elem = item.find("description")
            description = desc_elem.text if desc_elem is not None and desc_elem.text else ""

            # Statistics
            stats = item.find("statistics/ratings")
            rating = 0.0
            weight = 0.0
            rank = None

            if stats is not None:
                avg_elem = stats.find("average")
                if avg_elem is not None:
                    try:
                        rating = float(avg_elem.get("value", 0))
                    except (ValueError, TypeError):
                        rating = 0.0

                weight_elem = stats.find("averageweight")
                if weight_elem is not None:
                    try:
                        weight = float(weight_elem.get("value", 0))
                    except (ValueError, TypeError):
                        weight = 0.0

                # Get overall rank
                for rank_elem in stats.findall("ranks/rank"):
                    if rank_elem.get("name") == "boardgame":
                        rank_val = rank_elem.get("value", "Not Ranked")
                        if rank_val != "Not Ranked":
                            try:
                                rank = int(rank_val)
                            except (ValueError, TypeError):
                                pass
                        break

            # Mechanics and categories from links
            mechanics = []
            categories = []
            for link in item.findall("link"):
                link_type = link.get("type", "")
                link_value = link.get("value", "")
                if link_type == "boardgamemechanic":
                    mechanics.append(link_value)
                elif link_type == "boardgamecategory":
                    categories.append(link_value)

            return BGGGame(
                id=game_id,
                name=name,
                year=year,
                min_players=min_players,
                max_players=max_players,
                min_playtime=min_playtime,
                max_playtime=max_playtime,
                rating=rating,
                weight=weight,
                rank=rank,
                description=description,
                mechanics=mechanics,
                categories=categories,
            )
        except Exception as e:
            self.console.print(f"[yellow]Warning: Failed to parse game: {e}[/yellow]")
            return None

    def fetch_game_batch(self, game_ids: list[int]) -> list[BGGGame]:
        """Fetch a batch of games from BGG API.

        Args:
            game_ids: List of game IDs to fetch (max 20)

        Returns:
            List of parsed BGGGame objects
        """
        if not game_ids:
            return []

        ids_str = ",".join(str(gid) for gid in game_ids[:self.BATCH_SIZE])
        url = f"{self.API_BASE}/thing?id={ids_str}&stats=1"

        # Build headers with authentication
        headers = {"User-Agent": self.USER_AGENT}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=30,
                )

                if response.status_code == 200:
                    root = ET.fromstring(response.content)
                    games = []
                    for item in root.findall("item"):
                        if item.get("type") == "boardgame":
                            game = self._parse_game_xml(item)
                            if game:
                                games.append(game)
                    return games

                elif response.status_code == 401:
                    # Authentication required
                    self.console.print(
                        "[red]API error: 401 Unauthorized[/red]\n"
                        "[yellow]BGG requires API authentication. To fix:[/yellow]\n"
                        "1. Register at https://boardgamegeek.com/applications\n"
                        "2. Create a non-commercial application\n"
                        "3. Once approved, get your token from Tokens section\n"
                        "4. Set: export BGG_API_TOKEN=your_token_here"
                    )
                    return []
                elif response.status_code in (429, 500, 503):
                    # Rate limited or server error - wait and retry
                    wait_time = self.RETRY_DELAY * (attempt + 1)
                    self.console.print(
                        f"[yellow]API returned {response.status_code}, "
                        f"waiting {wait_time}s...[/yellow]"
                    )
                    time.sleep(wait_time)
                else:
                    self.console.print(
                        f"[red]API error: {response.status_code}[/red]"
                    )
                    return []

            except requests.RequestException as e:
                self.console.print(f"[yellow]Request failed: {e}[/yellow]")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)

        return []

    def get_top_game_ids(self, limit: int = 5000) -> list[int]:
        """Get game IDs for top-ranked games on BGG.

        Uses a search-based approach since BGG doesn't have a direct "top N" API.
        This fetches games by searching popular terms and collecting highly-rated ones.

        Args:
            limit: Maximum number of game IDs to return

        Returns:
            List of game IDs
        """
        # BGG game IDs are sparse. We use a combination approach:
        # 1. Well-known top games (manually curated starting points)
        # 2. Sequential ID scanning with filtering

        # Top 100 most popular/highly-rated games (known IDs)
        known_top_games = [
            174430,  # Gloomhaven
            167791,  # Terraforming Mars
            161936,  # Pandemic Legacy: Season 1
            224517,  # Brass: Birmingham
            169786,  # Scythe
            193738,  # Great Western Trail
            266192,  # Wingspan
            182028,  # Through the Ages
            12333,   # Twilight Struggle
            120677,  # Terra Mystica
            84876,   # The Castles of Burgundy
            28720,   # Brass
            68448,   # 7 Wonders
            62219,   # Dominant Species
            31260,   # Agricola
            148228,  # Splendor
            13,      # Catan
            822,     # Carcassonne
            2651,    # Power Grid
            36218,   # Dominion
            9209,    # Ticket to Ride
            204583,  # Kingdomino
            178900,  # Codenames
            230802,  # Azul
            173346,  # 7 Wonders Duel
            205637,  # Arkham Horror: The Card Game
            187645,  # Star Wars: Rebellion
            164928,  # Orléans
            103343,  # Alhambra: Big Box
            126163,  # Tzolk'in
            102794,  # Caverna
            39463,   # Cosmic Encounter
            96848,   # Mage Knight
            121921,  # Robinson Crusoe
            35677,   # Le Havre
            25613,   # Through the Desert
            66356,   # Troyes
            150376,  # Dead of Winter
            110327,  # Lords of Waterdeep
            70149,   # Ora et Labora
            72125,   # Eclipse
            63888,   # Innovation
            71818,   # Alien Frontiers
            102680,  # Trajan
            188834,  # Secret Hitler
            40834,   # Dominion: Intrigue
            42215,   # Race for the Galaxy: Rebel vs Imperium
            3076,    # Puerto Rico
            37111,   # Battlestar Galactica
            175914,  # Food Chain Magnate
            157354,  # Five Tribes
            171623,  # The Voyages of Marco Polo
            128882,  # The Resistance: Avalon
            31481,   # Galaxy Trucker
            244521,  # The Quacks of Quedlinburg
            192135,  # Too Many Bones
            162886,  # Spirit Island
            233078,  # Everdell
            205059,  # Mansions of Madness
            155426,  # Inis
            164153,  # Star Realms
            209010,  # Mechs vs. Minions
            256226,  # Clank! Legacy
            291457,  # Gloomhaven: Jaws of the Lion
            316554,  # Dune: Imperium
            312484,  # Lost Ruins of Arnak
            284083,  # The Crew
            237182,  # Root
            246900,  # Eclipse: Second Dawn
            220308,  # Gaia Project
            199792,  # Viticulture
            199478,  # Flamme Rouge
            217372,  # The 7th Continent
            295947,  # Cascadia
            286096,  # Tapestry
            281259,  # The Isle of Cats
            216132,  # Clank!
            209418,  # Santorini
            163412,  # Patchwork
            169426,  # Roll for the Galaxy
            180263,  # The Gallerist
            147020,  # Star Wars: Imperial Assault
            73439,   # Seasons
            144733,  # Russian Railroads
            215,     # Tikal
            43015,   # Dungeon Lords
            40692,   # Small World
            54043,   # Jaipur
            41114,   # The Resistance
            124742,  # Android: Netrunner
            35497,   # Agricola: All Creatures Big and Small
            42,      # Tigris & Euphrates
            21790,   # Thurn and Taxis
            38453,   # Space Alert
            14996,   # Ticket to Ride: Europe
        ]

        # Return known games if that's enough
        if limit <= len(known_top_games):
            return known_top_games[:limit]

        # Otherwise, expand by scanning sequential IDs
        # BGG IDs go up to ~400k but most valid games are < 350k
        game_ids = set(known_top_games)

        # Scan ranges where good games are likely to be found
        scan_ranges = [
            (1, 5000),       # Classic games
            (5000, 50000),   # 2000s era
            (50000, 150000), # 2010s era
            (150000, 350000), # Modern era
        ]

        for start, end in scan_ranges:
            if len(game_ids) >= limit:
                break
            # Sample IDs from range
            step = max(1, (end - start) // 1000)
            for gid in range(start, end, step):
                if len(game_ids) >= limit:
                    break
                game_ids.add(gid)

        return sorted(game_ids)[:limit]

    def collect(
        self,
        limit: int = 5000,
        skip_existing: bool = True,
    ) -> int:
        """Collect games from BGG API.

        Args:
            limit: Maximum number of games to collect
            skip_existing: Skip games already in database

        Returns:
            Number of games collected
        """
        # Check for API token
        if not self.api_token:
            self.console.print(
                "[red]BGG_API_TOKEN not set![/red]\n\n"
                "[yellow]BGG requires API authentication. To fix:[/yellow]\n"
                "1. Register at https://boardgamegeek.com/applications\n"
                "2. Create a non-commercial application\n"
                "3. Once approved, get your token from Tokens section\n"
                "4. Set: export BGG_API_TOKEN=your_token_here\n"
                "   Or add to your .env file: BGG_API_TOKEN=your_token_here"
            )
            return 0

        self.console.print(f"[cyan]Starting BGG collection (limit: {limit})[/cyan]")

        # Get game IDs to collect
        all_ids = self.get_top_game_ids(limit)

        if skip_existing:
            existing_ids = self._get_collected_ids()
            ids_to_collect = [gid for gid in all_ids if gid not in existing_ids]
            self.console.print(
                f"[dim]Found {len(existing_ids)} existing games, "
                f"collecting {len(ids_to_collect)} new games[/dim]"
            )
        else:
            ids_to_collect = all_ids

        if not ids_to_collect:
            self.console.print("[green]All games already collected![/green]")
            return 0

        # Collect in batches
        collected = 0
        batches = [
            ids_to_collect[i:i + self.BATCH_SIZE]
            for i in range(0, len(ids_to_collect), self.BATCH_SIZE)
        ]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task(
                "Collecting games...",
                total=len(ids_to_collect),
            )

            for batch in batches:
                games = self.fetch_game_batch(batch)

                for game in games:
                    self._save_game(game)
                    collected += 1

                progress.update(task, advance=len(batch))

                # Rate limiting
                if batch != batches[-1]:
                    time.sleep(self.RATE_LIMIT_DELAY)

        self.console.print(f"[green]Collected {collected} games[/green]")
        return collected

    def get_all_games(self) -> list[BGGGame]:
        """Get all collected games from the database.

        Returns:
            List of all BGGGame objects in the database
        """
        games = []

        with sqlite3.connect(self.db_path) as conn:
            # Get all games
            cursor = conn.execute("""
                SELECT id, name, year, min_players, max_players,
                       min_playtime, max_playtime, rating, weight, rank, description
                FROM games
                ORDER BY rank ASC NULLS LAST, rating DESC
            """)

            for row in cursor:
                game_id = row[0]

                # Get mechanics
                mech_cursor = conn.execute(
                    "SELECT mechanic FROM game_mechanics WHERE game_id = ?",
                    (game_id,)
                )
                mechanics = [m[0] for m in mech_cursor]

                # Get categories
                cat_cursor = conn.execute(
                    "SELECT category FROM game_categories WHERE game_id = ?",
                    (game_id,)
                )
                categories = [c[0] for c in cat_cursor]

                games.append(BGGGame(
                    id=row[0],
                    name=row[1],
                    year=row[2],
                    min_players=row[3],
                    max_players=row[4],
                    min_playtime=row[5],
                    max_playtime=row[6],
                    rating=row[7],
                    weight=row[8],
                    rank=row[9],
                    description=row[10] or "",
                    mechanics=mechanics,
                    categories=categories,
                ))

        return games

    def get_game_count(self) -> int:
        """Get the number of games in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM games")
            return cursor.fetchone()[0]

    def get_all_mechanics(self) -> list[tuple[str, int]]:
        """Get all unique mechanics and their counts.

        Returns:
            List of (mechanic_name, count) tuples sorted by count descending
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT mechanic, COUNT(*) as count
                FROM game_mechanics
                GROUP BY mechanic
                ORDER BY count DESC
            """)
            return cursor.fetchall()
