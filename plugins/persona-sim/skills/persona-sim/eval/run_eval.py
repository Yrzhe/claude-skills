"""Auto-eval suites. Data-ready: fill eval/{gss_20q,bfi44,anes_demo_corr}.json to activate.

Each suite returns: {name, status, metric, value, threshold, pass, note}.
Overall report: eval/reports/score_card_YYYYMMDD.json
"""
from __future__ import annotations
import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib import sampler, sim_engine
from lib.sim_engine import _JSON_FENCE, _persona_card, SYSTEM_PROMPT
from lib.llm_router import generate

EVAL_DIR = Path(__file__).parent
REPORT_DIR = EVAL_DIR / "reports"
THRESHOLDS = {
    "gss_20q":      {"metric": "js_divergence_mean", "max": 0.15},
    "bfi44":        {"metric": "domains_within_1sd_fraction", "min": 0.6},
    "test_retest":  {"metric": "cohen_kappa", "min": 0.6},
    "diversity":    {"metric": "shannon_entropy_ratio", "min": 0.7},
    "demo_corr":    {"metric": "frobenius_distance", "max": 0.8},
    "bias_audit":   {"metric": "calibration_warnings", "max": 2},
}


# ---------------- Shared helpers ----------------

def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception as e:
        print(f"WARN: failed to load {path}: {e}", file=sys.stderr)
        return None


def _parse_json_answer(text: str, key: str) -> str | int | float | None:
    """Robust: tries direct JSON, then searches for first {...} object containing the key.
    Real LLM output often has ```json fences PLUS trailing prose explanation."""
    import re as _re
    cleaned = _JSON_FENCE.sub("", text.strip()).strip()
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict):
            return obj.get(key)
    except (ValueError, TypeError):
        pass
    for m in _re.finditer(r"\{[^{}]*\}", cleaned):
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict) and key in obj:
                return obj[key]
        except (ValueError, TypeError):
            continue
    return None


def _ask_persona(persona: dict, task: str, max_tokens: int = 200) -> str:
    return generate(
        system=SYSTEM_PROMPT,
        persona_card=_persona_card(persona),
        task=task,
        tier="default",
        max_tokens=max_tokens,
    )


def _parallel_ask(personas: list[dict], task_fn, max_workers: int = 8) -> list:
    """task_fn(persona) → result. Returns list in panel order, None on failure."""
    out: list = [None] * len(personas)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(task_fn, p): i for i, p in enumerate(personas)}
        for f in as_completed(futs):
            try:
                out[futs[f]] = f.result()
            except Exception as e:
                print(f"  panel item failed: {e}", file=sys.stderr)
    return out


def _js_divergence(p: dict, q: dict) -> float:
    """Jensen-Shannon divergence between two categorical distributions (dict option→prob)."""
    keys = set(p) | set(q)
    eps = 1e-12
    m = {k: 0.5 * (p.get(k, 0) + q.get(k, 0)) + eps for k in keys}
    def kl(a, b):
        return sum(a.get(k, 0) * math.log((a.get(k, 0) + eps) / b[k]) for k in keys if a.get(k, 0) > 0)
    return 0.5 * (kl(p, m) + kl(q, m)) / math.log(2)  # normalize to [0,1]


# ---------------- Suite: GSS 20q ----------------

def suite_gss_20q(panel: list[dict]) -> dict:
    data = _load_json(EVAL_DIR / "gss_20q.json")
    if not data:
        return {"name": "gss_20q", "status": "skipped", "note": "eval/gss_20q.json missing"}

    items = data["items"]
    per_item = []
    for item in items:
        options = list(item["options"])
        task = (
            f"Question: {item['question']}\n"
            f"Choose ONE option from: {options}\n"
            f'Respond JSON: {{"answer": "<option>"}}'
        )
        raws = _parallel_ask(panel, lambda p, t=task: _ask_persona(p, t, max_tokens=120))
        answers = [_parse_json_answer(r, "answer") for r in raws if r]
        answers = [a for a in answers if a in options]
        if not answers:
            per_item.append({"id": item["id"], "status": "no_valid_answers"})
            continue
        sim_dist = {o: answers.count(o) / len(answers) for o in options}
        js = _js_divergence(sim_dist, item["options"])
        per_item.append({
            "id": item["id"],
            "n_valid": len(answers),
            "sim_dist": {k: round(v, 3) for k, v in sim_dist.items()},
            "real_dist": item["options"],
            "js_divergence": round(js, 3),
        })

    valid = [x for x in per_item if "js_divergence" in x]
    if not valid:
        return {"name": "gss_20q", "status": "failed", "note": "no valid items"}
    mean_js = sum(x["js_divergence"] for x in valid) / len(valid)
    th = THRESHOLDS["gss_20q"]
    return {
        "name": "gss_20q",
        "status": "ok",
        "metric": th["metric"],
        "value": round(mean_js, 3),
        "threshold": th["max"],
        "pass": mean_js <= th["max"],
        "per_item": per_item,
    }


# ---------------- Suite: BFI-44 ----------------

def suite_bfi44(panel: list[dict]) -> dict:
    data = _load_json(EVAL_DIR / "bfi44.json")
    if not data:
        return {"name": "bfi44", "status": "skipped", "note": "eval/bfi44.json missing"}

    items = data["items"]
    norms = data["norms"]
    # Ask ALL 44 items in one call per persona to save API cost
    task = (
        f"Rate each statement 1-5 (1=strongly disagree, 5=strongly agree) about yourself.\n"
        f"Respond JSON like {{\"E01\": 3, \"E02\": 4, ...}} using the IDs below.\n\n"
        + "\n".join(f"{it['id']}: {it['text']}" for it in items)
    )
    raws = _parallel_ask(panel, lambda p, t=task: _ask_persona(p, t, max_tokens=800))

    by_domain: dict[str, list[float]] = defaultdict(list)
    for raw in raws:
        if not raw:
            continue
        cleaned = _JSON_FENCE.sub("", raw.strip()).strip()
        try:
            responses = json.loads(cleaned)
        except (ValueError, TypeError):
            continue
        domain_scores: dict[str, list[float]] = defaultdict(list)
        for it in items:
            v = responses.get(it["id"])
            if not isinstance(v, (int, float)):
                continue
            if it["key"] == "-":
                v = 6 - v  # reverse
            domain_scores[it["domain"]].append(v)
        for d, vals in domain_scores.items():
            if vals:
                by_domain[d].append(sum(vals) / len(vals))

    per_domain = {}
    within_1sd = 0
    for d, norm in norms.items():
        vals = by_domain.get(d, [])
        if not vals:
            per_domain[d] = {"n": 0, "status": "no_data"}
            continue
        mean = sum(vals) / len(vals)
        z = (mean - norm["mean"]) / norm["sd"] if norm["sd"] else 0
        pass_1sd = abs(z) <= 1.0
        if pass_1sd:
            within_1sd += 1
        per_domain[d] = {"n": len(vals), "mean": round(mean, 2), "z": round(z, 2), "within_1sd": pass_1sd}

    frac = within_1sd / len(norms) if norms else 0
    th = THRESHOLDS["bfi44"]
    return {
        "name": "bfi44",
        "status": "ok",
        "metric": th["metric"],
        "value": round(frac, 2),
        "threshold": th["min"],
        "pass": frac >= th["min"],
        "per_domain": per_domain,
    }


# ---------------- Suite: test_retest ----------------

def suite_test_retest(panel: list[dict], question: str | None = None) -> dict:
    q = question or "Do you agree the government should provide more funding for public schools? Answer yes or no."
    task = f"{q}\nRespond JSON: {{\"answer\": \"yes\" or \"no\"}}"

    def _norm(x):
        if isinstance(x, str):
            x = x.strip().lower()
            if x in {"yes", "y", "true", "1", "agree"}:
                return "yes"
            if x in {"no", "n", "false", "0", "disagree"}:
                return "no"
        return None

    def ask_twice(p):
        a1 = _norm(_parse_json_answer(_ask_persona(p, task, max_tokens=80), "answer"))
        a2 = _norm(_parse_json_answer(_ask_persona(p, task, max_tokens=80), "answer"))
        return (a1, a2)

    pairs = _parallel_ask(panel, ask_twice)
    valid = [(a, b) for pair in pairs if pair for a, b in [pair] if a in {"yes", "no"} and b in {"yes", "no"}]
    if len(valid) < max(3, len(panel) // 2):
        return {"name": "test_retest", "status": "failed", "note": f"only {len(valid)}/{len(panel)} valid pairs"}

    # Cohen's kappa
    a1 = [p[0] for p in valid]
    a2 = [p[1] for p in valid]
    po = sum(1 for x, y in zip(a1, a2) if x == y) / len(valid)
    p_yes = (a1.count("yes") + a2.count("yes")) / (2 * len(valid))
    p_no = 1 - p_yes
    pe = p_yes ** 2 + p_no ** 2
    kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0

    th = THRESHOLDS["test_retest"]
    return {
        "name": "test_retest",
        "status": "ok",
        "metric": th["metric"],
        "value": round(kappa, 3),
        "threshold": th["min"],
        "pass": kappa >= th["min"],
        "n_pairs": len(valid),
        "agreement": round(po, 3),
    }


# ---------------- Suite: diversity ----------------

def suite_diversity(panel: list[dict]) -> dict:
    task = (
        "Name one thing you'd change about your country's education system. "
        'Respond JSON: {"change": "<one short phrase>"}'
    )
    raws = _parallel_ask(panel, lambda p, t=task: _ask_persona(p, t))
    answers = [_parse_json_answer(r, "change") for r in raws if r]
    answers = [a.strip().lower() for a in answers if isinstance(a, str) and a.strip()]
    if len(answers) < 5:
        return {"name": "diversity", "status": "failed", "note": f"only {len(answers)} valid answers"}

    c = Counter(answers)
    total = sum(c.values())
    h = -sum((v / total) * math.log2(v / total) for v in c.values())
    h_max = math.log2(len(c)) if len(c) > 1 else 1
    ratio = h / h_max if h_max else 0
    unique_ratio = len(c) / len(answers)

    th = THRESHOLDS["diversity"]
    return {
        "name": "diversity",
        "status": "ok",
        "metric": th["metric"],
        "value": round(ratio, 3),
        "threshold": th["min"],
        "pass": ratio >= th["min"],
        "unique_ratio": round(unique_ratio, 3),
        "n_answers": len(answers),
    }


# ---------------- Suite: demo_corr ----------------

_ATTITUDE_QUESTIONS = {
    "abortion_legal":     "Should abortion be legal in most cases? Answer yes or no.",
    "gun_permit":         "Should people have to get a permit before buying a gun? Answer yes or no.",
    "climate_action":     "Should the government take strong action on climate change? Answer yes or no.",
    "immig_decrease":     "Should immigration to the US be decreased? Answer yes or no.",
    "gun_control":        "Should there be stricter gun control laws? Answer yes or no.",
    "univ_healthcare":    "Should the government provide healthcare for all Americans? Answer yes or no.",
}


def _persona_num(p: dict, var: str) -> float | None:
    """Project persona field to a numeric value for correlation (age/education/income)."""
    v = p.get(var)
    if var == "age" and isinstance(v, (int, float)):
        return float(v)
    if var == "education":
        order = ["primary", "secondary", "some college", "bachelor", "graduate"]
        if isinstance(v, str):
            vl = v.lower()
            for i, lvl in enumerate(order):
                if lvl in vl:
                    return float(i)
        return None
    if var == "income_bracket":
        # Nemotron has no income field — return None and skip this dim.
        return None
    return None


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx2 = sum((x - mx) ** 2 for x in xs)
    dy2 = sum((y - my) ** 2 for y in ys)
    denom = (dx2 * dy2) ** 0.5
    return num / denom if denom > 0 else 0.0


def suite_demo_corr(panel: list[dict]) -> dict:
    data = _load_json(EVAL_DIR / "anes_demo_corr.json")
    if not data:
        return {"name": "demo_corr", "status": "skipped", "note": "eval/anes_demo_corr.json missing"}

    demo_vars = data["demographic_vars"]
    attitude_vars = data["attitude_vars"]
    ref_corr: dict[str, float] = data["correlations"]

    # 1. Ask each persona each attitude question
    attitude_responses: dict[str, list[tuple[int, float]]] = {a: [] for a in attitude_vars}
    # list of (persona_index, 1.0 for yes / 0.0 for no)

    def ask(persona, idx):
        out = {}
        for a in attitude_vars:
            q = _ATTITUDE_QUESTIONS.get(a)
            if not q:
                continue
            task = f"{q}\nRespond JSON: {{\"answer\": \"yes\" or \"no\"}}"
            resp = _ask_persona(persona, task, max_tokens=80)
            ans = _parse_json_answer(resp, "answer")
            if isinstance(ans, str):
                al = ans.strip().lower()
                if al in ("yes", "y"): out[a] = 1.0
                elif al in ("no", "n"): out[a] = 0.0
        return (idx, out)

    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = [ex.submit(ask, p, i) for i, p in enumerate(panel)]
        for f in as_completed(futs):
            try:
                idx, out = f.result()
                for a, v in out.items():
                    attitude_responses[a].append((idx, v))
            except Exception:
                pass

    # 2. For each (demo_var, attitude_var), compute observed Pearson
    observed: dict[str, float] = {}
    skipped_dims = []
    for dv in demo_vars:
        # Build mapping idx -> demo numeric
        demo_map = {}
        for i, p in enumerate(panel):
            v = _persona_num(p, dv)
            if v is not None:
                demo_map[i] = v
        if len(demo_map) < 5:
            skipped_dims.append(dv)
            continue
        for av in attitude_vars:
            pairs = [(demo_map[i], v) for i, v in attitude_responses[av] if i in demo_map]
            if len(pairs) < 5:
                continue
            xs, ys = zip(*pairs)
            r = _pearson(list(xs), list(ys))
            if r is not None:
                observed[f"{dv}__{av}"] = r

    # 3. Frobenius distance vs reference (only over keys both present)
    common = [k for k in ref_corr if k in observed]
    if not common:
        return {"name": "demo_corr", "status": "failed",
                "note": f"no overlapping demo×attitude pairs; skipped: {skipped_dims}"}
    frob = (sum((observed[k] - ref_corr[k]) ** 2 for k in common)) ** 0.5
    th = THRESHOLDS["demo_corr"]
    return {
        "name": "demo_corr",
        "status": "ok",
        "metric": th["metric"],
        "value": round(frob, 3),
        "threshold": th["max"],
        "pass": frob <= th["max"],
        "n_pairs": len(common),
        "skipped_demo_dims": skipped_dims,
        "observed_sample": {k: round(observed[k], 3) for k in common[:5]},
        "reference_sample": {k: ref_corr[k] for k in common[:5]},
    }


# ---------------- Suite: bias_audit ----------------

def suite_bias_audit(panel: list[dict]) -> dict:
    """Wraps lib/bias_audit.run_audit. Passes if audit completes; interpretation lives in the report."""
    from lib.bias_audit import run_audit
    raw = run_audit(panel, suites=("framing", "acquiescence", "order", "authority"))
    # Summarize: count how many probes revealed < 50% of human-typical magnitude (calibration warnings).
    warnings = 0
    details = {}
    f = raw.get("framing")
    if isinstance(f, dict) and "shift_ratio" in f:
        details["framing_shift_ratio"] = f["shift_ratio"]
        if f["shift_ratio"] < 0.5:
            warnings += 1
    a = raw.get("acquiescence")
    if isinstance(a, dict) and "value" in a:
        details["acquiescence_excess"] = a["value"]
        if abs(a["value"]) < 0.05:
            warnings += 1
    o = raw.get("order")
    if isinstance(o, dict) and "value" in o:
        details["order_tv_distance"] = o["value"]
        if o["value"] < 0.03:
            warnings += 1
    au = raw.get("authority")
    if isinstance(au, dict) and "value" in au:
        details["authority_shift"] = au["value"]
        if au["value"] < 0.05:
            warnings += 1
    return {
        "name": "bias_audit",
        "status": "ok",
        "metric": "calibration_warnings",
        "value": warnings,
        "threshold": 2,  # pass if <2 biases are absent (i.e. personas behave more human-like)
        "pass": warnings < 2,
        "interpretation": "more warnings = more LLM-typical absence of human biases. "
                          "High warnings count → don't use this panel as a substitute for real surveys.",
        "details": details,
        "warning": raw["warning"],
    }


SUITES = {
    "gss_20q":     suite_gss_20q,
    "bfi44":       suite_bfi44,
    "test_retest": suite_test_retest,
    "diversity":   suite_diversity,
    "demo_corr":   suite_demo_corr,
    "bias_audit":  suite_bias_audit,
}


def run(suites: list[str], panel_n: int, source: str, seed: int) -> dict:
    print(f"Sampling panel of {panel_n} from {source}...", file=sys.stderr)
    panel = sampler.sample_personas(n=panel_n, source=source, mode="stream", seed=seed)
    print(f"Got {len(panel)} personas. Running {len(suites)} suite(s)...", file=sys.stderr)
    results = []
    for s in suites:
        print(f"  → {s}", file=sys.stderr)
        results.append(SUITES[s](panel))

    # Overall score: fraction of non-skipped suites that pass
    active = [r for r in results if r.get("status") == "ok"]
    passed = [r for r in active if r.get("pass")]
    overall = len(passed) / len(active) if active else 0.0

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "panel": {"n": len(panel), "source": source, "seed": seed},
        "overall_score": round(overall, 2),
        "suites_active": len(active),
        "suites_passed": len(passed),
        "results": results,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--suite", default="gss_20q,bfi44,test_retest,diversity,demo_corr")
    p.add_argument("--n", type=int, default=30)
    p.add_argument("--source", default="nemotron_usa")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", default=None)
    args = p.parse_args()

    report = run(args.suite.split(","), args.n, args.source, args.seed)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = Path(args.out) if args.out else REPORT_DIR / f"score_card_{datetime.utcnow():%Y%m%d_%H%M%S}.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n=== Overall: {report['overall_score']} ({report['suites_passed']}/{report['suites_active']} suites passed) ===")
    for r in report["results"]:
        mark = "✓" if r.get("pass") else ("—" if r.get("status") != "ok" else "✗")
        val = r.get("value", "?")
        th = r.get("threshold", "?")
        print(f"  {mark} {r['name']:12s}  {r.get('status'):8s}  {r.get('metric', ''):30s} {val} (threshold {th})")
    print(f"\n→ {out}")


if __name__ == "__main__":
    main()
