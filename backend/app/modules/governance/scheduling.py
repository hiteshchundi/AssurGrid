"""Calendar-month schedules preserve the original deadline when completed late."""
from calendar import monthrange
from datetime import date
import hashlib


def add_months(day: date, months: int) -> date:
    index = day.year * 12 + day.month - 1 + months
    year, month = divmod(index, 12)
    month += 1
    return date(year, month, min(day.day, monthrange(year, month)[1]))


def generation_key(application_id, rule_id, window_start: date) -> str:
    return hashlib.sha256(f"{application_id}/{rule_id}/{window_start}".encode()).hexdigest()


def obligation_status(due_date: date, due_soon_days: int, as_of: date, completed=False) -> str:
    if completed:
        return "Completed"
    remaining = (due_date - as_of).days
    if remaining < 0:
        return "Overdue"
    return "Due soon" if remaining <= due_soon_days else "Upcoming"
