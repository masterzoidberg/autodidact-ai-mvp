from pathlib import Path
from datetime import date
import os
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from learning import spaced_scheduler


def test_get_due_flashcards(tmp_path, monkeypatch):
    today = date.today()
    data = [
        {"question": "q1", "answer": "a1", "due_date": today.isoformat()},
        {"question": "q2", "answer": "a2", "due_date": "2099-01-01"},
    ]
    queue_path = tmp_path / "spaced_review_queue.json"
    queue_path.write_text(spaced_scheduler.json.dumps(data))

    monkeypatch.chdir(tmp_path)
    cards = spaced_scheduler.get_due_flashcards()
    assert len(cards) == 1
    assert cards[0]["question"] == "q1"

