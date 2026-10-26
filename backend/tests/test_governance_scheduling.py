from datetime import date

import pytest

from app.modules.governance.scheduling import add_months, obligation_status


@pytest.mark.parametrize("day,months,expected", [
    (date(2024, 1, 31), 1, date(2024, 2, 29)),
    (date(2025, 1, 31), 1, date(2025, 2, 28)),
    (date(2024, 2, 29), 12, date(2025, 2, 28)),
    (date(2026, 10, 12), 12, date(2027, 10, 12)),
    (date(2026, 1, 12), -3, date(2025, 10, 12)),
])
def test_calendar_month_boundaries(day, months, expected):
    assert add_months(day, months) == expected


@pytest.mark.parametrize("day,completed,expected", [
    (date(2026, 9, 11), False, "Upcoming"),
    (date(2026, 9, 12), False, "Due soon"),
    (date(2026, 10, 12), False, "Due soon"),
    (date(2026, 10, 13), False, "Overdue"),
    (date(2026, 10, 13), True, "Completed"),
])
def test_status_boundaries(day, completed, expected):
    assert obligation_status(date(2026, 10, 12), 30, day, completed) == expected
