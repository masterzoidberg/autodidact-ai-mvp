"""Simple summary generator stub."""

from pathlib import Path
import argparse


def generate_summary(paragraph: str) -> str:
    """Return a three-sentence summary for *paragraph*.

    This implementation is a stub and simply returns a placeholder summary.
    """
    return (
        "This is summary sentence one. "
        "This is summary sentence two. "
        "This is summary sentence three."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a summary from a text paragraph")
    parser.add_argument("input_file", help="Path to a text file containing a single paragraph")
    parser.add_argument("--output", default="summary.txt", help="File to write the summary to")
    args = parser.parse_args()

    text = Path(args.input_file).read_text(encoding="utf-8")
    summary = generate_summary(text)

    out_path = Path(args.output)
    out_path.write_text(summary, encoding="utf-8")
    print(f"Wrote summary to {out_path}")


if __name__ == "__main__":
    main()
