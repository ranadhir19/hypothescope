"""The testing engine and ledger for hypothescope.

The engine runs every LOCAL hypothesis's deciding test and stamps the
ledger. The discipline is the point:

  TESTED-SUPPORTED  the deciding test ran locally and passed
  TESTED-REFUTED    the deciding test ran locally and failed
  UNTESTED          the deciding test did not run - a reason code says why
                    (NO_LOCAL_TEST, COST_OFFSITE, COST_MANUAL,
                    ARTIFACT_MISSING, PROBE_ERROR)

An untested hypothesis is NEVER promoted: no score, summary, or report
produced by this tool may describe an UNTESTED hypothesis as true.
"""
from . import probes
from .generate import generate

COST_WEIGHT = {"LOCAL": 1.0, "MANUAL": 3.0, "OFFSITE": 5.0}

VERDICT_SUPPORTED = "TESTED-SUPPORTED"
VERDICT_REFUTED = "TESTED-REFUTED"
VERDICT_UNTESTED = "UNTESTED"


def test_profile(profile):
    """Generate hypotheses for a profile and test the locally testable ones.
    Returns the ledger dict."""
    entries = []
    for hyp in generate(profile):
        entry = dict(hyp)
        entry["verdict"] = VERDICT_UNTESTED
        entry["reason_code"] = None
        entry["test_detail"] = None
        spec = hyp.get("test")
        if hyp["cost_class"] != "LOCAL":
            entry["reason_code"] = f"COST_{hyp['cost_class']}"
        elif not spec:
            entry["reason_code"] = "NO_LOCAL_TEST"
        else:
            try:
                passed, detail = probes.run_probe(profile, spec)
                entry["test_detail"] = detail
                entry["verdict"] = VERDICT_SUPPORTED if passed else VERDICT_REFUTED
            except probes.ProbeError as exc:
                msg = str(exc)
                entry["test_detail"] = msg
                entry["reason_code"] = (
                    "ARTIFACT_MISSING" if "missing" in msg else "PROBE_ERROR")
        entry["rank_score"] = round(
            float(hyp.get("predicted_effect", 0.0)) /
            COST_WEIGHT[hyp["cost_class"]], 4)
        entries.append(entry)
    entries.sort(key=lambda e: (-e["rank_score"], e["id"]))
    counts = {v: 0 for v in (VERDICT_SUPPORTED, VERDICT_REFUTED, VERDICT_UNTESTED)}
    for e in entries:
        counts[e["verdict"]] += 1
    return {
        "paper_id": profile["paper_id"],
        "title": profile["title"],
        "venue": profile["venue"],
        "gate_scores": profile.get("gate_scores", {}),
        "counts": counts,
        "entries": entries,
    }


def render_markdown(ledger):
    lines = []
    lines.append(f"# Hypothesis ledger - {ledger['paper_id']}")
    lines.append("")
    lines.append(f"**Paper:** {ledger['title']}  ")
    lines.append(f"**Venue:** {ledger['venue']}  ")
    gs = ledger.get("gate_scores") or {}
    if gs:
        lines.append(f"**Gate scores:** {gs}  ")
    c = ledger["counts"]
    lines.append(f"**Verdicts:** {c[VERDICT_SUPPORTED]} tested-supported, "
                 f"{c[VERDICT_REFUTED]} tested-refuted, "
                 f"{c[VERDICT_UNTESTED]} untested")
    lines.append("")
    lines.append("Ranked by predicted effect / cost. UNTESTED hypotheses are "
                 "recorded with the exact deciding test that would settle "
                 "them; they are not claims.")
    lines.append("")
    lines.append("| # | ID | Class | Verdict | Reason | Effect | Cost | Hypothesis |")
    lines.append("|---|----|-------|---------|--------|--------|------|------------|")
    for i, e in enumerate(ledger["entries"], 1):
        stmt = e["statement"].replace("|", "/")
        if len(stmt) > 140:
            stmt = stmt[:137] + "..."
        lines.append(f"| {i} | {e['id']} | {e['class']} | {e['verdict']} | "
                     f"{e['reason_code'] or '-'} | {e['predicted_effect']} | "
                     f"{e['cost_class']} | {stmt} |")
    lines.append("")
    for e in ledger["entries"]:
        lines.append(f"## {e['id']} - {e['class']} - {e['verdict']}")
        lines.append("")
        lines.append(f"- Statement: {e['statement']}")
        lines.append(f"- Target: {e['target']}")
        lines.append(f"- Predicted effect: {e['predicted_effect']} "
                     f"(cost {e['cost_class']}, rank score {e['rank_score']})")
        if e["kill_criterion"]:
            lines.append(f"- Kill criterion (pre-registered): {e['kill_criterion']}")
        if e["verdict"] == VERDICT_UNTESTED:
            lines.append(f"- Reason untested: {e['reason_code']}")
            lines.append(f"- Deciding test: {e['deciding_test']}")
        if e.get("test_detail"):
            lines.append(f"- Test detail: {e['test_detail']}")
        lines.append("")
    return "\n".join(lines)
