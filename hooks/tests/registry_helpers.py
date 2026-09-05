#!/usr/bin/env python3
"""Throwaway agent-deck registry for tests.

Delegates to preclose_lib.fixture_registry so the schema has exactly one owner -
the module that reads it. Tests import production, never the reverse.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import preclose_lib as lib  # noqa: E402

INSTANCES_DDL = lib.INSTANCES_DDL


def temp_registry(rows, directory):
    return lib.fixture_registry(rows, directory)
