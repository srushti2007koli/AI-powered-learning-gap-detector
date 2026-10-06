"""One interface for practice questions: math templates or teacher-approved bank questions."""
import random

from src import tracker
from src.analyzer import analyze
from src.generator import SUPPORTED, make_question, check as numeric_check

RANK = {"easy": 1, "medium": 2, "hard": 3}


def topics_available():
    return list(dict.fromkeys(SUPPORTED + tracker.bank_topics()))


def next_question(topic, level, focus=None, avoid=None):
    if topic in SUPPORTED:
        q = make_question(topic, level, focus, seed=random.randint(0, 10**6))
        return {"kind": "numeric", "prompt": q["prompt"], "hint": q["hint"], "solution": q["solution"], "_q": q, "qid": f"gen:{topic}"}
    pool = [q for q in tracker.approved_as_questions().values() if q["topic"] == topic]
    if not pool:
        return None
    gap = min(abs(RANK[q["difficulty"]] - level) for q in pool)
    best = [q for q in pool if abs(RANK[q["difficulty"]] - level) == gap]
    best = [q for q in best if q["qid"] != avoid] or best
    q = random.choice(best)
    return {"kind": "mcq" if q["type"] == "mcq" else "text", "prompt": q["stem"], "options": q["options"],
            "hint": q.get("hint") or "Read the question again and look for the key word.",
            "solution": q.get("solution", ""), "_q": q, "qid": q["qid"]}


def grade(nq, answer):
    """Return (verdict, message). Verdict is correct, partial or incorrect."""
    if nq["kind"] == "numeric":
        return ("correct" if numeric_check(nq["_q"], answer) else "incorrect"), ""
    res = analyze(nq["_q"], answer)
    return res["verdict"], res["evidence"]


def model_answer(nq):
    q = nq["_q"]
    if nq["kind"] == "mcq":
        i = ord(q["correct_answer"]) - 65
        return f'{q["correct_answer"]}) {q["options"][i]}' if 0 <= i < len(q["options"]) else q["correct_answer"]
    return "" if nq["kind"] == "numeric" else q["correct_answer"]
