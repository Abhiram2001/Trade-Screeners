"""Screener registry — discovers and exposes all registered screeners.

Usage (defining a new screener)::

    from tradescreener.screeners import register
    from tradescreener.screeners.base import BaseScreener

    @register
    class MyScreener(BaseScreener):
        id       = 3
        label    = "My Custom Screener"
        tab_icon = "🔍"
        enabled  = True
        ...

The screener will automatically appear in the UI on the next launch.
"""

from __future__ import annotations

from typing import List, Type

from .base import BaseScreener

_REGISTRY: List[Type[BaseScreener]] = []


def register(cls: Type[BaseScreener]) -> Type[BaseScreener]:
    """Class decorator — adds *cls* to the screener registry."""
    _REGISTRY.append(cls)
    return cls


def get_enabled_screeners() -> List[BaseScreener]:
    """Return instantiated enabled screeners in registration order."""
    return [cls() for cls in _REGISTRY if cls.enabled]


# ── Auto-import all screener sub-packages so they self-register ───────────────
from . import screener1, screener2  # noqa: E402, F401
