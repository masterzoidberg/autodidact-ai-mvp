import argparse
import json
from datetime import datetime
from pathlib import Path
import sys
import time

VALID_LENGTHS = {25, 50, 90}


def countdown(minutes: int) -> None:
    """Run a countdown timer for the given minutes."""
    total_seconds = minutes * 60
    try:
        while total_seconds:
            mins, secs = divmod(total_seconds, 60)
            timer = f"{mins:02d}:{secs:02d}"
            print(timer, end="\r", flush=True)
            time.sleep(1)
            total_seconds -= 1
    except KeyboardInterrupt:
        print("\nTimer cancelled.")
        sys.exit(1)
    print("Time's up!            ")


def log_session(minutes: int, log_path: Path) -> None:
    """Append a completed session entry to the log file."""
    log_entry = {
        "session_length": minutes,
        "completed_at": datetime.utcnow().isoformat() + "Z",
    }
    if log_path.exists():
        data = json.loads(log_path.read_text())
        if not isinstance(data, list):
            data = []
    else:
        data = []
    data.append(log_entry)
    log_path.write_text(json.dumps(data, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Focus timer")
    parser.add_argument(
        "minutes",
        type=int,
        help="Session length in minutes (25, 50, or 90)",
    )
    args = parser.parse_args()
    if args.minutes not in VALID_LENGTHS:
        print("Invalid session length. Choose from 25, 50, or 90 minutes.")
        sys.exit(1)

    countdown(args.minutes)

    log_path = Path(__file__).resolve().parents[1] / "focus_log.json"
    log_session(args.minutes, log_path)
    print(f"Session logged to {log_path}")


if __name__ == "__main__":
    main()
