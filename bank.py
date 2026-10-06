"""Validation, cleaning and sample drafts for the question bank."""
DIFFS = ["easy", "medium", "hard"]
LETTERS = list("ABCD")


def clean(d, topic=None):
    qt = "mcq" if str(d.get("type") or d.get("qtype", "")).lower().startswith("m") else "short_answer"
    opts = [str(o).strip() for o in (d.get("options") or [])][:4] if qt == "mcq" else []
    ca = str(d.get("correct_answer", "")).strip()
    if qt == "mcq":
        match = [LETTERS[i] for i, o in enumerate(opts) if o.lower() == ca.lower()]
        ca = match[0] if match and len(ca) > 1 else ca[:1].upper()
        if ca not in LETTERS:
            ca = ""
    mis = {str(k).strip().upper()[:1]: str(v).strip() for k, v in (d.get("misconceptions") or {}).items() if str(v).strip()}
    diff = str(d.get("difficulty", "medium")).lower()
    return {"topic": topic or d.get("topic", ""), "subtopic": str(d.get("subtopic", "") or ""),
            "difficulty": diff if diff in DIFFS else "medium", "qtype": qt, "question": str(d.get("question", "")).strip(),
            "options": opts, "correct_answer": ca if qt == "mcq" else ca,
            "misconceptions": mis if qt == "mcq" else {}, "accepted": [str(a).strip() for a in (d.get("accepted") or []) if str(a).strip()],
            "keywords": [str(k).strip() for k in (d.get("keywords") or []) if str(k).strip()],
            "hint": str(d.get("hint", "") or "").strip(), "solution": str(d.get("solution", "") or "").strip()}


def validate(d):
    p = []
    if not d.get("question", "").strip():
        p.append("The question is empty.")
    if d.get("qtype") == "mcq":
        opts = d.get("options") or []
        if len([o for o in opts if o.strip()]) < 3 or any(not o.strip() for o in opts):
            p.append("Fill in all four options.")
        if d.get("correct_answer") not in LETTERS[:len(opts)]:
            p.append("Choose which option is correct.")
        if len({o.strip().lower() for o in opts}) < len(opts):
            p.append("Two options are identical.")
    elif not d.get("correct_answer", "").strip():
        p.append("The model answer is empty.")
    if not d.get("hint", "").strip():
        p.append("Add a hint (it should not give the answer away).")
    return p


_TENSES = [
        {"type": "mcq", "difficulty": "easy", "question": "Choose the correct form: She ___ to school every day.",
         "options": ["go", "goes", "going", "gone"], "correct_answer": "B",
         "misconceptions": {"A": "Subject-verb agreement: used the base verb with a third person singular subject",
                            "C": "Used the -ing form without a helping verb", "D": "Used the past participle as a simple present"},
         "hint": "Look at the subject. Is it one person or many?", "solution": "'She' is third person singular, so the simple present verb takes -s: goes."},
        {"type": "mcq", "difficulty": "medium", "question": "Which sentence is in the past perfect tense?",
         "options": ["I had finished my homework before dinner.", "I have finished my homework.", "I finished my homework.", "I will have finished my homework."],
         "correct_answer": "A",
         "misconceptions": {"B": "Confused past perfect with present perfect", "C": "Confused past perfect with simple past",
                            "D": "Confused past perfect with future perfect"},
         "hint": "Past perfect uses 'had' plus the past participle.", "solution": "'Had finished' shows an action completed before another past action."},
        {"type": "short_answer", "difficulty": "easy", "question": "Rewrite in the past tense: 'I eat an apple.'",
         "correct_answer": "I ate an apple.", "accepted": ["I ate an apple", "I had an apple"],
         "hint": "'Eat' is an irregular verb.", "solution": "The past tense of 'eat' is 'ate'."},
        {"type": "short_answer", "difficulty": "hard", "question": "In one sentence, explain when we use the present perfect tense.",
         "correct_answer": "We use it for past actions that connect to the present.",
         "keywords": ["past|finished|completed|happened|already", "present|now|result|connect|still|today"],
         "hint": "Think about a past action that still matters now.",
         "solution": "The present perfect links a past action to the present, for example 'I have lost my keys'."},
]

SAMPLES = {"Tenses": _TENSES, **{'Quadratic Equations': [{'type': 'mcq',
                          'difficulty': 'easy',
                          'question': 'What are the roots of x² - 5x + 6 = 0?',
                          'options': ['x = 2 and x = 3', 'x = -2 and x = -3', 'x = 1 and x = 6', 'x = -1 and x = -6'],
                          'correct_answer': 'A',
                          'misconceptions': {'B': 'Sign error: the roots add up to +5, so they cannot both be negative',
                                             'C': 'Picked factors of 6 that do not add up to 5',
                                             'D': 'Wrong factors and a sign error'},
                          'hint': 'Find two numbers that multiply to 6 and add to 5.',
                          'solution': 'x² - 5x + 6 = (x - 2)(x - 3), so x = 2 or x = 3.'},
                         {'type': 'mcq',
                          'difficulty': 'medium',
                          'question': 'Which equation has roots x = 4 and x = -1?',
                          'options': ['x² - 3x - 4 = 0', 'x² + 3x - 4 = 0', 'x² - 5x + 4 = 0', 'x² + 5x + 4 = 0'],
                          'correct_answer': 'A',
                          'misconceptions': {'B': 'Reversed the sign of both roots (these roots are -4 and 1)',
                                             'C': 'Used roots 4 and 1, dropping the minus sign on -1',
                                             'D': 'Used roots -4 and -1'},
                          'hint': 'The roots add up to 3 and multiply to -4.',
                          'solution': '(x - 4)(x + 1) = x² - 3x - 4.'},
                         {'type': 'short_answer',
                          'difficulty': 'easy',
                          'question': 'Solve x² - 9 = 0. Enter the roots separated by a comma.',
                          'correct_answer': '3, -3',
                          'accepted': ['3,-3', '-3, 3', '-3,3', '3 and -3', '-3 and 3'],
                          'hint': 'A square can come from a positive or a negative number.',
                          'solution': 'x² = 9, so x = 3 or x = -3.'},
                         {'type': 'short_answer',
                          'difficulty': 'medium',
                          'question': 'Solve x² + 2x - 8 = 0. Enter the roots separated by a comma.',
                          'correct_answer': '2, -4',
                          'accepted': ['2,-4', '-4, 2', '-4,2', '2 and -4', '-4 and 2'],
                          'hint': 'Find two numbers that multiply to -8 and add to 2.',
                          'solution': 'x² + 2x - 8 = (x + 4)(x - 2), so x = -4 or x = 2.'}],
 'Linear Equations': [{'type': 'mcq',
                       'difficulty': 'easy',
                       'question': 'Solve 3x + 5 = 20.',
                       'options': ['x = 5', 'x = 15', 'x = -5', 'x = 25/3'],
                       'correct_answer': 'A',
                       'misconceptions': {'B': 'Subtracted 5 but forgot to divide by 3',
                                          'C': 'Sign error when moving the 5',
                                          'D': 'Added 5 instead of subtracting it'},
                       'hint': 'Subtract 5 from both sides first, then divide.',
                       'solution': '3x = 15, so x = 5.'},
                      {'type': 'mcq',
                       'difficulty': 'medium',
                       'question': 'Solve 5x - 7 = 2x + 8.',
                       'options': ['x = 5', 'x = 15/7', 'x = -5', 'x = 3'],
                       'correct_answer': 'A',
                       'misconceptions': {'B': 'Added 2x to both sides instead of subtracting it',
                                          'C': 'Sign error when moving terms across the equals sign',
                                          'D': 'Divided 15 by 5 instead of by 3'},
                       'hint': 'Collect the x-terms on one side and the numbers on the other.',
                       'solution': '3x = 15, so x = 5.'},
                      {'type': 'short_answer',
                       'difficulty': 'easy',
                       'question': 'Solve 2(x + 3) = 14.',
                       'correct_answer': '4',
                       'accepted': ['x = 4', 'x=4'],
                       'hint': 'Divide both sides by 2, or expand the bracket first.',
                       'solution': 'x + 3 = 7, so x = 4.'},
                      {'type': 'short_answer',
                       'difficulty': 'medium',
                       'question': 'Solve 7 - 2x = 1.',
                       'correct_answer': '3',
                       'accepted': ['x = 3', 'x=3'],
                       'hint': 'Subtract 7 from both sides, then divide by the negative number.',
                       'solution': '-2x = -6, so x = 3.'}],
 'Algebra': [{'type': 'mcq',
              'difficulty': 'easy',
              'question': 'Simplify 3(x + 4) - 2x.',
              'options': ['x + 12', '5x + 12', 'x + 4', '5x + 4'],
              'correct_answer': 'A',
              'misconceptions': {'B': 'Added 2x instead of subtracting it',
                                 'C': 'Multiplied 3 by x only, not by 4',
                                 'D': 'Made both mistakes'},
              'hint': 'Expand the bracket first, then collect like terms.',
              'solution': '3x + 12 - 2x = x + 12.'},
             {'type': 'mcq',
              'difficulty': 'medium',
              'question': 'Expand (x + 3)(x - 2).',
              'options': ['x² + x - 6', 'x² - 6', 'x² + 5x - 6', 'x² + x + 6'],
              'correct_answer': 'A',
              'misconceptions': {'B': 'Dropped the middle term',
                                 'C': 'Added 3 and 2 instead of subtracting them',
                                 'D': 'Sign error on the constant'},
              'hint': 'Multiply every term in the first bracket by every term in the second.',
              'solution': 'x² - 2x + 3x - 6 = x² + x - 6.'},
             {'type': 'short_answer',
              'difficulty': 'easy',
              'question': 'Evaluate 2a + 3b when a = 4 and b = -1.',
              'correct_answer': '5',
              'accepted': [],
              'hint': 'Put the numbers in brackets so the minus sign is not lost.',
              'solution': '2(4) + 3(-1) = 8 - 3 = 5.'},
             {'type': 'short_answer',
              'difficulty': 'medium',
              'question': 'Factorise x² + 7x + 12.',
              'correct_answer': '(x + 3)(x + 4)',
              'accepted': ['(x+3)(x+4)', '(x + 4)(x + 3)', '(x+4)(x+3)'],
              'hint': 'Find two numbers that multiply to 12 and add to 7.',
              'solution': '3 × 4 = 12 and 3 + 4 = 7, so (x + 3)(x + 4).'}],
 'Functions': [{'type': 'mcq',
                'difficulty': 'easy',
                'question': 'If f(x) = 2x + 1, what is f(3)?',
                'options': ['7', '6', '5', '9'],
                'correct_answer': 'A',
                'misconceptions': {'B': 'Forgot to add 1',
                                   'C': 'Added 2 and 3 instead of multiplying',
                                   'D': 'Used 2³ + 1'},
                'hint': 'Replace x with 3.',
                'solution': 'f(3) = 2(3) + 1 = 7.'},
               {'type': 'mcq',
                'difficulty': 'medium',
                'question': 'If f(x) = x² - 3x, what is f(-2)?',
                'options': ['10', '2', '-10', '-2'],
                'correct_answer': 'A',
                'misconceptions': {'B': 'Treated (-2)² as -4',
                                   'C': 'Sign error on both terms',
                                   'D': 'Squared correctly but subtracted 6 instead of adding it'},
                'hint': 'A negative number squared is positive, and -3 times -2 is positive.',
                'solution': '(-2)² - 3(-2) = 4 + 6 = 10.'},
               {'type': 'short_answer',
                'difficulty': 'easy',
                'question': 'f(x) = 5x - 4. Find f(2).',
                'correct_answer': '6',
                'accepted': ['f(2) = 6'],
                'hint': 'Replace x with 2.',
                'solution': '5(2) - 4 = 6.'},
               {'type': 'short_answer',
                'difficulty': 'hard',
                'question': 'f(x) = x + 2 and g(x) = 3x. Find f(g(2)).',
                'correct_answer': '8',
                'accepted': ['f(g(2)) = 8'],
                'hint': 'Work from the inside out: find g(2) first.',
                'solution': 'g(2) = 6, then f(6) = 8.'}],
 'Calculus': [{'type': 'mcq',
               'difficulty': 'easy',
               'question': 'What is the derivative of x³?',
               'options': ['3x²', 'x⁴/4', '3x³', 'x²'],
               'correct_answer': 'A',
               'misconceptions': {'B': 'Integrated instead of differentiating',
                                  'C': 'Multiplied by the power but did not reduce it',
                                  'D': 'Reduced the power but forgot to multiply'},
               'hint': 'Bring the power down, then reduce the power by 1.',
               'solution': 'd/dx of x³ = 3x².'},
              {'type': 'mcq',
               'difficulty': 'medium',
               'question': "Find f'(x) for f(x) = 4x² - 6x + 1.",
               'options': ['8x - 6', '4x - 6', '8x² - 6x', '8x - 5'],
               'correct_answer': 'A',
               'misconceptions': {'B': 'Differentiated 4x² as 4x',
                                  'C': 'Multiplied by the powers but did not reduce them',
                                  'D': 'Treated the derivative of the constant as 1'},
               'hint': 'Differentiate each term separately. A constant becomes 0.',
               'solution': "f'(x) = 8x - 6."},
              {'type': 'short_answer',
               'difficulty': 'easy',
               'question': "Find f'(2) for f(x) = x² + 3x.",
               'correct_answer': '7',
               'accepted': ["f'(2) = 7"],
               'hint': 'Differentiate first, then put in x = 2.',
               'solution': "f'(x) = 2x + 3, so f'(2) = 7."},
              {'type': 'short_answer',
               'difficulty': 'medium',
               'question': 'Find the x-value of the stationary point of f(x) = x² - 6x + 5.',
               'correct_answer': '3',
               'accepted': ['x = 3'],
               'hint': "A stationary point is where f'(x) = 0.",
               'solution': "f'(x) = 2x - 6 = 0, so x = 3."}]}}


def has_samples(topic):
    return topic in SAMPLES


def sample_drafts(topic):
    """Offline example questions that really belong to the topic. Empty list if there are none."""
    return [clean(r, topic) for r in SAMPLES.get(topic, [])]