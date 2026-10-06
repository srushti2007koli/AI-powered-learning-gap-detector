"""Template-based practice question generator (works offline, answers are exact)."""
import random
from fractions import Fraction as F
from src.analyzer import _numset

SUPPORTED = ["Algebra", "Linear Equations", "Quadratic Equations", "Functions", "Calculus"]


def poly(cs, var="x"):
    n, out = len(cs) - 1, ""
    for i, c in enumerate(cs):
        if c == 0:
            continue
        p, a = n - i, abs(c)
        body = ("" if (a == 1 and p > 0) else str(a)) + (var if p >= 1 else "") + ({2: "²", 3: "³"}.get(p, "") if p >= 2 else "")
        out += (("-" if c < 0 else "") + body) if not out else f" {'-' if c < 0 else '+'} {body}"
    return out or "0"


def _q(prompt, answers, hint, solution):
    return {"prompt": prompt, "answer": {F(a) for a in answers}, "hint": hint, "solution": solution}


def _quad(r, lv, neg):
    if lv == 1 and not neg:
        r1, r2 = r.sample(range(1, 6), 2)
    elif lv == 1:
        r1, r2 = r.randint(1, 4), -r.randint(1, 4)
    elif lv == 2:
        r1, r2 = r.randint(1, 7), -r.randint(1, 7)
    else:
        r1, r2 = r.choice([-1, 1]) * r.randint(1, 6), r.choice([-1, 1]) * r.randint(1, 6)
        if r1 == r2:
            r2 = r1 + 1
    a = 1 if lv < 3 else r.choice([2, 3])
    cs = [a, -a * (r1 + r2), a * r1 * r2]
    return _q(f"Solve {poly(cs)} = 0. Enter the roots separated by a comma.", [r1, r2],
              "The roots add up to -b/a and multiply to c/a. Watch the sign of b.",
              f"Roots are {r1} and {r2}: sum {r1 + r2} = -b/a and product {r1 * r2} = c/a.")


def _lin(r, lv, neg):
    if lv == 1:
        a, b, x = r.randint(2, 5), r.randint(1, 9), (-r.randint(1, 6) if neg else r.randint(-6, 9))
        return _q(f"Solve {poly([a, b])} = {a * x + b}", [x], "Subtract the constant, then divide.",
                  f"{a}x = {a * x}, so x = {x}.")
    if lv == 2:
        a, c = r.randint(3, 6), r.randint(1, 2)
        b, x = r.randint(-5, 9), r.randint(-6, 7)
        d = (a - c) * x + b
        return _q(f"Solve {poly([a, b])} = {poly([c, d])}", [x],
                  "Move x-terms to one side. Flip the sign when a term crosses the equals sign.",
                  f"{a - c}x = {d - b}, so x = {x}.")
    p, q, x = r.randint(2, 5), r.choice([-5, -4, -3, -2, 2, 3, 4, 5]), r.randint(-4, 8)
    return _q(f"Solve {p}(x {'+' if q > 0 else '-'} {abs(q)}) = {p * (x + q)}", [x],
              "Distribute first, or divide both sides by the number outside the bracket.",
              f"x {'+' if q > 0 else '-'} {abs(q)} = {x + q}, so x = {x}.")


def _fun(r, lv, neg):
    if lv == 1:
        a, b, k = r.randint(2, 5), r.randint(-5, 5), (-r.randint(1, 5) if neg else r.randint(1, 6))
        return _q(f"f(x) = {poly([a, b])}. Find f({k}).", [a * k + b], "Replace x with the number in brackets.",
                  f"{a}({k}) + ({b}) = {a * k + b}.")
    if lv == 2:
        b, c, k = r.randint(-5, 5), r.randint(-6, 6), -r.randint(1, 5)
        return _q(f"f(x) = {poly([1, b, c])}. Find f({k}).", [k * k + b * k + c],
                  "Square the whole bracket: a negative number squared is positive.",
                  f"({k})² + ({b})({k}) + ({c}) = {k * k + b * k + c}.")
    a, c, b, k = r.randint(2, 4), r.randint(-3, 3), r.randint(-4, 4), r.randint(-3, 3)
    v = a * k + c
    return _q(f"f(x) = {poly([1, 0, b])} and g(x) = {poly([a, c])}. Find f(g({k})).", [v * v + b],
              "Work from the inside out: find g first, then put the result into f.",
              f"g({k}) = {v}, then f({v}) = {v * v + b}.")


def _alg(r, lv, neg):
    if lv == 1:
        a, b, k = r.randint(2, 5), r.randint(1, 6), r.randint(1, 5)
        return _q(f"Evaluate {a}(x + {b}) when x = {k}", [a * (k + b)], "Add inside the bracket, then multiply.",
                  f"{a} × {k + b} = {a * (k + b)}.")
    if lv == 2:
        a, b, c, d, k = r.randint(2, 4), r.randint(1, 5), r.randint(2, 4), r.randint(1, 5), r.randint(-3, 4)
        return _q(f"Evaluate {a}(x + {b}) - {c}(x - {d}) when x = {k}", [a * (k + b) - c * (k - d)],
                  "The minus sign in front of the second bracket applies to every term inside it.",
                  f"{a * (k + b)} - ({c * (k - d)}) = {a * (k + b) - c * (k - d)}.")
    u, v = r.randint(-5, 6), r.randint(1, 5)
    s, p = u + v, u * v
    return _q(f"If a + b = {s} and ab = {p}, find a² + b²", [s * s - 2 * p],
              "Use (a + b)² = a² + 2ab + b².", f"{s}² - 2({p}) = {s * s - 2 * p}.")


def _calc(r, lv, neg):
    if lv == 1:
        a, b, k = r.randint(1, 5), r.randint(-6, 6), r.randint(-3, 4)
        return _q(f"f(x) = {poly([a, b, 0])}. Find f'({k}).", [2 * a * k + b], "Differentiate: x² becomes 2x.",
                  f"f'(x) = {poly([2 * a, b])}, so f'({k}) = {2 * a * k + b}.")
    if lv == 2:
        a, b, k = r.randint(1, 4), r.randint(-6, 6), r.randint(-2, 3)
        return _q(f"f(x) = {poly([a, 0, b, 0])}. Find f'({k}).", [3 * a * k * k + b], "Differentiate: x³ becomes 3x².",
                  f"f'(x) = {poly([3 * a, 0, b])}, so f'({k}) = {3 * a * k * k + b}.")
    a, b, c = r.randint(1, 4), r.randint(-8, 8), r.randint(-5, 5)
    return _q(f"Find the x-value of the critical point of f(x) = {poly([a, b, c])}", [F(-b, 2 * a)],
              "Set f'(x) = 0 and solve. Fractions like 3/2 are fine.", f"f'(x) = {poly([2 * a, b])} = 0, so x = {F(-b, 2 * a)}.")


_MAKERS = {"Algebra": _alg, "Linear Equations": _lin, "Quadratic Equations": _quad, "Functions": _fun, "Calculus": _calc}


def make_question(topic, level=1, focus=None, seed=None):
    fn = _MAKERS.get(topic)
    if fn is None:
        return None
    return fn(random.Random(seed), max(1, min(3, level)), focus == "sign_error")


def check(q, text):
    got = _numset(text)
    return got is not None and got == q["answer"]
