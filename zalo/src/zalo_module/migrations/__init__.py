"""Migration registry consumed by ``database.run_migrations``.

Each migration module exposes ``version: int`` and ``upgrade(engine_or_conn)``.
Add new modules here; ``MIGRATIONS`` stays sorted by ``version``.
"""
from __future__ import annotations

from zalo_module.migrations import m0001_initial, m0002_engine

_MODULES = [m0001_initial, m0002_engine]

MIGRATIONS = sorted(_MODULES, key=lambda m: m.version)
