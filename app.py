import hmac
import io
import os
import re
from collections import Counter

import plotly.graph_objects as go
import streamlit as st

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv is optional here
    load_dotenv = None

from src import config as C
from src import tracker, practice, content_manager
from src.loader import load_questions, load_graph, load_responses
from src.diagnosis import score_student, build_report, recommend
from ui.theme import css, LIGHT, DARK
from ui import components as K
from ui import landing as L

if load_dotenv:
    load_dotenv(C.BASE_DIR / ".env")
st.set_page_config(page_title="Learning Gap Detector", page_icon="🎯", layout="wide")

tracker.seed_from_files()
GRAPH = load_graph()
NAMES = {sid: s["name"] for sid, s in tracker.list_students().items()}
name = lambda s: NAMES.get(s, s)

NAV = ["Overview", "Gap report", "Practice zone", "Assessment"]
LEVELS = {1: "Easy", 2: "Medium", 3: "Hard"}
EMPTY = {"topics": [], "primary": None, "gaps": [], "overall": 0.0, "rows": []}


def merged_graph():
    """Math graph from the JSON file plus any topics the teacher added in the database."""
    g = {"order": list(GRAPH["order"]), "prerequisites": {k: list(v) for k, v in GRAPH["prerequisites"].items()}}
    for t in tracker.list_topics():
        if t["name"] not in g["order"]:
            g["order"].append(t["name"])
        g["prerequisites"].setdefault(t["name"], [t["prereq"]] if t["prereq"] else [])
    return g


def stamp():
    """Changes whenever responses, approved questions or topics change, so cached reports refresh."""
    return (tracker.responses_version(), tracker.content_version(), tuple(t["name"] for t in tracker.list_topics()))


@st.cache_data(show_spinner=False)
def run_all(version, use_llm, mastered, gap):
    C.MASTERED, C.GAP = mastered / 100, gap / 100
    df = tracker.load_responses_df()
    questions = {**load_questions(), **tracker.approved_as_questions()}
    graph, out = merged_graph(), {}
    for s, g in df.groupby("student_id"):
        rows = score_student(g, questions, use_llm)
        if rows:
            out[s] = build_report(rows, graph)
    return out


# ---------------------------------------------------------------- before sign in
def goto(page):
    st.session_state["page"] = page


def logout():
    for k in ("auth_sid", "auth_teacher"):
        st.session_state.pop(k, None)
    st.session_state["page"] = "landing"


def landing_page():
    L.inject()
    brand, _, c1, c2 = st.columns([3, 2.4, 1, 1.1], vertical_alignment="center")
    brand.markdown(L.brand(), unsafe_allow_html=True)
    c1.button("Log in", key="nav_login", on_click=goto, args=("login",), use_container_width=True)
    c2.button("Sign up", key="nav_signup", type="primary", on_click=goto, args=("signup",), use_container_width=True)

    st.markdown(L.hero(), unsafe_allow_html=True)
    _, mid, _ = st.columns([1.2, 1, 1.2])
    mid.button("Close my gaps now", key="land_cta", type="primary", on_click=goto, args=("signup",), use_container_width=True)

    st.markdown(L.flow(), unsafe_allow_html=True)
    st.markdown(L.features([
        ("assess", "Assessments", "Short tests across your topics."),
        ("report", "Gap report", "Which topic is weak, and why."),
        ("practice", "Practice zone", "Questions matched to your level."),
        ("class", "Class heatmap", "Teachers see who needs help first."),
    ]), unsafe_allow_html=True)
    st.markdown(L.footer(), unsafe_allow_html=True)


def login_page():
    L.inject()
    back, _ = st.columns([1.2, 5])
    back.button("\u2190 Home", key="back_l", on_click=goto, args=("landing",))
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.markdown(L.side("Welcome back", "Log in to see where you stand and pick up your practice.",
                           ["See which topics are weak, and why", "Practise questions matched to your level",
                            "Teachers: your class heatmap is one login away"]), unsafe_allow_html=True)
    with right:
        tab_s, tab_t = st.tabs(["Student", "Teacher"])
        with tab_s:
            with st.form("login_s"):
                user = st.text_input("Username", placeholder="your username")
                pw = st.text_input("Password", type="password", placeholder="your password")
                sent = st.form_submit_button("Log in")
            if sent:
                sid = tracker.check_login(user, pw)
                if sid:
                    st.session_state["auth_sid"] = sid
                    st.session_state.pop("auth_teacher", None)
                    st.rerun()
                st.error("Wrong username or password.")
            st.button("New here? Create an account", key="to_signup", on_click=goto, args=("signup",))
        with tab_t:
            with st.form("login_t"):
                pw = st.text_input("Teacher password", type="password", placeholder="teacher password")
                sent = st.form_submit_button("Log in as teacher")
            if sent:
                if hmac.compare_digest(pw.encode(), os.getenv("TEACHER_PASSWORD", "teacher123").encode()):
                    st.session_state["auth_teacher"] = True
                    st.session_state.pop("auth_sid", None)
                    st.rerun()
                st.error("Wrong password.")


def signup_page():
    L.inject()
    back, _ = st.columns([1.2, 5])
    back.button("\u2190 Home", key="back_s", on_click=goto, args=("landing",))
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.markdown(L.side("Start closing your gaps", "Make an account in a minute. You are logged in straight away.",
                           ["Take a short assessment for your first report", "Get practice questions for your weakest topic",
                            "Got a teacher code? Link your existing results"]), unsafe_allow_html=True)
    with right:
        with st.form("signup"):
            full = st.text_input("Full name", placeholder="Asha Patil")
            user = st.text_input("Username", help="3 to 20 letters, numbers, dots or underscores")
            pw = st.text_input("Password", type="password", help="At least 6 characters")
            pw2 = st.text_input("Confirm password", type="password")
            code = st.text_input("Teacher code (optional)", help="If your teacher gave you a code, enter it to link your existing results.")
            sent = st.form_submit_button("Create account")
        if sent:
            u = user.strip().lower()
            if not full.strip():
                st.error("Please enter your name.")
            elif not re.fullmatch(r"[a-z0-9_.]{3,20}", u):
                st.error("Username must be 3 to 20 letters, numbers, dots or underscores.")
            elif len(pw) < 6:
                st.error("Password must be at least 6 characters.")
            elif pw != pw2:
                st.error("The two passwords do not match.")
            else:
                sid, err = tracker.create_account(u, pw, full, code)
                if err:
                    st.error(err)
                else:
                    st.session_state["auth_sid"] = sid
                    st.session_state.pop("auth_teacher", None)
                    st.session_state["welcome"] = f"Welcome, {full.strip()}! Take an assessment to get your first report."
                    st.rerun()
        st.button("Already have an account? Log in", key="to_login", on_click=goto, args=("login",))


signed_sid = st.session_state.get("auth_sid") if st.session_state.get("auth_sid") in NAMES else None
signed_teacher = bool(st.session_state.get("auth_teacher"))

with st.sidebar:
    st.markdown("### 🎯 Learning Gap Detector")
    dark = st.toggle("Dark mode", value=True, key="dark")
    mastered, gap, use_llm = 75, 45, False
    if signed_sid or signed_teacher:
        st.markdown("---")
        st.markdown("Signed in as **" + ("Teacher" if signed_teacher else name(signed_sid)) + "**")
        st.button("Log out", key="logout", on_click=logout)
    if signed_teacher:
        st.markdown("---")
        mastered = st.slider("Mastered from (%)", 50, 95, 75, 5)
        gap = min(st.slider("Gap below (%)", 20, 70, 45, 5), mastered - 5)
        st.caption("Move the sliders to see how the diagnosis changes.")
        use_llm = st.checkbox("Use LLM for unclassified errors", value=False)

st.markdown(f"<style>{css(dark)}</style>", unsafe_allow_html=True)
PAL = DARK if dark else LIGHT
reports = run_all(stamp(), use_llm, mastered, gap) if (signed_sid or signed_teacher) else {}
C.MASTERED, C.GAP = mastered / 100, gap / 100


# ---------------------------------------------------------------- charts
def style_fig(fig, height=330, legend=False):
    fig.update_layout(template="plotly_dark" if dark else "plotly_white", height=height,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color=PAL["text"]), margin=dict(t=30, b=20, l=10, r=10), showlegend=legend)
    fig.update_xaxes(color=PAL["text"], gridcolor=PAL["border"])
    fig.update_yaxes(color=PAL["text"], gridcolor=PAL["border"])
    return fig


def show(fig):
    # theme=None keeps our colours instead of Streamlit's, which made labels unreadable
    st.plotly_chart(fig, use_container_width=True, theme=None)


def bar_fig(topics, values):
    cols = [PAL[K.tone(v / 100)] for v in values]
    fig = go.Figure(go.Bar(x=topics, y=values, marker_color=cols, text=[f"{v:.0f}%" for v in values],
                           textposition="outside", hovertemplate="%{x}: %{y:.0f}%<extra></extra>"))
    fig.add_hline(y=mastered, line_dash="dot", line_color=PAL["good"], annotation_text="mastered")
    fig.add_hline(y=gap, line_dash="dot", line_color=PAL["bad"], annotation_text="gap")
    fig.update_yaxes(range=[0, 112], title="Mastery %")
    return style_fig(fig)


def compare_fig(sid, T):
    """Assessment mastery next to practice accuracy, per topic. None if the student has not practised."""
    names = [t["topic"] for t in T]
    stats = [tracker.attempt_stats(sid, n) for n in names]
    prac = [100 * c / n if n else None for n, c in stats]
    if not any(v is not None for v in prac):
        return None
    fig = go.Figure()
    fig.add_bar(name="Assessment", x=names, y=[t["mastery"] * 100 for t in T], marker_color=PAL["accent"])
    fig.add_bar(name="Practice", x=names, y=prac, marker_color=PAL["accent2"])
    fig.update_layout(barmode="group", legend=dict(orientation="h", y=1.15))
    fig.update_yaxes(range=[0, 112], title="Percent correct")
    return style_fig(fig, legend=True)


def trend_block(sid, topic, item):
    hist = tracker.attempt_history(sid, topic)
    if len(hist) < 2:
        st.caption("Answer a few more questions and your progress chart will appear here.")
        return
    roll = [100 * sum(hist[max(0, i - 4):i + 1]) / len(hist[max(0, i - 4):i + 1]) for i in range(len(hist))]
    fig = go.Figure(go.Scatter(x=list(range(1, len(hist) + 1)), y=roll, mode="lines+markers", line_color=PAL["accent"],
                               hovertemplate="Answer %{x}: %{y:.0f}%<extra></extra>"))
    if item:
        fig.add_hline(y=item["mastery"] * 100, line_dash="dot", line_color=PAL["warn"], annotation_text="assessment")
    fig.update_xaxes(title="Practice answer number")
    fig.update_yaxes(range=[0, 105], title="Recent accuracy %")
    st.markdown("##### Your progress over time")
    show(style_fig(fig, 260))
    if len(hist) >= 6:
        first, last = 100 * sum(hist[:5]) / 5, 100 * sum(hist[-5:]) / 5
        st.caption(f"{topic}: {first:.0f}% on your first 5 answers, {last:.0f}% on your latest 5.")


# ---------------------------------------------------------------- navigation helpers
def go_practice(sid, topic):
    st.session_state["nav"] = "Practice zone"
    st.session_state[f"pt_{sid}"] = topic


def save_step(sid, topic, step, key):
    tracker.set_step(sid, topic, step, st.session_state.get(key, False))


def suggest_next(rep, topic):
    avail = practice.topics_available()
    gaps = [g["topic"] for g in rep["gaps"] if g["topic"] != topic and g["topic"] in avail]
    if gaps:
        return gaps[0]
    others = [t for t in avail if t != topic]
    return others[0] if others else None


# ---------------------------------------------------------------- student
def tab_overview(sid, rep):
    T = rep["topics"]
    if not T:
        st.info("No assessment results yet. Open the Assessment section to take your first one, or ask your teacher to add your results.")
        return
    p = rep["primary"]
    with st.expander("How to read this page"):
        st.markdown("- **Mastery** is the share of marks you earned in a topic. Harder questions count more.\n"
                    "- **Gap** means a topic is below the gap line on the charts. These come first.\n"
                    "- **How sure we are** goes up when you have answered more questions in a topic and your mistakes follow one pattern.\n"
                    "- A **careless slip** is a mistake on an easy question in a topic you otherwise know well. We do not count it as a gap.")
    c = st.columns(4)
    c[0].markdown(K.kpi("Overall score", f'{rep["overall"]*100:.0f}%', K.overall_msg(rep["overall"], len(rep["gaps"])), K.tone(rep["overall"])), unsafe_allow_html=True)
    c[1].markdown(K.kpi("Gaps found", len(rep["gaps"]), "topics below the gap line", "bad" if rep["gaps"] else "good"), unsafe_allow_html=True)
    c[2].markdown(K.kpi("Biggest gap", p["topic"] if p else "None", K.SEV_S[p["severity"]] if p else "all clear", "bad" if p else "good"), unsafe_allow_html=True)
    c[3].markdown(K.kpi("How sure we are", K.conf_word(p["confidence"]) if p else "-", f'{p["confidence"]*100:.0f}%, higher with more answers' if p else ""), unsafe_allow_html=True)
    if p and p["topic"] in practice.topics_available():
        st.button(f'Practice {p["topic"]} now', key=f"ov_go_{sid}", on_click=go_practice, args=(sid, p["topic"]))
    names, vals = [t["topic"] for t in T], [t["mastery"] * 100 for t in T]
    a, b = st.columns(2)
    a.markdown("##### Assessment mastery by topic")
    with a:
        show(bar_fig(names, vals))
    b.markdown("##### Assessment vs practice")
    with b:
        fig = compare_fig(sid, T)
        if fig:
            show(fig)
        else:
            st.markdown(K.h('<div class="card"><div class="big">No practice yet</div><div class="muted sm" style="margin-top:6px">Practise a topic and this chart will show how your practice compares with your assessment.</div></div>'), unsafe_allow_html=True)
    n, cor = tracker.attempt_totals(sid)
    msg = f"Practice so far: {cor} of {n} correct ({100*cor/n:.0f}%)." if n else "You have not practised yet. Open the Practice zone to start."
    st.markdown(K.h(f'<div class="card"><div class="muted sm">{msg}</div></div>'), unsafe_allow_html=True)
    st.markdown("##### Concept dependency chain")
    st.markdown(K.h(f'<div class="card">{K.chain(T)}<div class="muted sm" style="margin-top:10px">Each topic builds on the one before it. A weak link can pull later topics down.</div></div>'), unsafe_allow_html=True)
    st.markdown(K.topic_grid(T), unsafe_allow_html=True)


def tab_report(sid, rep):
    T = rep["topics"]
    if not T:
        st.info("No gap report yet. Take an assessment first.")
        return
    default = [t["topic"] for t in T].index(rep["primary"]["topic"]) if rep["primary"] else 0
    pick = st.radio("Inspect a topic", [t["topic"] for t in T], index=default, horizontal=True, key=f"pick_{sid}")
    g = next(t for t in T if t["topic"] == pick)
    tn = K.tone(g["mastery"])
    st.markdown(K.h(f'''<div class="card"><div class="big">{g["topic"]}</div>
        <div style="margin:8px 0">{K.pill(g["status"], tn)}{K.pill(K.SEV_S[g["severity"]], K.sev_tone(g["severity"]))}{K.pill("Most common mistake: " + K.ERR_S[g["dominant_error"]])}</div>
        <div class="muted sm">Mastery {g["mastery"]*100:.0f}%</div>{K.meter(g["mastery"]*100, tn)}
        <div class="muted sm">How sure we are: {K.conf_word(g["confidence"])} ({g["confidence"]*100:.0f}%). This goes up with more answers and a steady pattern of mistakes.</div>{K.meter(g["confidence"]*100)}</div>'''), unsafe_allow_html=True)
    if not g["evidence"]:
        st.success("No mistakes in this topic. Nothing to fix here.")
        return
    left, right = st.columns([3, 2])
    with left:
        st.markdown("##### Why we think so (evidence)")
        st.markdown(K.h('<div class="card">' + "".join(K.evidence_row(r, student=True) for r in g["evidence"]) + "</div>"), unsafe_allow_html=True)
    with right:
        st.markdown("##### Mistake pattern")
        cnt = Counter(r["error_type"] for r in g["evidence"])
        rows = "".join(f'<div class="sm">{K.ERR_S[k]} ({v})</div>{K.meter(100*v/len(g["evidence"]), "warn" if k in ("incomplete","careless") else "bad")}' for k, v in cnt.most_common())
        st.markdown(K.h(f'<div class="card">{rows}</div>'), unsafe_allow_html=True)
        if g["root_cause"] != g["topic"]:
            st.warning(f'Root cause: **{g["root_cause"]}**. Fix this first.')
        if g["affects"]:
            st.info("Knock-on effect on: " + ", ".join(g["affects"]))
    if g["status"] != "Mastered":
        st.markdown("##### Your learning path (tick as you go, your ticks are saved)")
        steps, saved = recommend(g, merged_graph()), tracker.get_steps(sid, pick)
        done = 0
        for i, step in enumerate(steps):
            k = f"step_{sid}_{pick}_{i}"
            if k not in st.session_state:
                st.session_state[k] = saved.get(step, False)
            st.checkbox(step, key=k, on_change=save_step, args=(sid, pick, step, k))
            done += int(st.session_state[k])
        st.markdown(K.h(f'<div class="muted sm">{done} of {len(steps)} steps done</div>{K.meter(100*done/len(steps), "good")}'), unsafe_allow_html=True)
        if pick in practice.topics_available():
            st.button(f"Practice {pick}", key=f"rep_go_{sid}_{pick}", on_click=go_practice, args=(sid, pick))
        if done == len(steps):
            st.balloons()


def new_session():
    return {"level": 1, "n": 0, "score": 0, "streak": 0, "q": None, "fb": None, "tries": 0, "last": None, "done": False}


def tab_practice(sid, rep):
    topics = practice.topics_available()
    pk = f"pt_{sid}"
    if st.session_state.get(pk) not in topics:
        prim = rep["primary"]["topic"] if rep["primary"] else None
        st.session_state[pk] = prim if prim in topics else topics[0]
    topic = st.selectbox("Topic to practice", topics, key=pk)
    item = next((t for t in rep["topics"] if t["topic"] == topic), None)
    focus = item["dominant_error"] if item else None
    key = f"quiz_{sid}_{topic}"
    if key not in st.session_state:
        st.session_state[key] = new_session()
    s = st.session_state[key]
    acc = 100 * s["score"] / s["tries"] if s["tries"] else 0
    nxt = suggest_next(rep, topic)

    if s["done"]:
        st.markdown(K.h(f'''<div class="card"><div class="big">Session complete</div>
            <div style="margin:8px 0">{K.pill("Score " + str(s["score"]) + "/" + str(s["tries"]), "good")}{K.pill("Accuracy " + format(acc, ".0f") + "%", K.tone(acc / 100))}{K.pill("Ended on level " + str(s["level"]), "neutral")}</div>
            <div class="muted sm">{"Assessment mastery was " + format(item["mastery"] * 100, ".0f") + "%. " if item else ""}{"You did better in practice than in the assessment." if item and acc > item["mastery"] * 100 else "Every session builds the skill, keep going."}</div></div>'''), unsafe_allow_html=True)
        if nxt:
            st.info(f"Suggested next topic: {nxt}")
            st.button(f"Switch to {nxt}", key=f"sw_{key}", on_click=go_practice, args=(sid, nxt))
        if st.button("Start a new session", key=f"ns_{key}"):
            st.session_state[key] = new_session()
            st.rerun()
        trend_block(sid, topic, item)
        return

    if s["q"] is None:
        s["q"] = practice.next_question(topic, s["level"], focus, avoid=s["last"])
    q = s["q"]
    if q is None:
        st.info("No approved questions for this topic yet. Ask your teacher to add some.")
        return
    alln, allc = tracker.attempt_stats(sid, topic)
    target = f" Targeting: {K.ERR_S[focus]}." if focus not in (None, "none") else ""
    st.markdown(K.h(f'''<div class="card"><div>{K.pill("Level " + str(s["level"]) + ": " + LEVELS[s["level"]], "neutral")}{K.pill("Score " + str(s["score"]) + "/" + str(s["tries"]), "good")}{K.pill("Streak " + str(s["streak"]), "warn")}{K.pill("All time " + str(allc) + "/" + str(alln), "neutral")}</div>
        <div class="muted sm" style="margin-top:10px">Level 1 is easy, 2 is medium, 3 is hard. A correct answer makes the next question harder, a mistake makes it easier.{target}</div>
        <div class="qbox">{q["prompt"]}</div></div>'''), unsafe_allow_html=True)

    if s["fb"] is None:
        wid = f"{key}_{s['n']}"
        if q["kind"] == "mcq":
            labels = [f"{chr(65 + i)}) {o}" for i, o in enumerate(q["options"])]
            pick = st.radio("Choose one", labels, index=None, key=f"ans_{wid}")
            ans = pick[0] if pick else ""
        else:
            ans = st.text_input("Your answer", key=f"ans_{wid}", placeholder="e.g. 2, -3" if q["kind"] == "numeric" else "Type your answer")
        c1, c2 = st.columns([1, 3])
        if c1.button("Check answer", key=f"chk_{wid}"):
            if not ans.strip():
                st.warning("Choose or type an answer first.")
            else:
                verdict, why = practice.grade(q, ans)
                ok = verdict == "correct"
                tracker.save_attempt(sid, topic, q["qid"], ans, ok, s["level"])
                s["fb"] = {"verdict": verdict, "ans": ans, "why": why}
                s["tries"], s["score"], s["last"] = s["tries"] + 1, s["score"] + int(ok), q["qid"]
                s["streak"] = s["streak"] + 1 if ok else 0
                s["level"] = min(3, s["level"] + 1) if ok else max(1, s["level"] - 1)
                st.rerun()
        with c2.expander("Need a hint?"):
            st.write(q["hint"])
    else:
        fb = s["fb"]
        right = practice.model_answer(q)
        extra = (f" Correct answer: {right}." if right else "") + (" " + q["solution"] if q["solution"] else "")
        if fb["verdict"] == "correct":
            st.success("Correct!" + (" " + q["solution"] if q["solution"] else ""))
            if s["streak"] >= 3:
                st.balloons()
                if nxt:
                    st.info(f"Great streak! When you are ready, try {nxt} next.")
                    st.button(f"Switch to {nxt}", key=f"sw_{key}_{s['n']}", on_click=go_practice, args=(sid, nxt))
        elif fb["verdict"] == "partial":
            st.warning("Partly right. You covered some of it, but not everything." + extra)
        else:
            note = f" {fb['why']}." if q["kind"] == "mcq" and fb["why"] and not fb["why"].startswith("chose ") else ""
            st.error(f"Not quite (you wrote {fb['ans']})." + note + extra)
            pre = merged_graph()["prerequisites"].get(topic, [])
            if s["level"] == 1 and pre:
                st.info(f"Still tricky? Revisit the prerequisite: {pre[0]}.")
        b1, b2 = st.columns([1, 1])
        if b1.button("Next question", key=f"nxt_{key}_{s['n']}"):
            s["q"], s["fb"], s["n"] = None, None, s["n"] + 1
            st.rerun()
        if b2.button("Finish session", key=f"fin_{key}_{s['n']}"):
            s["done"] = True
            st.rerun()

    if s["tries"]:
        st.markdown("##### Before and after")
        after = f'<div class="sm muted">After practice (answers this session): {acc:.0f}%</div>{K.meter(acc, K.tone(acc/100))}'
        if item:
            before = item["mastery"] * 100
            msg = "Improving: +" + format(acc - before, ".0f") + " points" if acc > before else "Keep going, the more you practice the clearer this gets."
            st.markdown(K.h(f'''<div class="card"><div class="sm muted">Before practice (assessment mastery): {before:.0f}%</div>{K.meter(before, K.tone(before/100))}
                {after}<div class="big {"goodc" if acc > before else ""}">{msg}</div></div>'''), unsafe_allow_html=True)
        else:
            st.markdown(K.h(f'<div class="card">{after}</div>'), unsafe_allow_html=True)
    trend_block(sid, topic, item)


def tab_assessment(sid, rep):
    qs = tracker.approved_as_questions()
    topics = sorted({q["topic"] for q in qs.values()})
    if not topics:
        st.info("Your teacher has not added any assessment questions yet.")
        return
    saved = st.session_state.pop("assess_saved", None)
    if saved:
        st.success(f"Saved {saved} answers. Your Overview and Gap report are updated.")
    topic = st.selectbox("Assessment topic", topics, key=f"as_t_{sid}")
    items = [q for q in qs.values() if q["topic"] == topic]
    st.caption(f"{len(items)} questions. Your answers are saved when you press Submit. Taking it again replaces your earlier answers.")
    with st.form(f"assess_{sid}_{topic}"):
        answers = {}
        for i, q in enumerate(items, 1):
            st.markdown(f"**Q{i}. {q['stem']}**")
            if q["type"] == "mcq":
                labels = [f"{chr(65 + j)}) {o}" for j, o in enumerate(q["options"])]
                pick = st.radio("Choose one", labels, index=None, key=f"asr_{sid}_{q['qid']}", label_visibility="collapsed")
                answers[q["qid"]] = pick[0] if pick else ""
            else:
                answers[q["qid"]] = st.text_input("Your answer", key=f"asr_{sid}_{q['qid']}", label_visibility="collapsed")
        sent = st.form_submit_button("Submit assessment")
    if sent:
        given = {k: v for k, v in answers.items() if v.strip()}
        if not given:
            st.warning("Answer at least one question first.")
        else:
            tracker.save_responses([(sid, k, v) for k, v in given.items()])
            st.session_state["assess_saved"] = len(given)
            st.rerun()


def student_view(sid):
    rep = reports.get(sid) or EMPTY
    welcome = st.session_state.pop("welcome", None)
    if welcome:
        st.success(welcome)
    p = rep["primary"]
    if p:
        chips = K.pill(f'Biggest gap: {p["topic"]}') + K.pill(K.SEV_S[p["severity"]])
    else:
        chips = K.pill("No gaps detected" if rep["topics"] else "No assessment yet")
    sub = f'Overall score {rep["overall"]*100:.0f}%. {K.overall_msg(rep["overall"], len(rep["gaps"]))}' if rep["topics"] else "Take an assessment to see your first report."
    st.markdown(K.hero(f"Learning gap report: {name(sid)}", sub, chips), unsafe_allow_html=True)
    page = st.radio("Section", NAV, horizontal=True, key="nav", label_visibility="collapsed")
    {"Overview": tab_overview, "Gap report": tab_report, "Practice zone": tab_practice, "Assessment": tab_assessment}[page](sid, rep)
    careless = [r for r in rep["rows"] if r["error_type"] == "careless"]
    if careless and page == "Overview":
        st.caption("Marked as careless slips, not gaps: " + "; ".join(f'{r["qid"]} ({r["topic"]})' for r in careless))


# ---------------------------------------------------------------- teacher
def teacher_dashboard():
    st.markdown(K.hero("Teacher dashboard", "See the whole class at a glance and spot who needs help first."), unsafe_allow_html=True)
    if not reports:
        st.info("No results yet. Import a responses CSV in the Students & data tab, or let students take an assessment.")
        return
    c1, c2 = st.columns([1, 1])
    only = c1.toggle("Only students with gaps", value=False)
    sort = c2.selectbox("Sort students by", ["Name", "Lowest overall first"])
    ids = [s for s in reports if (reports[s]["primary"] or not only)]
    ids.sort(key=(lambda s: reports[s]["overall"]) if sort != "Name" else (lambda s: name(s)))
    if not ids:
        st.info("No students match this filter.")
        return
    order = [t for t in merged_graph()["order"] if any(x["topic"] == t for s in ids for x in reports[s]["topics"])]
    matrix = [[next((t["mastery"] * 100 for t in reports[s]["topics"] if t["topic"] == tp), None) for tp in order] for s in ids]
    avg = [sum(v for v in col if v is not None) / len([v for v in col if v is not None]) for col in zip(*matrix)]
    weakest = order[avg.index(min(avg))]
    flagged = [s for s in ids if reports[s]["primary"]]
    k = st.columns(4)
    k[0].markdown(K.kpi("Students", len(ids)), unsafe_allow_html=True)
    k[1].markdown(K.kpi("Class average", f"{sum(avg)/len(avg):.0f}%", "", K.tone(sum(avg)/len(avg)/100)), unsafe_allow_html=True)
    k[2].markdown(K.kpi("Need attention", len(flagged), "students with a gap", "bad" if flagged else "good"), unsafe_allow_html=True)
    k[3].markdown(K.kpi("Weakest concept", weakest, f"class avg {min(avg):.0f}%"), unsafe_allow_html=True)
    st.markdown("##### Class mastery heatmap")
    st.markdown(K.heat_table([name(s) for s in ids], order, matrix), unsafe_allow_html=True)
    a, b = st.columns(2)
    a.markdown("##### Class average by concept")
    with a:
        show(bar_fig(order, avg))
    b.markdown("##### Students needing intervention")
    for s in flagged:
        g = reports[s]["primary"]
        root = f' Root cause: {g["root_cause"]}.' if g["root_cause"] != g["topic"] else ""
        b.markdown(K.h(f'<div class="card"><div class="big">{name(s)}</div><div>{K.pill(g["topic"], "bad")}{K.pill("Severity " + g["severity"], K.sev_tone(g["severity"]))}{K.pill(K.ERR[g["dominant_error"]], "warn")}</div><div class="muted sm" style="margin-top:6px">Confidence {g["confidence"]*100:.0f}%.{root}</div></div>'), unsafe_allow_html=True)
    if not flagged:
        b.success("No students flagged.")
    st.markdown("##### Drill into a student")
    who = st.selectbox("Choose a student", ids, format_func=name, key="drill")
    for g in reports[who]["gaps"]:
        with st.expander(f'{g["topic"]}: {g["mastery"]*100:.0f}%, severity {g["severity"]}', expanded=True):
            st.markdown("".join(K.evidence_row(r) for r in g["evidence"]), unsafe_allow_html=True)
            for i, step in enumerate(recommend(g, merged_graph()), 1):
                st.write(f"{i}. {step}")


def teacher_data():
    flash = st.session_state.pop("flash", None)
    if flash:
        st.success(flash)
    st.markdown("##### Students and access codes")
    st.caption("Students create their own account. If a student already has results here, give them their teacher code so they can enter it when signing up and link those results.")
    studs = tracker.list_students()
    if studs:
        users = tracker.account_names()
        st.table([{"ID": i, "Name": s["name"], "Teacher code": s["code"], "Account": users.get(i, "not signed up yet")} for i, s in studs.items()])
    with st.form("add_student", clear_on_submit=True):
        nm = st.text_input("New student name")
        if st.form_submit_button("Add student"):
            if nm.strip():
                tracker.add_student(nm)
                st.session_state["flash"] = f"Added {nm.strip()}."
                st.rerun()
            st.error("Enter a name.")
    st.markdown("##### Import responses (CSV)")
    st.caption("Needs the columns student_id, qid and answer. An answer for the same student and question replaces the old one.")
    up = st.file_uploader("Responses CSV", type="csv", key="resp_up")
    if up is not None and st.button("Save to database", key="resp_save"):
        try:
            df = load_responses(io.BytesIO(up.getvalue()))
            tracker.save_responses(list(zip(df["student_id"], df["qid"], df["answer"])))
            st.session_state["flash"] = f"Saved {len(df)} answers."
            st.rerun()
        except Exception as e:
            st.error(str(e))
    st.markdown("##### Practice activity")
    act = tracker.activity_summary()
    if any(r["n"] for r in act):
        st.table([{"Student": r["name"], "Practice answers": r["n"], "Correct": f'{100*r["c"]/r["n"]:.0f}%' if r["n"] else "-"} for r in act])
    else:
        st.caption("No practice answers yet.")


def teacher_view():
    t1, t2, t3 = st.tabs(["Class dashboard", "Content manager", "Students & data"])
    with t1:
        teacher_dashboard()
    with t2:
        content_manager.render(merged_graph())
    with t3:
        teacher_data()


if signed_teacher:
    teacher_view()
elif signed_sid:
    student_view(signed_sid)
else:
    {"landing": landing_page, "login": login_page, "signup": signup_page}.get(st.session_state.get("page"), landing_page)()