"""Base abstractions for all screeners and jobs.

To add a new screener:
  1. Create  tradescreener/screeners/screenerN/__init__.py
  2. Define job classes (BaseJob subclasses) with their FieldDefs
  3. Define a BaseScreener subclass decorated with @register
  4. The screener will automatically appear in the UI.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Type


@dataclass
class FieldDef:
    """Describes one configurable parameter rendered in the Config Panel."""
    attr: str           # attribute name on the config dataclass
    label: str          # human-readable label shown in the UI
    kind: str           # "int" | "float" | "bool"
    default: Any        # default value
    min_val: Any = None # minimum value (int/float only)
    max_val: Any = None # maximum value (int/float only)
    decimals: int = 1   # decimal places (float only)
    tooltip: str = ""   # tooltip shown on hover


class BaseJob(ABC):
    """Abstract base class for a single screener job."""

    #: Short label shown as the section header and result tab name
    label: str = ""

    #: Export filename prefix (e.g. "Potential_Bullish_1")
    result_name: str = ""

    #: Config fields rendered in the Config Panel for this job
    fields: List[FieldDef] = []

    #: If True the worker passes the previous job's output as a watchlist filter
    needs_watchlist: bool = False

    @property
    @abstractmethod
    def config_class(self) -> Type:
        """Return the dataclass type used to configure this job."""
        ...

    def default_config(self):
        """Return a config instance populated with all field defaults."""
        return self.config_class()

    @abstractmethod
    def run(self, cfg, universe: set, watchlist: set | None = None) -> list:
        """Run the job and return a list of result-row dicts.

        Args:
            cfg:       Instance of ``config_class``.
            universe:  Set of ticker symbols in the scan universe.
            watchlist: Symbols from the previous job (only when needs_watchlist=True).
        """
        ...

    def conditions_summary(self, cfg) -> List[str]:
        """Return human-readable condition strings for the active config.

        Override in each job to populate the *Active Conditions* sidebar panel.
        """
        return []


class BaseScreener(ABC):
    """Abstract base class for a complete screener (one or more jobs)."""

    #: Unique integer ID — used as the settings key and watchlist filename prefix
    id: int = 0

    #: Full display label shown in the tab header
    label: str = ""

    #: Emoji prefix prepended to the tab title
    tab_icon: str = "📊"

    #: Set to False to hide this screener from the UI without removing it
    enabled: bool = True

    @property
    @abstractmethod
    def jobs(self) -> List[BaseJob]:
        """Ordered list of BaseJob instances for this screener."""
        ...
