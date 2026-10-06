"""Teacher content manager: add topics and questions, generate AI drafts, review and approve."""
import json

import streamlit as st

from src import tracker, bank, llm_client
from src.loader import load_graph
from ui import components as K

TYPE_LABEL = {"mcq": "Multiple choice", "short_answer": "Short answer"}


def _split(s):
    return [x.strip() for x in s.split(",") if x.strip()]


def editor(d, p, topics):
    c1, c2, c3 = st.columns(3)
    topic = c1.selectbox("Topic", topics, index=topics.index(d["topic"]) if d.get("topic") in topics else 0, key=f"{p}_topic")
    qtype = c2.radio("Type", list(TYPE_LABEL), index=0 if d.get("qtype", "mcq") == "mcq" else 1,
                     format_func=lambda x: TYPE_LABEL[x], horizontal=True, key=f"{p}_type")
    diff = c3.selectbox("Difficulty", bank.DIFFS, index=bank.DIFFS.index(d.get("difficulty", "easy")), key=f"{p}_diff")
    out = {"topic": topic, "qtype": qtype, "difficulty": diff, "options": [], "misconceptions": {}, "accepted": [], "keywords": []}
    out["question"] = st.text_area("Question", d.get("question", ""), key=f"{p}_q").strip()
    if qtype == "mcq":
        opts, mis = list(d.get("options") or []) + [""] * 4, d.get("misconceptions", {})
        options, notes = [], {}
        for i, L in enumerate(bank.LETTERS):
            a, b = st.columns(2)
            options.append(a.text_input(f"Option {L}", opts[i], key=f"{p}_o{i}").strip())
            notes[L] = b.text_input(f"Why a student might pick {L} (optional)", mis.get(L, ""), key=f"{p}_m{i}").strip()
        cur = d.get("correct_answer", "A")
        correct = st.selectbox("Correct option", bank.LETTERS, index=bank.LETTERS.index(cur) if cur in bank.LETTERS else 0, key=f"{p}_c")
        out.update(options=options, correct_answer=correct, misconceptions={k: v for k, v in notes.items() if v and k != correct})
    else:
        out["correct_answer"] = st.text_input("Model answer", d.get("correct_answer", ""), key=f"{p}_ca").strip()
        out["accepted"] = _split(st.text_input("Other accepted answers (comma separated)", ", ".join(d.get("accepted", [])), key=f"{p}_acc"))
        out["keywords"] = _split(st.text_input("Key ideas to look for (comma separated, use | for alternatives)",
                                               ", ".join(d.get("keywords", [])), key=f"{p}_kw"))
    out["hint"] = st.text_input("Hint (do not give the answer away)", d.get("hint", ""), key=f"{p}_h").strip()
    out["solution"] = st.text_area("Explanation shown after answering", d.get("solution", ""), height=80, key=f"{p}_s").strip()
    out["subtopic"] = d.get("subtopic", "")
    return out


def tab_review(topics):
    drafts = tracker.list_questions("draft")
    if not drafts:
        st.info("No drafts waiting. Generate some in the AI drafts tab, or add a question yourself.")
        return
    st.caption("Nothing here is visible to students until you approve it. Edit anything that looks wrong first.")
    for d in drafts:
        src = {"ai": "AI draft", "sample": "Sample draft"}.get(d["source"], "Draft")
        with st.expander(f'{d["qid"]} · {d["topic"]} · {TYPE_LABEL[d["qtype"]]} · {d["difficulty"]} · {src}'):
            e = editor(d, f'rq_{d["qid"]}', topics)
            problems = bank.validate(e)
            for pr in problems:
                st.warning(pr)
            a, b, c = st.columns(3)
            if a.button("Approve", key=f'ap_{d["qid"]}'):
                if problems:
                    st.error("Fix the warnings above before approving.")
                else:
                    tracker.update_question(d["qid"], e)
                    tracker.set_status(d["qid"], "approved")
                    st.rerun()
            if b.button("Save changes", key=f'sv_{d["qid"]}'):
                tracker.update_question(d["qid"], e)
                st.success("Saved.")
            if c.button("Reject", key=f'rj_{d["qid"]}'):
                tracker.set_status(d["qid"], "rejected")
                st.rerun()


def tab_add(topics):
    ctr = st.session_state.get("new_ctr", 0)
    e = editor({}, f"new{ctr}", topics)
    if st.button("Save question", key=f"save_new{ctr}"):
        problems = bank.validate(e)
        for pr in problems:
            st.error(pr)
        if not problems:
            tracker.add_question(e, "approved", "teacher")
            st.session_state["new_ctr"] = ctr + 1
            st.rerun()


def tab_ai(topics):
    st.caption("The AI writes drafts. You review them in the Review queue before students see anything.")
    c1, c2, c3 = st.columns(3)
    topic = c1.selectbox("Topic", topics, key="ai_topic")
    qtype = c2.selectbox("Question type", list(TYPE_LABEL), format_func=lambda x: TYPE_LABEL[x], key="ai_type")
    diff = c3.selectbox("Difficulty", bank.DIFFS, index=1, key="ai_diff")
    n = st.slider("How many questions", 2, 8, 4, key="ai_n")
    notes = st.text_area("Optional notes for the AI (chapter, class level, focus area)", key="ai_notes", height=70)
    a, b = st.columns(2)
    if a.button("Generate drafts with AI", key="ai_go"):
        with st.spinner("Writing questions..."):
            subject = {t["name"]: t["subject"] for t in tracker.list_topics()}.get(topic, "Mathematics")
            raw, err = llm_client.generate_questions(topic, subject, n, qtype, diff, notes)
        if err:
            st.error(err)
        else:
            for r in raw:
                tracker.add_question(bank.clean(r, topic), "draft", "ai")
            st.success(f"{len(raw)} drafts added. Open the Review queue to check them.")
    if b.button("Load sample drafts (offline demo)", key="ai_sample"):
        have = {r["question"] for r in tracker.list_questions() if r["topic"] == topic}
        fresh = [r for r in bank.sample_drafts(topic) if r["question"] not in have]
        if not bank.has_samples(topic):
            st.info(f"There are no offline samples for {topic}. Use 'Generate drafts with AI' (needs an API key in .env) or add questions yourself.")
        elif not fresh:
            st.info(f"The sample drafts for {topic} are already in your question bank.")
        else:
            for r in fresh:
                tracker.add_question(r, "draft", "sample")
            st.success(f"{len(fresh)} sample drafts for {topic} added to the Review queue. These are examples, not AI output.")


def tab_topics(topics):
    builtin = set(load_graph()["order"])
    st.markdown("##### Add a topic")
    st.caption("Use this for a new topic only. Algebra, Linear Equations, Quadratic Equations, Functions and Calculus already exist.")
    with st.form("add_topic", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Topic name", placeholder="Tenses")
        subject = c2.text_input("Subject", value="English", help="Maths topics: write Mathematics. The AI uses this to write the right kind of questions.")
        pre = c3.selectbox("Builds on (prerequisite)", ["(none)"] + topics)
        if st.form_submit_button("Add topic"):
            if not name.strip():
                st.error("Enter a topic name.")
            elif name.strip().lower() in {t.lower() for t in topics}:
                st.error(f"{name.strip()} already exists. Pick it from the Topic list instead of adding it again.")
            elif not subject.strip():
                st.error("Enter a subject, for example Mathematics or English.")
            else:
                tracker.add_topic(name, subject, None if pre == "(none)" else pre)
                st.rerun()
    mine = tracker.list_topics()
    if mine:
        st.table([{"Topic": t["name"], "Subject": t["subject"], "Builds on": t["prereq"] or "None"} for t in mine])
        pick = st.selectbox("Remove a topic you added", [t["name"] for t in mine], key="del_topic")
        used = [q for q in tracker.list_questions(topic=pick)]
        if pick not in builtin and used:
            st.caption(f"{pick} has {len(used)} questions. Delete them in the Question bank first, then remove the topic.")
        elif st.button("Remove topic", key="del_topic_go"):
            tracker.delete_topic(pick)
            st.rerun()
        if pick in builtin:
            st.caption(f"{pick} is a built-in topic, so removing this entry only deletes the duplicate. The topic stays available.")


def tab_bank():
    rows = tracker.list_questions()
    approved = [r for r in rows if r["status"] == "approved"]
    c = st.columns(3)
    c[0].markdown(K.kpi("Approved", len(approved), "visible to students", "good"), unsafe_allow_html=True)
    c[1].markdown(K.kpi("Drafts", sum(r["status"] == "draft" for r in rows), "waiting for review", "warn"), unsafe_allow_html=True)
    c[2].markdown(K.kpi("Rejected", sum(r["status"] == "rejected" for r in rows)), unsafe_allow_html=True)
    if rows:
        st.table([{"ID": r["qid"], "Topic": r["topic"], "Type": TYPE_LABEL[r["qtype"]], "Level": r["difficulty"],
                   "Status": r["status"], "Question": r["question"][:70]} for r in rows])
        a, b = st.columns(2)
        pick = a.selectbox("Delete a question", [r["qid"] for r in rows], key="del_pick")
        if a.button("Delete", key="del_go"):
            tracker.delete_question(pick)
            st.rerun()
        b.download_button("Export bank (JSON)", json.dumps(rows, indent=2), file_name="question_bank.json", mime="application/json")
    up = st.file_uploader("Import questions (JSON list, same format as the export)", type="json", key="imp")
    if up is not None and st.button("Import now", key="imp_go"):
        try:
            data, ok, bad = json.loads(up.getvalue()), 0, 0
            for r in data:
                e = bank.clean(r)
                if bank.validate(e):
                    tracker.add_question(e, "draft", "import")
                    bad += 1
                else:
                    tracker.add_question(e, "approved", "import")
                    ok += 1
            st.success(f"{ok} imported as approved, {bad} sent to the Review queue to fix.")
        except Exception:
            st.error("That file could not be read. Use a JSON list of questions.")


def render(graph):
    topics = list(dict.fromkeys(graph["order"]))
    n = len(tracker.list_questions("draft"))
    t = st.tabs([f"Review queue ({n})", "Add question", "AI drafts", "Topics", "Question bank"])
    with t[0]:
        tab_review(topics)
    with t[1]:
        tab_add(topics)
    with t[2]:
        tab_ai(topics)
    with t[3]:
        tab_topics(topics)
    with t[4]:
        tab_bank()