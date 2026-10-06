"""SQLite storage: topics, question bank (draft/approved/rejected) and practice attempts."""
import hashlib
import hmac
import json
import secrets
import sqlite3
import time
from contextlib import contextmanager

from src import config as C

SCHEMA = """
CREATE TABLE IF NOT EXISTS topics(name TEXT PRIMARY KEY, subject TEXT, prereq TEXT, pos INTEGER);
CREATE TABLE IF NOT EXISTS questions(qid TEXT PRIMARY KEY, topic TEXT, subtopic TEXT, difficulty TEXT, qtype TEXT,
  question TEXT, options TEXT, correct_answer TEXT, misconceptions TEXT, accepted TEXT, keywords TEXT,
  hint TEXT, solution TEXT, status TEXT, source TEXT, created REAL);
CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, topic TEXT, qid TEXT,
  answer TEXT, correct INTEGER, level INTEGER, ts REAL);
CREATE TABLE IF NOT EXISTS students(id TEXT PRIMARY KEY, name TEXT, code TEXT);
CREATE TABLE IF NOT EXISTS responses(student_id TEXT, qid TEXT, answer TEXT, ts REAL, PRIMARY KEY(student_id, qid));
CREATE TABLE IF NOT EXISTS accounts(username TEXT PRIMARY KEY, student_id TEXT UNIQUE, salt TEXT, pw_hash TEXT);
CREATE TABLE IF NOT EXISTS steps(student_id TEXT, topic TEXT, step TEXT, done INTEGER, PRIMARY KEY(student_id, topic, step));
"""
FIELDS = ["topic", "subtopic", "difficulty", "qtype", "question", "options", "correct_answer",
          "misconceptions", "accepted", "keywords", "hint", "solution"]
JSON_FIELDS = {"options": [], "misconceptions": {}, "accepted": [], "keywords": []}
WEIGHT = {"easy": 1, "medium": 2, "hard": 3}



@contextmanager
def db():
    con = sqlite3.connect(C.DB_FILE)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    try:
        yield con
        con.commit()
    finally:
        con.close()


def _row(r):
    d = dict(r)
    for f, empty in JSON_FIELDS.items():
        d[f] = json.loads(d[f]) if d.get(f) else empty
    return d


# ---- topics
def add_topic(name, subject="General", prereq=None):
    with db() as con:
        pos = con.execute("SELECT COUNT(*) FROM topics").fetchone()[0]
        con.execute("INSERT OR REPLACE INTO topics VALUES(?,?,?,?)", (name.strip(), subject.strip(), prereq or None, pos))


def delete_topic(name):
    with db() as con:
        con.execute("DELETE FROM topics WHERE name=?", (name,))


def list_topics():
    with db() as con:
        return [dict(r) for r in con.execute("SELECT * FROM topics ORDER BY pos")]


# ---- questions
def add_question(d, status="approved", source="teacher"):
    with db() as con:
        n = con.execute("SELECT COUNT(*) FROM questions").fetchone()[0] + 1
        while con.execute("SELECT 1 FROM questions WHERE qid=?", (f"B{n:03d}",)).fetchone():
            n += 1
        qid = f"B{n:03d}"
        vals = [json.dumps(d.get(f, JSON_FIELDS[f])) if f in JSON_FIELDS else d.get(f, "") for f in FIELDS]
        con.execute("INSERT INTO questions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (qid, *vals, status, source, time.time()))
    return qid


def update_question(qid, d):
    sets = [f for f in FIELDS if f in d]
    vals = [json.dumps(d[f]) if f in JSON_FIELDS else d[f] for f in sets]
    with db() as con:
        con.execute(f"UPDATE questions SET {', '.join(f + '=?' for f in sets)} WHERE qid=?", (*vals, qid))


def set_status(qid, status):
    with db() as con:
        con.execute("UPDATE questions SET status=? WHERE qid=?", (status, qid))


def delete_question(qid):
    with db() as con:
        con.execute("DELETE FROM questions WHERE qid=?", (qid,))


def list_questions(status=None, topic=None):
    q, args = "SELECT * FROM questions WHERE 1=1", []
    if status:
        q, args = q + " AND status=?", args + [status]
    if topic:
        q, args = q + " AND topic=?", args + [topic]
    with db() as con:
        return [_row(r) for r in con.execute(q + " ORDER BY created", args)]


def to_question(d):
    """Convert a bank row into the dict shape the analyzer and diagnosis expect."""
    mcq = d["qtype"] == "mcq"
    stem = d["question"]
    text = stem + ("   " + "   ".join(f"{chr(65 + i)}) {o}" for i, o in enumerate(d["options"])) if mcq else "")
    return {"qid": d["qid"], "question": text, "stem": stem, "options": d["options"],
            "correct_answer": d["correct_answer"], "topic": d["topic"], "subtopic": d["subtopic"] or "General",
            "difficulty": d["difficulty"], "type": "mcq" if mcq else "short_answer", "marks": WEIGHT.get(d["difficulty"], 2),
            "prerequisites": [], "distractor_misconceptions": d["misconceptions"], "accepted": d["accepted"],
            "keywords": d["keywords"], "hint": d["hint"], "solution": d["solution"]}


def approved_as_questions():
    return {q["qid"]: to_question(q) for q in list_questions("approved")}


def bank_topics():
    return sorted({q["topic"] for q in list_questions("approved")})


def content_version():
    with db() as con:
        r = con.execute("SELECT COUNT(*), COALESCE(MAX(created),0), COALESCE(SUM(LENGTH(question)+LENGTH(correct_answer)),0) "
                        "FROM questions WHERE status='approved'").fetchone()
        t = con.execute("SELECT COUNT(*) FROM topics").fetchone()[0]
    return (*tuple(r), t)


# ---- attempts
def save_attempt(student_id, topic, qid, answer, correct, level):
    with db() as con:
        con.execute("INSERT INTO attempts(student_id,topic,qid,answer,correct,level,ts) VALUES(?,?,?,?,?,?,?)",
                    (student_id, topic, qid, answer, int(correct), level, time.time()))


def attempt_stats(student_id, topic):
    with db() as con:
        n, c = con.execute("SELECT COUNT(*), COALESCE(SUM(correct),0) FROM attempts WHERE student_id=? AND topic=?",
                           (student_id, topic)).fetchone()
    return n, c


def attempt_totals(student_id):
    with db() as con:
        n, c = con.execute("SELECT COUNT(*), COALESCE(SUM(correct),0) FROM attempts WHERE student_id=?", (student_id,)).fetchone()
    return n, c


def attempt_history(student_id, topic):
    """Oldest to newest list of 1/0 for every practice answer on this topic."""
    with db() as con:
        return [r[0] for r in con.execute("SELECT correct FROM attempts WHERE student_id=? AND topic=? ORDER BY ts, id", (student_id, topic))]


def activity_summary():
    with db() as con:
        return [dict(r) for r in con.execute(
            "SELECT s.name AS name, COUNT(a.id) AS n, COALESCE(SUM(a.correct),0) AS c FROM students s "
            "LEFT JOIN attempts a ON a.student_id=s.id GROUP BY s.id ORDER BY s.name")]


# ---- students and assessment responses
def _code():
    return "".join(secrets.choice("23456789abcdefghjkmnpqrstuvwxyz") for _ in range(5))


def add_student(name, sid=None):
    with db() as con:
        if not sid:
            n = con.execute("SELECT COUNT(*) FROM students").fetchone()[0] + 1
            while con.execute("SELECT 1 FROM students WHERE id=?", (f"S{n}",)).fetchone():
                n += 1
            sid = f"S{n}"
        con.execute("INSERT OR IGNORE INTO students VALUES(?,?,?)", (sid, name.strip(), _code()))
    return sid


def list_students():
    with db() as con:
        return {r["id"]: {"name": r["name"], "code": r["code"]} for r in con.execute("SELECT * FROM students ORDER BY name")}


def student_by_code(code):
    code = (code or "").strip().lower()
    if not code:
        return None
    with db() as con:
        r = con.execute("SELECT id FROM students WHERE lower(code)=?", (code,)).fetchone()
    return r["id"] if r else None


def save_responses(rows):
    """rows: iterable of (student_id, qid, answer). Same student and question replaces the old answer."""
    rows, now = list(rows), time.time()
    with db() as con:
        for sid in {r[0] for r in rows}:
            con.execute("INSERT OR IGNORE INTO students VALUES(?,?,?)", (sid, sid, _code()))
        con.executemany("INSERT OR REPLACE INTO responses VALUES(?,?,?,?)", [(a, b, str(c), now) for a, b, c in rows])


def load_responses_df():
    import pandas as pd
    with db() as con:
        rows = con.execute("SELECT student_id, qid, answer FROM responses ORDER BY student_id, qid").fetchall()
    return pd.DataFrame([tuple(r) for r in rows], columns=["student_id", "qid", "answer"], dtype=str)


def responses_version():
    with db() as con:
        return tuple(con.execute("SELECT COUNT(*), COALESCE(MAX(ts),0) FROM responses").fetchone())


def seed_from_files():
    """First run only: copy students.json and responses.csv into the database."""
    from src.loader import load_students, load_responses
    with db() as con:
        no_students = con.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0
        no_resp = con.execute("SELECT COUNT(*) FROM responses").fetchone()[0] == 0
    if no_students:
        for sid, nm in load_students().items():
            add_student(nm, sid)
    if no_resp:
        df = load_responses()
        save_responses(zip(df["student_id"], df["qid"], df["answer"]))


# ---- learning-path ticks
def get_steps(student_id, topic):
    with db() as con:
        return {r["step"]: bool(r["done"]) for r in con.execute("SELECT step, done FROM steps WHERE student_id=? AND topic=?", (student_id, topic))}


def set_step(student_id, topic, step, done):
    with db() as con:
        con.execute("INSERT OR REPLACE INTO steps VALUES(?,?,?,?)", (student_id, topic, step, int(bool(done))))


# ---- student accounts (username + password)
def _hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 120_000).hex()


def create_account(username, password, name, code=None):
    """Return (student_id, error). A teacher code links the account to an existing student record."""
    u, sid = username.strip().lower(), None
    with db() as con:
        if con.execute("SELECT 1 FROM accounts WHERE username=?", (u,)).fetchone():
            return None, "That username is already taken."
        if code and code.strip():
            r = con.execute("SELECT id FROM students WHERE lower(code)=?", (code.strip().lower(),)).fetchone()
            if not r:
                return None, "That teacher code was not found. Leave it empty if you do not have one."
            if con.execute("SELECT 1 FROM accounts WHERE student_id=?", (r["id"],)).fetchone():
                return None, "That code already has an account. Please log in instead."
            sid = r["id"]
    if not sid:
        sid = add_student(name)
    salt = secrets.token_hex(16)
    with db() as con:
        con.execute("INSERT INTO accounts VALUES(?,?,?,?)", (u, sid, salt, _hash(password, salt)))
    return sid, None


def check_login(username, password):
    with db() as con:
        r = con.execute("SELECT student_id, salt, pw_hash FROM accounts WHERE username=?", (username.strip().lower(),)).fetchone()
    if r and hmac.compare_digest(_hash(password, r["salt"]), r["pw_hash"]):
        return r["student_id"]
    return None


def account_names():
    with db() as con:
        return {r["student_id"]: r["username"] for r in con.execute("SELECT student_id, username FROM accounts")}