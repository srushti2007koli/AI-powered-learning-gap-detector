from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
QUESTIONS_FILE = DATA_DIR / "questions.json"
RESPONSES_FILE = DATA_DIR / "responses.csv"
GRAPH_FILE = DATA_DIR / "concept_graph.json"
STUDENTS_FILE = DATA_DIR / "students.json"
GROUND_TRUTH_FILE = DATA_DIR / "ground_truth.json"
DB_FILE = DATA_DIR / "progress.db"

DIFFICULTY_WEIGHT = {"easy": 1, "medium": 2, "hard": 3}
SCORE = {"correct": 1.0, "partial": 0.5, "incorrect": 0.0}

MASTERED = 0.75
GAP = 0.45
SEVERITY_HIGH = 0.70