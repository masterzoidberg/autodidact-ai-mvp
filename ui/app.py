import threading
from datetime import date, datetime
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
from utils import focus_timer, summary_writer
from videos import video_manager
from ingestion import document_ingestor, video_ingestor
FLASHCARDS_PATH = BASE_DIR / "flashcards.json"
CURRICULUM_PATH = BASE_DIR / "curriculum" / "curriculum.json"
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
QUEUE_PATH = BASE_DIR / "spaced_review_queue.json"
FOCUS_LOG_PATH = BASE_DIR / "focus_log.json"
CLIPS_PATH = BASE_DIR / "video_clips.json"
REVIEW_LOG_PATH = BASE_DIR / "review_log.json"

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
    project = request.form.get("project") or "default"
    if not file or file.filename == "":
        flash("No file selected")
        return redirect(url_for("index"))

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / secure_filename(file.filename)
    file.save(dest)

    paths = []
    summary = ""
    flashcard_count = 0

    ext = dest.suffix.lower()

    try:
        if ext in {".pdf", ".epub"}:
            output = document_ingestor.ingest_document(str(dest), project)
            app.logger.info(f"Document ingested to {output}")
            paths.append(str(output))

            text = Path(output).read_text(encoding="utf-8")
            summary = summary_writer.generate_summary(text)
            summary_path = Path(output).parent / "summary.json"
            summary_path.write_text(json.dumps({"summary": summary}, indent=2), encoding="utf-8")
            paths.append(str(summary_path))

            cards = flashcard_gen.generate_flashcards(text)
            flashcards_path = Path(output).parent / "flashcards.json"
            flashcards_path.write_text(json.dumps(cards, indent=2), encoding="utf-8")
            flashcard_count = len(cards)
            paths.append(str(flashcards_path))
        elif ext == ".mp4":
            t_path, c_path = video_ingestor.ingest_video(str(dest), project)
            app.logger.info(f"Video processed: {t_path}, {c_path}")
            paths.extend([str(t_path), str(c_path)])

            transcript_text = Path(t_path).read_text(encoding="utf-8")
            summary = summary_writer.generate_summary(transcript_text)
            summary_path = Path(t_path).parent / "summary.json"
            summary_path.write_text(json.dumps({"summary": summary}, indent=2), encoding="utf-8")
            paths.append(str(summary_path))

            flashcards_path = flashcard_gen.generate_flashcards_from_transcript(c_path, project)
            paths.append(str(flashcards_path))
            try:
                flashcard_count = len(json.loads(Path(flashcards_path).read_text()))
            except Exception:
                flashcard_count = 0
        else:
            flash("Unsupported file type")
            return redirect(url_for("index"))
    except Exception as e:
        app.logger.exception("Error processing upload")
        flash(str(e))
        return redirect(url_for("index"))

    return render_template(
        "upload_success.html",
        uploaded=str(dest),
        paths=paths,
        summary=summary,
        flashcard_count=flashcard_count,
    )

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

def _run_focus(minutes: int, session_type: str, project_id: str) -> None:
    start = datetime.utcnow()
    focus_timer.countdown(minutes)
    end = datetime.utcnow()
    focus_timer.log_session(start, end, session_type, project_id, FOCUS_LOG_PATH)


def _calculate_streak(log: list[dict]) -> int:
    streak = 0
    last_date = None
    for entry in reversed(log):
        try:
            start_date = datetime.fromisoformat(entry["start"].replace("Z", "")).date()
        except Exception:
            continue
        if last_date is None:
            streak = 1
            last_date = start_date
            continue
        diff = (last_date - start_date).days
        if diff == 0:
            continue
        if diff == 1:
            streak += 1
            last_date = start_date
        else:
            break
    return streak
    
@app.route("/focus", methods=["POST"])
def focus():
    minutes = int(request.form.get("minutes", 25))
    session_type = request.form.get("session_type", "read")
    project_id = request.form.get("project_id", "default")
    threading.Thread(
        target=_run_focus,
        args=(minutes, session_type, project_id),
        daemon=True,
    ).start()
    flash(
        f"Started a {minutes} minute {session_type} session for project {project_id}"
    )
    return redirect(url_for("index"))


@app.route("/session_summary", methods=["GET", "POST"])
def session_summary():
    if not FOCUS_LOG_PATH.exists():
        return "No sessions", 404
    try:
        log = json.loads(FOCUS_LOG_PATH.read_text())
        if not isinstance(log, list):
            log = []
    except json.JSONDecodeError:
        log = []
    if not log:
        return "No sessions", 404
    last = log[-1]
    streak = _calculate_streak(log)
    total_time = last.get("session_length")
    session_type = last.get("session_type", "")
    project_id = last.get("project_id", "default")

    if request.method == "POST":
        surprised = request.form.get("surprised", "")
        revisit = request.form.get("revisit", "")
        out_dir = DATA_DIR / "projects" / project_id
        out_dir.mkdir(parents=True, exist_ok=True)
        ref_path = out_dir / "reflections.json"
        if ref_path.exists():
            try:
                reflections = json.loads(ref_path.read_text())
                if not isinstance(reflections, list):
                    reflections = []
            except json.JSONDecodeError:
                reflections = []
        else:
            reflections = []
        reflections.append(
            {
                "start": last.get("start"),
                "end": last.get("end"),
                "surprised": surprised,
                "revisit": revisit,
            }
        )
        ref_path.write_text(json.dumps(reflections, indent=2), encoding="utf-8")
        flash("Reflection saved")
        return redirect(url_for("index"))

    return render_template(
        "session_summary.html",
        total_time=total_time,
        session_type=session_type,
        streak=streak,
        project_id=project_id,
    )


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


@app.route("/review", methods=["GET", "POST"])
def review():
    """Daily review interface showing flashcards due today."""
    cards = spaced_scheduler.get_due_flashcards()

    if request.method == "POST":
        question = request.form.get("question", "")
        result = request.form.get("result", "incorrect")
        correct = result == "correct"
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "question": question,
            "correct": correct,
        }
        if REVIEW_LOG_PATH.exists():
            try:
                log = json.loads(REVIEW_LOG_PATH.read_text())
            except json.JSONDecodeError:
                log = []
        else:
            log = []
        log.append(entry)
        REVIEW_LOG_PATH.write_text(json.dumps(log, indent=2), encoding="utf-8")
        flash("Result logged")
        return redirect(url_for("review"))

    return render_template("review.html", cards=cards)


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    """Simple flashcard quiz interface."""
    try:
        cards = json.loads(FLASHCARDS_PATH.read_text()) if FLASHCARDS_PATH.exists() else []
    except json.JSONDecodeError:
        cards = []

    index = int(request.form.get("index", request.args.get("index", 0)))
    if index < 0:
        index = 0

    question = cards[index]["question"] if index < len(cards) else None

    show_answer = False
    user_answer = ""
    correct_answer = ""
    next_index = index + 1 if (index + 1) < len(cards) else None

    if request.method == "POST":
        show_answer = True
        user_answer = request.form.get("answer", "")
        if question is not None:
            correct_answer = cards[index].get("answer", "")

    return render_template(
        "quiz.html",
        question=question,
        index=index,
        show_answer=show_answer,
        user_answer=user_answer,
        correct_answer=correct_answer,
        next_index=next_index,
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
