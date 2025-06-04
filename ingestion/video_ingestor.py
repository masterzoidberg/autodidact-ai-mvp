from __future__ import annotations
import sys
import json
from pathlib import Path
import uuid


def transcribe(source: str) -> str:
    """Stub for WhisperX transcription."""
    print("transcription would happen here")
    return "This is a placeholder transcript."


def create_chunks(transcript: str) -> list[dict[str, float | str]]:
    """Return placeholder transcript chunks based on time."""
    return [{"start": 0.0, "end": 10.0, "text": transcript}]


def ingest_video(source: str, project: str | None = None) -> tuple[Path, Path]:
    base_dir = Path("data") / "projects"
    if project is None:
        project = uuid.uuid4().hex
    data_dir = base_dir / project
    data_dir.mkdir(parents=True, exist_ok=True)

    transcript_path = data_dir / "transcript.txt"
    chunks_path = data_dir / "transcript_chunks.json"

    transcript = transcribe(source)
    transcript_path.write_text(transcript)

    chunks = create_chunks(transcript)
    chunks_path.write_text(json.dumps(chunks, indent=2))

    return transcript_path, chunks_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest a video")
    parser.add_argument("source", help="Video file or URL")
    parser.add_argument("--project", help="Project ID", default=None)
    args = parser.parse_args()

    t_path, c_path = ingest_video(args.source, args.project)
    print(f"Wrote transcript to {t_path}")
    print(f"Wrote chunks to {c_path}")
