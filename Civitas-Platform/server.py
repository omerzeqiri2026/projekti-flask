from flask import Flask, jsonify, request, send_from_directory, session
from werkzeug.utils import secure_filename
import os
import sqlite3
import time
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent
DB = BASE / "civitas.db"
UPLOADS = BASE / "static" / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get("CIVITAS_SECRET_KEY") or "development-only-change-this-secret"

USERS = {
    "omerzeqiri": {"password": "23.09.2011", "name": "Omer Zeqiri", "majority": 48, "role": "Perfaqesues i shumices", "email": "omer.zeqiri@civitas.al", "phone": "+383 44 100 048", "address": "Prishtine, Kosove", "profession": "Menaxher publik", "position": "Kryesues"},
    "matinzeqiri": {"password": "11.06.2015", "name": "Matin Zeqiri", "majority": 29, "role": "Perfaqesues i grupit", "email": "matin.zeqiri@civitas.al", "phone": "+383 44 100 029", "address": "Prishtine, Kosove", "profession": "Koordinator", "position": "Anetar i grupit"},
    "nilzeqiri": {"password": "25.04.2018", "name": "Nil Zeqiri", "majority": 43, "role": "Perfaqesues i komunitetit", "email": "nil.zeqiri@civitas.al", "phone": "+383 44 100 043", "address": "Prishtine, Kosove", "profession": "Specialist i komunikimit", "position": "Anetar i komunitetit"},
}


def conn():
    db = sqlite3.connect(DB, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout=30000")
    db.execute("PRAGMA foreign_keys=ON")
    return db


def counts(db, poll_id):
    result = {"pro": 0, "kunder": 0, "abstenim": 0}
    rows = db.execute(
        "SELECT choice, COALESCE(SUM(weight), 0) AS total FROM votes WHERE poll_id=? GROUP BY choice",
        (poll_id,),
    )
    for row in rows:
        if row["choice"] in result:
            result[row["choice"]] = row["total"]
    return result


def active_poll(db):
    return db.execute("SELECT * FROM polls WHERE status='active' ORDER BY id DESC LIMIT 1").fetchone()


def shown_poll(db):
    return db.execute("SELECT * FROM polls ORDER BY id DESC LIMIT 1").fetchone()


def init_db():
    db = conn()
    try:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY, author TEXT, type TEXT, content TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY, sender TEXT, recipient TEXT, message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY, username TEXT, choice TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS polls (
                id INTEGER PRIMARY KEY, status TEXT NOT NULL, started_at TEXT NOT NULL,
                ended_at TEXT, pro_total INTEGER DEFAULT 0,
                kunder_total INTEGER DEFAULT 0, abstenim_total INTEGER DEFAULT 0
            );
        """)
        cols = {row["name"] for row in db.execute("PRAGMA table_info(votes)")}
        if "weight" not in cols:
            db.execute("ALTER TABLE votes ADD COLUMN weight INTEGER NOT NULL DEFAULT 1")
        if "poll_id" not in cols:
            db.execute("ALTER TABLE votes ADD COLUMN poll_id INTEGER NOT NULL DEFAULT 1")

        # Ensure the database permits one vote per user per poll, including older DBs.
        schema_row = db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='votes'").fetchone()
        schema = (schema_row["sql"] or "") if schema_row else ""
        if "username TEXT UNIQUE" in schema or "UNIQUE(username)" in schema.replace(" ", ""):
            db.execute("ALTER TABLE votes RENAME TO votes_old")
            db.execute("""CREATE TABLE votes (
                id INTEGER PRIMARY KEY, username TEXT, choice TEXT, created_at TEXT,
                weight INTEGER NOT NULL DEFAULT 1, poll_id INTEGER NOT NULL DEFAULT 1
            )""")
            db.execute("""INSERT INTO votes(id, username, choice, created_at, weight, poll_id)
                         SELECT id, username, choice, created_at, weight, poll_id FROM votes_old""")
            db.execute("DROP TABLE votes_old")
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_vote_per_poll ON votes(username, poll_id)")

        if not db.execute("SELECT 1 FROM polls LIMIT 1").fetchone():
            db.execute("INSERT INTO polls(status, started_at) VALUES('waiting', ?)", (datetime.now().isoformat(timespec="seconds"),))
        else:
            # Migrate the original auto-active empty round to waiting; preserve a round with votes.
            current = active_poll(db)
            if current and not db.execute("SELECT 1 FROM votes WHERE poll_id=? LIMIT 1", (current["id"],)).fetchone():
                db.execute("UPDATE polls SET status='waiting' WHERE id=?", (current["id"],))

        for username, profile in USERS.items():
            db.execute("UPDATE votes SET weight=? WHERE username=?", (profile["majority"], username))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@app.route("/")
def home():
    return send_from_directory("static", "index.html")


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", ""))
    user = USERS.get(username)
    if not user or user["password"] != data.get("password") or not str(data.get("id", "")).strip():
        return jsonify(error="Te dhenat e hyrjes nuk jane te sakta."), 401
    session.clear()
    session["username"] = username
    return jsonify(username=username, **user)


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


@app.get("/api/posts")
def posts():
    db = conn()
    try:
        return jsonify([dict(row) for row in db.execute("SELECT * FROM posts ORDER BY id DESC")])
    finally:
        db.close()


@app.post("/api/posts")
def post():
    data = request.get_json(silent=True) or {}
    content = str(data.get("content", "")).strip()
    if not content:
        return jsonify(error="Shkruani nje permbajtje."), 400
    db = conn()
    try:
        db.execute("INSERT INTO posts(author,type,content) VALUES(?,?,?)", (data.get("author", "Vizitor"), data.get("type", "text"), content))
        db.commit()
        return jsonify(ok=True), 201
    finally:
        db.close()


@app.post("/api/upload")
def upload():
    file = request.files.get("file")
    author = request.form.get("author", "Vizitor")
    if not file or not file.filename:
        return jsonify(error="Zgjidhni nje file."), 400
    filename = secure_filename(file.filename)
    if not filename:
        return jsonify(error="Emri i file-it nuk pranohet."), 400
    suffix = Path(filename).suffix.lower()
    target = UPLOADS / f"{Path(filename).stem}-{time.time_ns()}{suffix}"
    file.save(target)
    kind = "image" if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp"} else "video" if suffix in {".mp4", ".webm", ".ogg", ".mov"} else "file"
    db = conn()
    try:
        db.execute("INSERT INTO posts(author,type,content) VALUES(?,?,?)", (author, kind, f"/static/uploads/{target.name}"))
        db.commit()
        return jsonify(ok=True), 201
    finally:
        db.close()


@app.get("/api/complaints")
def complaints():
    username = request.args.get("user", "")
    db = conn()
    try:
        return jsonify([dict(row) for row in db.execute("SELECT * FROM complaints WHERE sender=? OR recipient=? ORDER BY id DESC", (username, username))])
    finally:
        db.close()


@app.post("/api/complaints")
def complaint():
    data = request.get_json(silent=True) or {}
    recipient = str(data.get("recipient", "")).strip()
    message = str(data.get("message", "")).strip()
    if not recipient or not message:
        return jsonify(error="Zgjidhni marresin dhe shkruani ankesen."), 400
    sender = session.get("username")
    if not sender:
        return jsonify(error="Duhet te hyni ne llogari."), 401
    db = conn()
    try:
        db.execute("INSERT INTO complaints(sender,recipient,message) VALUES(?,?,?)", (sender, recipient, message))
        db.commit()
        return jsonify(ok=True), 201
    finally:
        db.close()


@app.get("/api/votes")
def votes():
    db = conn()
    try:
        poll = shown_poll(db)
        if poll is None:
            return jsonify(status="waiting", poll_id=None, pro=0, kunder=0, abstenim=0, can_vote=False)
        totals = counts(db, poll["id"])
        return jsonify(poll_id=poll["id"], status=poll["status"], started_at=poll["started_at"], ended_at=poll["ended_at"], can_vote=(poll["status"] == "active"), **totals)
    finally:
        db.close()


@app.post("/api/votes/start")
def start_vote():
    data = request.get_json(silent=True) or {}
    if session.get("username") != "matinzeqiri" or data.get("username") != "matinzeqiri":
        return jsonify(error="Vetem Matin Zeqiri mund ta nise votimin."), 403
    db = conn()
    try:
        if active_poll(db):
            return jsonify(error="Votimi eshte tashme aktiv."), 409
        now = datetime.now().isoformat(timespec="seconds")
        cursor = db.execute("INSERT INTO polls(status, started_at) VALUES('active', ?)", (now,))
        db.commit()
        return jsonify(poll_id=cursor.lastrowid, status="active", started_at=now, message="Votimi filloi."), 201
    finally:
        db.close()


@app.post("/api/votes")
def vote():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    user = USERS.get(username)
    if data.get("choice") not in ("pro", "kunder", "abstenim"):
        return jsonify(error="Vote e pavlefshme."), 400
    if not user:
        return jsonify(error="Perdorues i panjohur."), 401
    if session.get("username") != username:
        return jsonify(error="Duhet te hyni ne llogarine tuaj per te votuar."), 401
    db = conn()
    try:
        poll = active_poll(db)
        if poll is None:
            return jsonify(error="Votimi nuk eshte aktiv ose ka perfunduar."), 409
        db.execute("INSERT INTO votes(username,choice,weight,poll_id,created_at) VALUES(?,?,?,?,?)", (username, data["choice"], user["majority"], poll["id"], datetime.now().isoformat(timespec="seconds")))
        db.commit()
        return jsonify(poll_id=poll["id"], status="active", **counts(db, poll["id"]))
    except sqlite3.IntegrityError:
        return jsonify(error="Ju tashme keni votuar ne kete raund."), 409
    finally:
        db.close()


@app.post("/api/votes/finish")
def finish_vote():
    data = request.get_json(silent=True) or {}
    if data.get("username") != "matinzeqiri" or session.get("username") != "matinzeqiri":
        return jsonify(error="Vetem Matin Zeqiri mund ta perfundoje votimin."), 403
    db = conn()
    try:
        poll = active_poll(db)
        if poll is None:
            return jsonify(error="Nuk ka votim aktiv per ta perfunduar."), 409
        totals = counts(db, poll["id"])
        ended_at = datetime.now().isoformat(timespec="seconds")
        db.execute("UPDATE polls SET status='finished', ended_at=?, pro_total=?, kunder_total=?, abstenim_total=? WHERE id=? AND status='active'", (ended_at, totals["pro"], totals["kunder"], totals["abstenim"], poll["id"]))
        if db.total_changes == 0:
            db.rollback()
            return jsonify(error="Votimi nuk eshte me aktiv."), 409
        db.commit()
        return jsonify(message="Votimi u perfundua dhe u ruajt ne histori.", status="finished", ended_at=ended_at, **totals)
    finally:
        db.close()


@app.get("/api/vote-history")
def vote_history():
    db = conn()
    try:
        rows = db.execute("SELECT id,started_at,ended_at,pro_total,kunder_total,abstenim_total FROM polls WHERE status='finished' ORDER BY id DESC")
        return jsonify([dict(row) for row in rows])
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=False)
