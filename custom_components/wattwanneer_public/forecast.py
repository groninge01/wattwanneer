"""Feed validation and local-hour selection, independent of Home Assistant."""

import math
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

AMSTERDAM = ZoneInfo("Europe/Amsterdam")


def parse_forecast(payload):
    """Validate the complete feed without changing its price values."""
    if not isinstance(payload, list) or not payload:
        raise ValueError("Expected a non-empty forecast array")
    rows = []
    seen = set()
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Forecast entries must be objects")
        stamp = item.get("datetime")
        if not isinstance(stamp, str):
            raise ValueError("Missing datetime")
        parsed = datetime.strptime(stamp, "%Y-%m-%d %H:%M")
        if parsed.strftime("%Y-%m-%d %H:%M") != stamp or parsed.minute:
            raise ValueError("Expected local hourly timestamps")
        price = item.get("price_eur_kwh")
        if (
            isinstance(price, bool)
            or not isinstance(price, (int, float))
            or not math.isfinite(price)
        ):
            raise ValueError("Invalid price_eur_kwh")
        if stamp in seen:
            raise ValueError("Duplicate local timestamp")
        seen.add(stamp)
        rows.append(dict(item))
    return sorted(rows, key=lambda row: row["datetime"])


def local_hour(now, offset=0):
    """Match the feed's local clock labels, including CET/CEST automatically."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")

    return (
        (now.astimezone(UTC) + timedelta(hours=offset))
        .astimezone(AMSTERDAM)
        .strftime("%Y-%m-%d %H:00")
    )


def select_hour(rows, now, offset=0):
    key = local_hour(now, offset)
    return next((row for row in rows if row["datetime"] == key), None)


def daily_rows(rows, now, days=0):
    date = (now.astimezone(AMSTERDAM).date() + timedelta(days=days)).isoformat()
    return [row for row in rows if row["datetime"].startswith(date + " ")]
