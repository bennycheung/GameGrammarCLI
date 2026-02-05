"""Retrieval-Augmented Generation for GameGrammar.

This module provides RAG capabilities for game generation, allowing the system
to ground new game designs in existing games from BoardGameGeek's top games.

Components:
    - BGGMechanismMapping: Maps BGG mechanisms to GameGrammar MechanismTypes
    - BGGCollector: Collects game data from the BGG XML API
    - GameRAGStorage: ChromaDB vector storage for game embeddings
    - OntologyRAGRetriever: Retrieves similar games for generation context
    - RAGSinglePassGenerator: DSPy module for RAG-enhanced generation
"""

from gamegrammar.rag.mapping import BGGMechanismMapping
from gamegrammar.rag.collector import BGGCollector, BGGGame
from gamegrammar.rag.storage import GameRAGStorage
from gamegrammar.rag.retriever import (
    OntologyRAGRetriever,
    RAGOntologySignature,
    RAGSinglePassGenerator,
)

__all__ = [
    "BGGMechanismMapping",
    "BGGCollector",
    "BGGGame",
    "GameRAGStorage",
    "OntologyRAGRetriever",
    "RAGOntologySignature",
    "RAGSinglePassGenerator",
]
