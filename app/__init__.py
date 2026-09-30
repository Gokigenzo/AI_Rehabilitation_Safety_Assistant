"""
App package for AI_for_older PyQt5 Dashboard.
"""

from .dashboard import DashboardWindow
from .launcher import ModuleLauncher
from .router import DashboardRouter
from .state import AppState

__all__ = [
    "DashboardWindow",
    "ModuleLauncher",
    "DashboardRouter",
    "AppState",
]
