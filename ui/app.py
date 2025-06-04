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

from learning import spaced_scheduler
from utils import focus_timer
from videos import video_manager
CURRICULUM_PATH = BASE_DIR / "curriculum" / "curriculum.json"
DATA_DIR = BASE_DIR / "data"
QUEUE_PATH = BASE_DIR / "spaced_review_queue.json"
FOCUS_LOG_PATH = BASE_DIR / "focus_log.json"

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
    DATA_DIR.mkdir(exist_ok=True)
    dest = DATA_DIR / secure_filename(file.filename)
    file.save(dest)
    flash(f"Uploaded to {dest}")
    return redirect(url_for("index"))

@app.route("/flashcards")
def flashcards():
    queue = spaced_scheduler.read_queue(QUEUE_PATH)
    cards = spaced_scheduler.due_today(queue, date.today())
    return render_template("flashcards.html", cards=cards)

def _run_focus(minutes: int) -> None:
    focus_timer.countdown(minutes)
    focus_timer.log_session(minutes, FOCUS_LOG_PATH)

@app.route("/focus", methods=["POST"])
def focus():
    minutes = int(request.form.get("minutes", 25))
    threading.Thread(target=_run_focus, args=(minutes,), daemon=True).start()
    flash(f"Started a {minutes} minute focus session")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
