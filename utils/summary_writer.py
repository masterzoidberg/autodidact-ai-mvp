"""Simple summary generator stub."""

from pathlib import Path
import argparse
import json


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
    parser.add_argument(
        "--project",
        default="default",
        help="Project ID to save the summary under",
    )
    args = parser.parse_args()

    text = Path(args.input_file).read_text(encoding="utf-8")
    summary = generate_summary(text)

    out_dir = Path("data") / "projects" / args.project
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "summary.json"
    out_path.write_text(json.dumps({"summary": summary}, indent=2), encoding="utf-8")
    print(f"Wrote summary to {out_path}")


if __name__ == "__main__":
    main()
