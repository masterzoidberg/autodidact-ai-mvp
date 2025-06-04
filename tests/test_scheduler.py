from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from datetime import date

from learning import spaced_scheduler as ss


def test_build_queue_three_items():
    cards = [
        {"question": "q1", "answer": "a1"},
        {"question": "q2", "answer": "a2"},
        {"question": "q3", "answer": "a3"},
    ]
    start = date(2024, 1, 1)
    queue = ss.build_queue(cards, start)
    assert len(queue) == len(cards) * len(ss.SCHEDULE_DAYS)
    expected_dates = [start + ss.timedelta(days=d) for d in ss.SCHEDULE_DAYS]
    actual_dates = [date.fromisoformat(item["due_date"]) for item in queue[: len(ss.SCHEDULE_DAYS)]]
    assert actual_dates == expected_dates

    for days in ss.SCHEDULE_DAYS:
        due = start + ss.timedelta(days=days)
        day_cards = ss.due_today(queue, due)
        assert len(day_cards) == len(cards)
        assert all(date.fromisoformat(c["due_date"]) == due for c in day_cards)

