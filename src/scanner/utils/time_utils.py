"""
Time utilities for market hours and session handling.
"""

from datetime import datetime, time
from zoneinfo import ZoneInfo

# US Eastern timezone
ET = ZoneInfo("America/New_York")

# Regular trading hours
MARKET_OPEN = time(9, 30)
MARKET_CLOSE = time(16, 0)

# Early session window for momentum detection
EARLY_SESSION_START = time(9, 30)
EARLY_SESSION_END = time(11, 0)


def is_market_open(dt: datetime | None = None) -> bool:
    """Check if market is currently open."""
    if dt is None:
        dt = datetime.now(ET)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=ET)
    else:
        dt = dt.astimezone(ET)

    # Check weekday (0=Monday, 6=Sunday)
    if dt.weekday() >= 5:
        return False

    current_time = dt.time()
    return MARKET_OPEN <= current_time < MARKET_CLOSE


def is_early_session(dt: datetime | None = None) -> bool:
    """Check if within early session window (09:30-11:00 ET)."""
    if dt is None:
        dt = datetime.now(ET)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=ET)
    else:
        dt = dt.astimezone(ET)

    current_time = dt.time()
    return EARLY_SESSION_START <= current_time < EARLY_SESSION_END


def get_session_elapsed_minutes(dt: datetime | None = None) -> int:
    """Get minutes elapsed since market open."""
    if dt is None:
        dt = datetime.now(ET)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=ET)
    else:
        dt = dt.astimezone(ET)

    market_open_dt = dt.replace(hour=9, minute=30, second=0, microsecond=0)

    if dt < market_open_dt:
        return 0

    delta = dt - market_open_dt
    return int(delta.total_seconds() / 60)
