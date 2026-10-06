"""Stage 2: per-response verdict + error type using deterministic rules.
Answers the rules cannot classify are marked 'unclassified' (hook for the LLM)."""
import re
from fractions import Fraction

NUM = re.compile(r"-?\d+(?:\.\d+)?(?:/\d+)?")


def _norm(s):
    s = str(s).lower().replace(" ", "")
    return re.sub(r"[xy]=", "", s)


def _numset(s):
    """Return a set of numbers if the answer is purely numeric, else None."""
    t = _norm(s)
    if re.fullmatch(r"[-\d.,/]+", t) is None:
        return None
    return {Fraction(n) for n in NUM.findall(t)}


def _misconception_type(text):
    t = text.lower()
    if "sign" in t:
        return "sign_error"
    return "procedural"


def analyze(question, answer):
    """Return dict(verdict, error_type, evidence)."""
    correct, ans = question["correct_answer"], str(answer).strip()
    if question["type"] == "short_answer":
        return _analyze_text(question, ans)
    if question["type"] == "mcq":
        if ans.upper() == correct.upper():
            return _res("correct", "none", "")
        mis = question.get("distractor_misconceptions", {}).get(ans.upper(), "")
        return _res("incorrect", _misconception_type(mis), mis or f"chose {ans}")

    if _norm(ans) == _norm(correct):
        return _res("correct", "none", "")

    cs, ss = _numset(correct), _numset(ans)
    if cs is not None and ss is not None and ss:
        if ss < cs:
            return _res("partial", "incomplete", f"gave {_fmt(ss)}, missing {_fmt(cs - ss)}")
        if {-s for s in ss} == cs:
            return _res("incorrect", "sign_error", f"answered {ans}, expected {correct}: signs reversed")
        extra = ss - cs
        if ss & cs and extra and all(-e in cs for e in extra):
            return _res("partial", "sign_error", f"answered {ans}, expected {correct}: sign slip on one value")
        if ss & cs:
            return _res("partial", "incomplete", f"answered {ans}, only partly matches {correct}")
        return _res("incorrect", "unclassified", f"answered {ans}, expected {correct}")

    n_s, n_c = _norm(ans), _norm(correct)
    if n_s and n_c.startswith(n_s):
        return _res("partial", "incomplete", f"answered '{ans}', missing part of '{correct}'")
    return _res("incorrect", "unclassified", f"answered '{ans}', expected '{correct}'")


def _tnorm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s']", " ", str(s).lower())).strip()


def _analyze_text(q, ans):
    """Written answers: exact/accepted match, else key ideas (all = correct, some = partial)."""
    n = _tnorm(ans)
    if not n:
        return _res("incorrect", "incomplete", "no answer given")
    if any(n == _tnorm(t) for t in [q["correct_answer"], *q.get("accepted", [])] if str(t).strip()):
        return _res("correct", "none", "")
    kws = [k for k in q.get("keywords", []) if k.strip()]
    if kws:
        hit = [any(alt.strip().lower() in n for alt in k.split("|") if alt.strip()) for k in kws]
        if all(hit):
            return _res("correct", "none", "")
        if any(hit):
            return _res("partial", "incomplete", f"covered {sum(hit)} of {len(kws)} key ideas")
    return _res("incorrect", "unclassified", f"answered '{ans}', expected '{q['correct_answer']}'")


def _fmt(s):
    return ", ".join(str(x) for x in sorted(s))


def _res(v, e, ev):
    return {"verdict": v, "error_type": e, "evidence": ev}