import threading
from datetime import date
from pathlib import Path
import json
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
)
from werkzeug.utils import secure_filename

import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from learning import spaced_scheduler, flashcard_gen
from utils import focus_timer
from videos import video_manager
from ingestion import document_ingestor, video_ingestor
FLASHCARDS_PATH = BASE_DIR / "flashcards.json"
CURRICULUM_PATH = BASE_DIR / "curriculum" / "curriculum.json"
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
QUEUE_PATH = BASE_DIR / "spaced_review_queue.json"
FOCUS_LOG_PATH = BASE_DIR / "focus_log.json"
CLIPS_PATH = BASE_DIR / "video_clips.json"

app = Flask(__name__)
app.secret_key = "autodidact"  # simple session key

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/videos")
def video_library():
    videos = video_manager.list_videos()
    return render_template("video_library.html", videos=videos)


@app.route("/play")
def play_video():
    name = request.args.get("video")
    if not name:
        flash("No video specified")
        return redirect(url_for("video_library"))
    meta = video_manager.get_video_metadata(name)
    return render_template(
        "video_player.html", video=name, transcript=meta["transcript"], chunks=meta["chunks"]
    )


@app.route("/video/<path:filename>")
def video_file(filename: str):
    return send_from_directory(DATA_DIR, filename)

@app.route("/curriculum")
def curriculum():
    if not CURRICULUM_PATH.exists():
        return "Curriculum not found", 404
    data = json.loads(CURRICULUM_PATH.read_text())
    return render_template("curriculum.html", curriculum=data)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or file.filename == "":
        flash("No file selected")
        return redirect(url_for("index"))

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / secure_filename(file.filename)
    file.save(dest)

    paths = []
    ext = dest.suffix.lower()
    if ext in {".pdf", ".epub"}:
        output = document_ingestor.ingest_document(str(dest))
        app.logger.info(f"Document ingested to {output}")
        paths.append(str(output))
    elif ext == ".mp4":
        t_path, c_path = video_ingestor.ingest_video(str(dest))
        app.logger.info(f"Video processed: {t_path}, {c_path}")
        paths.extend([str(t_path), str(c_path)])
    else:
        flash("Unsupported file type")
        return redirect(url_for("index"))

    return render_template("upload_success.html", uploaded=str(dest), paths=paths)

@app.route("/flashcards")
def flashcards():
    queue = spaced_scheduler.read_queue(QUEUE_PATH)
    cards = spaced_scheduler.due_today(queue, date.today())
    return render_template("flashcards.html", cards=cards)


@app.route("/dashboard")
def dashboard():
    docs = list(DATA_DIR.glob("*.md"))
    videos = list(DATA_DIR.glob("*.mp4"))
    try:
        flashcards = json.loads(FLASHCARDS_PATH.read_text()) if FLASHCARDS_PATH.exists() else []
    except json.JSONDecodeError:
        flashcards = []
    try:
        focus_log = json.loads(FOCUS_LOG_PATH.read_text()) if FOCUS_LOG_PATH.exists() else []
    except json.JSONDecodeError:
        focus_log = []
    metrics = {
        "docs": len(docs),
        "videos": len(videos),
        "flashcards": len(flashcards),
        "focus_sessions": len(focus_log),
    }
    return render_template("dashboard.html", metrics=metrics)


@app.route("/generate_flashcards")
def generate_flashcards_route():
    video = request.args.get("video")
    if not video:
        return {"error": "Missing video"}, 400

    transcript_path = DATA_DIR / f"{video}.transcript.json"
    if not transcript_path.exists():
        return {"error": "Transcript not found"}, 404

    out_path = flashcard_gen.generate_flashcards_from_transcript(transcript_path)
    return {"flashcards": str(out_path)}

def _run_focus(minutes: int) -> None:
    focus_timer.countdown(minutes)
    focus_timer.log_session(minutes, FOCUS_LOG_PATH)

@app.route("/focus", methods=["POST"])
def focus():
    minutes = int(request.form.get("minutes", 25))
    threading.Thread(target=_run_focus, args=(minutes,), daemon=True).start()
    flash(f"Started a {minutes} minute focus session")
    return redirect(url_for("index"))


@app.route("/clip", methods=["POST"])
def save_clip():
    data = request.get_json(force=True, silent=True) or {}
    video = data.get("video")
    start = data.get("start")
    end = data.get("end")
    if not video or start is None or end is None:
        return {"error": "Missing parameters"}, 400
    if CLIPS_PATH.exists():
        try:
            clips = json.loads(CLIPS_PATH.read_text())
        except json.JSONDecodeError:
            clips = []
    else:
        clips = []
    clips.append({"video": video, "start": start, "end": end})
    CLIPS_PATH.write_text(json.dumps(clips, indent=2), encoding="utf-8")
    return {"status": "saved"}

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
