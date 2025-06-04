import json
from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict

SCHEDULE_DAYS = [1, 3, 7, 14, 30]


def load_flashcards(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Flashcards not found: {path}")
    return json.loads(path.read_text())


def build_queue(cards: List[Dict[str, str]], start: date) -> List[Dict[str, str]]:
    queue: List[Dict[str, str]] = []
    for card in cards:
        for days in SCHEDULE_DAYS:
            due = start + timedelta(days=days)
            queue.append({
                "question": card.get("question", ""),
                "answer": card.get("answer", ""),
                "due_date": due.isoformat(),
            })
    return queue


def write_queue(queue: List[Dict[str, str]], path: Path) -> None:
    path.write_text(json.dumps(queue, indent=2), encoding="utf-8")


def read_queue(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    return json.loads(path.read_text())


def due_today(queue: List[Dict[str, str]], today: date) -> List[Dict[str, str]]:
    iso = today.isoformat()
    return [item for item in queue if item.get("due_date") == iso]


def get_due_flashcards() -> List[Dict[str, str]]:
    """Return flashcards due today from the default queue file."""
    queue_path = Path("spaced_review_queue.json")
    queue = read_queue(queue_path)
    return due_today(queue, date.today())


def main() -> None:
    flashcards_path = Path("flashcards.json")
    queue_path = Path("spaced_review_queue.json")

    today = date.today()

    if queue_path.exists():
        queue = read_queue(queue_path)
    else:
        cards = load_flashcards(flashcards_path)
        queue = build_queue(cards, today)
        write_queue(queue, queue_path)

    today_cards = due_today(queue, today)

    if today_cards:
        print("Cards due today:")
        for i, card in enumerate(today_cards, start=1):
            print(f"{i}. {card['question']}")
    else:
        print("No cards due today.")


if __name__ == "__main__":
    main()
