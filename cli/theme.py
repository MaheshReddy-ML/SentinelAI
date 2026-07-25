"""Shared visual language for the SentinelAI command line."""

from rich.theme import Theme

THEME = Theme(
    {
        "brand": "bold #55d6be",
        "muted": "#8b9bb4",
        "success": "bold #55d6be",
        "warning": "bold #f6c453",
        "danger": "bold #ff7a90",
        "heading": "bold white",
        "dim": "dim #8b9bb4",
    }
)
