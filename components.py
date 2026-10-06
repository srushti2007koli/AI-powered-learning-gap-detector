from src import config as C

ERR = {"sign_error": "Sign error", "incomplete": "Incomplete answer", "procedural": "Procedural mistake",
       "conceptual": "Conceptual gap", "calculation": "Calculation slip", "careless": "Careless slip",
       "unclassified": "Unclassified (needs LLM)", "none": "None"}


# Student-friendly wording (teachers keep the technical labels in ERR)
ERR_S = {"sign_error": "Plus/minus slip", "incomplete": "Answer not complete", "procedural": "Method mistake",
         "conceptual": "Idea not clear yet", "calculation": "Calculation slip", "careless": "Careless slip",
         "unclassified": "Mistake not sorted yet", "none": "None"}
SEV_S = {"High": "Fix this first", "Medium": "Needs some practice", "Low": "Almost there", "None": "Looking good"}


def conf_word(c):
    return "High" if c >= 0.7 else ("Medium" if c >= 0.4 else "Low")


def overall_msg(o, n_gaps):
    """One honest sentence about the overall score, depending on the score and the gaps."""
    if n_gaps == 0:
        return "Strong work, no gaps found." if o >= C.MASTERED else "No big gaps, but there is room to grow."
    word = "topic is" if n_gaps == 1 else "topics are"
    if o >= C.MASTERED:
        return f"Looks good overall, but {n_gaps} {word} below the gap line."
    return f"{n_gaps} {word} pulling your score down."


def h(s):
    """Flatten HTML so markdown never treats indentation as a code block."""
    return "".join(line.strip() for line in s.strip().splitlines())


def tone(m):
    return "good" if m >= C.MASTERED else ("warn" if m >= C.GAP else "bad")


def pill(text, t="neutral"):
    return f'<span class="pill {t}">{text}</span>'


def sev_tone(s):
    return {"High": "bad", "Medium": "warn", "Low": "warn"}.get(s, "good")


def meter(pct, t="neutral"):
    return f'<div class="meter"><i style="width:{max(2, min(100, pct))}%;background:var(--{t})"></i></div>'


def hero(title, sub, chips=""):
    return h(f'<div class="hero"><div class="ht">{title}</div><div class="hs">{sub}</div><div class="hc">{chips}</div></div>')


def kpi(label, value, sub="", t=""):
    return h(f'<div class="card kpi"><div class="muted sm">{label}</div><div class="v {t}c">{value}</div><div class="muted sm">{sub}</div></div>')


def topic_card(t):
    tn = tone(t["mastery"])
    return (f'<div class="card"><div class="muted sm">{t["topic"]}</div>'
            f'<div class="kpi"><div class="v {tn}c">{t["mastery"]*100:.0f}%</div></div>{meter(t["mastery"]*100, tn)}'
            f'{pill(t["status"], tn)}</div>')


def topic_grid(topics):
    return h('<div class="grid">' + "".join(topic_card(t) for t in topics) + "</div>")


def chain(topics):
    parts = [f'<span class="chip {tone(t["mastery"])}">{t["topic"]} {t["mastery"]*100:.0f}%</span>' for t in topics]
    return h('<div class="chain">' + '<span class="arrow">›</span>'.join(parts) + "</div>")


def evidence_row(r, student=False):
    et = r["error_type"]
    t = "warn" if et in ("incomplete", "careless") else "bad"
    label = (ERR_S if student else ERR).get(et, et)
    return h(f'<div class="ev"><div class="q">{r["qid"]}</div><div class="t">{r["evidence"] or "Answer did not match."}</div>'
             f'<div>{pill(label, t)}{pill(r["difficulty"])}</div></div>')


def heat_table(names, topics, matrix):
    head = "<tr><th></th>" + "".join(f"<th>{t}</th>" for t in topics) + "</tr>"
    body = ""
    for n, row in zip(names, matrix):
        body += f'<tr><td class="n">{n}</td>' + "".join(
            '<td class="c neutral" title="No result yet">-</td>' if v is None else
            f'<td class="c {tone(v/100)}" title="{t}: {v:.0f}%">{v:.0f}%</td>' for t, v in zip(topics, row)) + "</tr>"
    return h(f'<div class="card"><table class="heat">{head}{body}</table></div>')