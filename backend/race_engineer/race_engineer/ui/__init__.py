"""Pages Streamlit (1 fichier = 1 page)."""

from race_engineer.ui.dashboard import page_dashboard
from race_engineer.ui.live_timing import page_live_timing
from race_engineer.ui.our_bike import page_our_bike
from race_engineer.ui.pilots import page_pilots
from race_engineer.ui.competitors import page_competitors
from race_engineer.ui.comparison import page_comparison
from race_engineer.ui.strategy import page_strategy
from race_engineer.ui.history import page_history
from race_engineer.ui.settings import page_settings
from race_engineer.ui.simulator import page_simulator

__all__ = [
    "page_dashboard",
    "page_live_timing",
    "page_our_bike",
    "page_pilots",
    "page_competitors",
    "page_comparison",
    "page_strategy",
    "page_history",
    "page_settings",
    "page_simulator",
]
