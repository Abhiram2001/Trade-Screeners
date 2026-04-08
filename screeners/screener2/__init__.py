"""Screener 2 — Weekly Bullish / Daily Pullback."""

from ..base import BaseScreener
from .. import register
from .job1 import Job1
from .job2 import Job2


@register
class Screener2(BaseScreener):
    id       = 2
    label    = "Screener 2 — Wkly Bullish / Daily Pullback"
    tab_icon = "📉"
    enabled  = True

    @property
    def jobs(self):
        return [Job1(), Job2()]
