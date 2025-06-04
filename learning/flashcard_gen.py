import json
import re
from pathlib import Path
from typing import List, Dict



def generate_flashcards(text_chunk: str) -> List[Dict[str, str]]:
    """Stub to generate example flashcards from *text_chunk*.

    In a real application this would call an LLM to create question/answer
    pairs. This stub extracts up to five sentences from the input text and
    uses them to create simple flashcards.
    """
    # Break the text into sentences
    sentences = [s.strip() for s in re.split(r'[.!?]', text_chunk) if s.strip()]

    flashcards: List[Dict[str, str]] = []
    for i, sentence in enumerate(sentences[:5], start=1):
        question = f"What does the text say about: '{sentence[:40]}'?"
        flashcards.append({"question": question, "answer": sentence})

    # Pad with example cards if fewer than five sentences were found
    while len(flashcards) < 5:
        n = len(flashcards) + 1
        flashcards.append({"question": f"Example question {n}", "answer": f"Example answer {n}"})

    return flashcards


def generate_flashcards_from_transcript(transcript_file: str | Path, project: str = "default") -> Path:
    """Generate flashcards from a ``.transcript.json`` file and store them for a project."""

    path = Path(transcript_file)
    data = json.loads(path.read_text())

    if isinstance(data, dict):
        chunks = data.get("chunks", [])
    else:
        chunks = data

    cards: List[Dict[str, str]] = []
    for chunk in chunks:
        title = chunk.get("title", "")
        lines = chunk.get("lines", [])
        text = " ".join(lines)
        content = f"{title}. {text}" if title else text
        if content:
            cards.extend(generate_flashcards(content))

    out_dir = Path("data") / "projects" / project
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "flashcards.json"
    out_path.write_text(json.dumps(cards, indent=2), encoding="utf-8")
    return out_path


def main() -> None:
    """Generate flashcards from a text file."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate flashcards from a text file")
    parser.add_argument("input_file", help="Path to the text file")
    parser.add_argument(
        "--project",
        default="default",
        help="Project ID to save flashcards under",
    )
    args = parser.parse_args()

    text = Path(args.input_file).read_text(encoding="utf-8")
    cards = generate_flashcards(text)

    out_dir = Path("data") / "projects" / args.project
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "flashcards.json"
    out_path.write_text(json.dumps(cards, indent=2), encoding="utf-8")
    print(f"Wrote {len(cards)} flashcards to {out_path}")


if __name__ == "__main__":
    main()
