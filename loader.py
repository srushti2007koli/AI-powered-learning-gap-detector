import json
import pandas as pd
from src import config as C


def load_questions():
    with open(C.QUESTIONS_FILE) as f:
        return {q["qid"]: q for q in json.load(f)}


def load_responses(source=None):
    df = pd.read_csv(source or C.RESPONSES_FILE, dtype=str).fillna("")
    need = {"student_id", "qid", "answer"}
    if not need.issubset(df.columns):
        raise ValueError(f"responses file needs columns {sorted(need)}")
    return df


def load_graph():
    with open(C.GRAPH_FILE) as f:
        return json.load(f)


def load_students():
    with open(C.STUDENTS_FILE) as f:
        return json.load(f)
