"""Optional LLM fallback for answers the rules cannot classify.
Needs ANTHROPIC_API_KEY in .env. Results are cached in cache/llm_cache.json
so the demo still works offline."""
import json, os, re
from src.config import BASE_DIR

CACHE = BASE_DIR / "cache" / "llm_cache.json"
MODEL = "claude-sonnet-5-5"
TAXONOMY = ["sign_error", "procedural", "conceptual", "calculation", "incomplete"]
PROMPT = """You are grading one student answer.
Question: {q}
Correct answer: {c}
Student answer: {a}
Pick ONE error type from {tax}. Reply with JSON only:
{{"error_type": "...", "misconception": "<one short sentence>"}}"""


def _load():
    return json.loads(CACHE.read_text()) if CACHE.exists() else {}


def classify(question, answer):
    key = f"{question['qid']}|{answer}"
    cache = _load()
    if key in cache:
        return cache[key]
    try:
        from dotenv import load_dotenv
        import anthropic
        load_dotenv(BASE_DIR / ".env")
        if not os.getenv("ANTHROPIC_API_KEY"):
            return None
        msg = anthropic.Anthropic().messages.create(
            model=MODEL, max_tokens=200, temperature=0,
            messages=[{"role": "user", "content": PROMPT.format(
                q=question["question"], c=question["correct_answer"], a=answer, tax=TAXONOMY)}])
        out = json.loads(msg.content[0].text.strip().strip("`").replace("json", "", 1))
        if out.get("error_type") not in TAXONOMY:
            return None
        cache[key] = out
        CACHE.parent.mkdir(exist_ok=True)
        CACHE.write_text(json.dumps(cache, indent=2))
        return out
    except Exception:
        return None


GEN_PROMPT = """You are an experienced {subject} teacher writing practice questions.
Topic: {topic}. Write {n} {kind} questions at {diff} difficulty. {notes}
Reply with a JSON array only, no other text. Each item has these keys:
{fields}
Never give the answer away in the hint."""
MCQ_FIELDS = ('"type":"mcq", "difficulty", "question", "options" (exactly 4 strings), "correct_answer" (letter A-D), '
              '"misconceptions" (object: letter of each WRONG option -> one short sentence on why a student might pick it), '
              '"hint", "solution" (short explanation)')
TEXT_FIELDS = ('"type":"short_answer", "difficulty", "question", "correct_answer", "accepted" (list of other acceptable answers), '
               '"keywords" (list of key ideas; use | between alternative words), "hint", "solution"')


def generate_questions(topic, subject, n, qtype, difficulty, notes=""):
    """Return (list_of_raw_question_dicts, error_message_or_None). Drafts only; teacher must approve."""
    try:
        from dotenv import load_dotenv
        import anthropic
        load_dotenv(BASE_DIR / ".env")
        if not os.getenv("ANTHROPIC_API_KEY"):
            return [], "No ANTHROPIC_API_KEY found in .env. Add it, or use 'Load sample drafts'."
        prompt = GEN_PROMPT.format(subject=subject, topic=topic, n=n, diff=difficulty,
                                   kind="multiple choice" if qtype == "mcq" else "short answer",
                                   fields=MCQ_FIELDS if qtype == "mcq" else TEXT_FIELDS,
                                   notes=f"Teacher notes: {notes}" if notes.strip() else "")
        msg = anthropic.Anthropic().messages.create(model=MODEL, max_tokens=3000,
                                                    messages=[{"role": "user", "content": prompt}])
        text = re.sub(r"^```(?:json)?|```$", "", msg.content[0].text.strip(), flags=re.M).strip()
        data = json.loads(text)
        data = [data] if isinstance(data, dict) else data
        data = [d for d in data if isinstance(d, dict)]
        return (data, None) if data else ([], "The AI returned no questions. Try again.")
    except ImportError:
        return [], "The anthropic package is missing. Run: pip install anthropic"
    except Exception as e:
        return [], f"Could not generate questions: {e}"