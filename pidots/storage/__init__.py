"""
Módulo de persistência e banco de dados SQLite WAL do piDots.
"""
from .db import get_db, init_edge_database
from .spaces_manager import SpacesManager
from .vector_store import VectorStore
from .memory_manager import MemoryManager
from .shared_space import SharedSpaceManager
from .maintenance import EdgeMaintenanceManager

__all__ = ["get_db", "init_edge_database", "SpacesManager", "VectorStore", "MemoryManager", "SharedSpaceManager", "EdgeMaintenanceManager"]


