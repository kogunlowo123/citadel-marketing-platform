"""
Email sending warmup schedule.
Gradually increases daily send volume over 4 weeks to build sender reputation.

Usage: python scripts/warmup.py
"""
import json
import sys
from datetime import datetime, timedelta

WARMUP_SCHEDULE = [
    (1, 3, 50),
    (4, 7, 100),
    (8, 14, 250),
    (15, 21, 500),
    (22, 28, 1000),
    (29, 999, 5000),
]


def get_daily_limit(warmup_day: int) -> int:
    for start, end, limit in WARMUP_SCHEDULE:
        if start <= warmup_day <= end:
            return limit
    return 5000


def main():
    warmup_start = datetime(2026, 7, 3)  # Update to your actual start date
    today = datetime.now()
    day_number = max(1, (today - warmup_start).days + 1)
    daily_limit = get_daily_limit(day_number)

    print(f"Warmup Day: {day_number}")
    print(f"Daily Send Limit: {daily_limit}")
    print(f"Started: {warmup_start.strftime('%Y-%m-%d')}")
    print()

    print("Full Schedule:")
    for start, end, limit in WARMUP_SCHEDULE:
        marker = " <-- current" if start <= day_number <= end else ""
        end_label = f"{end}" if end < 999 else "+"
        print(f"  Days {start:>2}-{end_label:>3}: {limit:>5} emails/day{marker}")


if __name__ == "__main__":
    main()
