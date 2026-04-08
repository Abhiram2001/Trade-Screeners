"""Screener 1 — Bullish Near Support."""

from ..base import BaseScreener
from .. import register
from .job1 import Job1
from .job2 import Job2


@register
class Screener1(BaseScreener):
    id       = 1
    label    = "Screener 1 — Bullish Near Support"
    tab_icon = "📈"
    enabled  = True

    @property
    def jobs(self):
        return [Job1(), Job2()]
