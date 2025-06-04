from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Optional


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def list_videos() -> List[Dict[str, Optional[str]]]:
    """Return metadata for each mp4 file found in the data directory."""
    videos: List[Dict[str, Optional[str]]] = []
    for file in DATA_DIR.glob("*.mp4"):
        transcript = DATA_DIR / f"{file.stem}_transcript.txt"
        chunks = DATA_DIR / f"{file.stem}_chunks.json"
        if chunks.exists():
            try:
                chunk_data = json.loads(chunks.read_text())
                duration = chunk_data[-1].get("end", 0) if chunk_data else 0
            except json.JSONDecodeError:
                duration = 0
        else:
            duration = 0
        videos.append(
            {
                "filename": file.name,
                "path": str(file),
                "transcript": str(transcript) if transcript.exists() else None,
                "chunks": str(chunks) if chunks.exists() else None,
                "duration": duration,
            }
        )
    return videos


def get_video_metadata(filename: str) -> Dict[str, Optional[str]]:
    """Return metadata for a single video."""
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(filename)
    transcript = DATA_DIR / f"{path.stem}_transcript.txt"
    chunks = DATA_DIR / f"{path.stem}_chunks.json"
    chunk_data = []
    if chunks.exists():
        try:
            chunk_data = json.loads(chunks.read_text())
        except json.JSONDecodeError:
            chunk_data = []
    return {
        "filename": filename,
        "path": str(path),
        "transcript": transcript.read_text() if transcript.exists() else "",
        "chunks": chunk_data,
    }
