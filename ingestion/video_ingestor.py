from __future__ import annotations
import sys
import json
from pathlib import Path


def transcribe(source: str) -> str:
    """Stub for WhisperX transcription."""
    print("transcription would happen here")
    return "This is a placeholder transcript."


def create_chunks(transcript: str) -> list[dict[str, float | str]]:
    """Return placeholder transcript chunks based on time."""
    return [{"start": 0.0, "end": 10.0, "text": transcript}]


def ingest_video(source: str) -> tuple[Path, Path]:
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    transcript_path = data_dir / "transcript.txt"
    chunks_path = data_dir / "transcript_chunks.json"

    transcript = transcribe(source)
    transcript_path.write_text(transcript)

    chunks = create_chunks(transcript)
    chunks_path.write_text(json.dumps(chunks, indent=2))

    return transcript_path, chunks_path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python video_ingestor.py <video.mp4|YouTube URL>")
        sys.exit(1)

    t_path, c_path = ingest_video(sys.argv[1])
    print(f"Wrote transcript to {t_path}")
    print(f"Wrote chunks to {c_path}")
