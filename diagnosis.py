"""Stage 3: mastery, severity, confidence, careless detection, gap report."""
from collections import Counter
from src import config as C
from src.analyzer import analyze
from src.graph import root_cause, downstream_impact


def score_student(student_df, questions, use_llm=False):
    rows = []
    for _, r in student_df.iterrows():
        q = questions.get(r["qid"])
        if q is None:
            continue
        a = analyze(q, r["answer"])
        if use_llm and a["error_type"] == "unclassified":
            from src.llm_client import classify
            out = classify(q, r["answer"])
            if out:
                a["error_type"], a["evidence"] = out["error_type"], f'{a["evidence"]}. {out["misconception"]}'
        rows.append({"qid": r["qid"], "topic": q["topic"], "subtopic": q["subtopic"],
                     "difficulty": q["difficulty"], "answer": r["answer"],
                     "weight": C.DIFFICULTY_WEIGHT[q["difficulty"]], **a})
    _flag_careless(rows)
    return rows


def _flag_careless(rows):
    """Wrong on an easy item but strong on medium/hard items of the same topic."""
    for t in {r["topic"] for r in rows}:
        tr = [r for r in rows if r["topic"] == t]
        hard = [r for r in tr if r["difficulty"] != "easy"]
        if not hard:
            continue
        hard_score = sum(C.SCORE[r["verdict"]] * r["weight"] for r in hard) / sum(r["weight"] for r in hard)
        for r in tr:
            if r["difficulty"] == "easy" and r["verdict"] == "incorrect" and hard_score >= 0.85:
                r["error_type"] = "careless"
                r["evidence"] += " (easy item missed while harder items in this topic were correct)"


def topic_mastery(rows):
    out = {}
    for t in {r["topic"] for r in rows}:
        tr = [r for r in rows if r["topic"] == t]
        m = sum(C.SCORE[r["verdict"]] * r["weight"] for r in tr) / sum(r["weight"] for r in tr)
        out[t] = m
    return out


def status(m):
    return "Mastered" if m >= C.MASTERED else ("Partial" if m >= C.GAP else "Gap")


def severity(m):
    s = 1 - m
    return "High" if s >= C.SEVERITY_HIGH else ("Medium" if m < C.GAP else ("Low" if m < C.MASTERED else "None"))


def confidence(topic_rows):
    """0..1: how sure we are. Combines sample size and consistency of error type."""
    n = len(topic_rows)
    bad = [r for r in topic_rows if r["verdict"] != "correct" and r["error_type"] != "careless"]
    if not bad:
        return 0.0
    top = Counter(r["error_type"] for r in bad).most_common(1)[0][1]
    return round(0.5 * min(n / 5, 1) + 0.5 * top / len(bad), 2)


def build_report(rows, graph):
    prereqs = graph["prerequisites"]
    mastery = topic_mastery(rows)
    topics = []
    for t in graph["order"]:
        if t not in mastery:
            continue
        tr = [r for r in rows if r["topic"] == t]
        errs = [r for r in tr if r["verdict"] != "correct"]
        types = Counter(r["error_type"] for r in errs if r["error_type"] != "careless")
        topics.append({
            "topic": t, "mastery": mastery[t], "status": status(mastery[t]),
            "severity": severity(mastery[t]), "confidence": confidence(tr),
            "dominant_error": types.most_common(1)[0][0] if types else "none",
            "evidence": errs, "root_cause": root_cause(t, mastery, prereqs),
            "affects": downstream_impact(t, mastery, prereqs),
        })
    gaps = sorted([x for x in topics if x["status"] == "Gap"], key=lambda x: x["mastery"])
    total = sum(r["weight"] * C.SCORE[r["verdict"]] for r in rows) / sum(r["weight"] for r in rows)
    return {"topics": topics, "primary": gaps[0] if gaps else None, "gaps": gaps,
            "overall": total, "rows": rows}


def recommend(item, graph):
    """Ordered learning path from computed facts."""
    steps = []
    if item["root_cause"] != item["topic"]:
        steps.append(f"Revise prerequisite first: {item['root_cause']}")
    fixes = {
        "sign_error": "Practice sign handling: reading roots from factors, using -b, and negative c in formulas",
        "incomplete": "Practice finding ALL solutions and checking the final answer is complete",
        "procedural": "Re-learn the step-by-step method with worked examples",
        "conceptual": "Review the core concept definition, then try guided examples",
        "unclassified": "Review the mistakes below with a worked solution",
    }
    steps.append(fixes.get(item["dominant_error"], "Review fundamentals"))
    n_easy = 5 if item["severity"] == "High" else 3
    steps.append(f"Complete {n_easy} beginner problems on {item['topic']}")
    steps.append("Attempt an adaptive assessment to confirm improvement")
    return steps
