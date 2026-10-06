"""Compare rule-based analyzer to ground truth. Run: python evaluate.py"""
import json
from src import config as C
from src.loader import load_questions, load_responses
from src.analyzer import analyze

q = load_questions()
gt = {(g["student_id"], g["qid"]): g for g in json.load(open(C.GROUND_TRUTH_FILE))}
df = load_responses()
v = e = n = 0
for _, r in df.iterrows():
    a, g = analyze(q[r["qid"]], r["answer"]), gt[(r["student_id"], r["qid"])]
    n += 1
    v += a["verdict"] == g["verdict"]
    if g["verdict"] != "correct":
        e += 0
print(f"Verdict accuracy: {v}/{n} = {100*v/n:.0f}%")
wrong = [(r["student_id"], r["qid"]) for _, r in df.iterrows()
         if gt[(r["student_id"], r["qid"])]["verdict"] != "correct"]
hit = sum(analyze(q[b], df[(df.student_id == a) & (df.qid == b)].iloc[0]["answer"])["error_type"]
          == gt[(a, b)]["error_type"] for a, b in wrong)
print(f"Error-type accuracy on wrong answers: {hit}/{len(wrong)} = {100*hit/len(wrong):.0f}% (rest need the LLM)")
