from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest
from learning.flashcard_gen import generate_flashcards


def test_generate_flashcards_returns_five_cards():
    text = "Python is great. Testing is essential."
    cards = generate_flashcards(text)
    assert len(cards) == 5
    assert cards[0]["question"] == "What does the text say about: 'Python is great'?"
    assert cards[0]["answer"] == "Python is great"
    assert cards[1]["question"] == "What does the text say about: 'Testing is essential'?"
    assert cards[1]["answer"] == "Testing is essential"
    for i in range(2, 5):
        n = i + 1
        assert cards[i]["question"] == f"Example question {n}"
        assert cards[i]["answer"] == f"Example answer {n}"

