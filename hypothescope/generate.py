"""Deterministic hypothesis generation for hypothescope.

The generator is a set of templates keyed by blocker kind and profile
structure. It is deliberately NOT a language model: the same profile always
produces the same hypotheses, each carrying the deciding test that would
settle it, a predicted effect, a cost class, and a pre-registered kill
criterion. Generation never asserts truth - a hypothesis enters the ledger
as UNTESTED until the testing engine runs its deciding test.

Hypothesis classes:
  CLAIM-TIGHTENING    a bound/result can be strengthened by a named route
  EVIDENCE-LIFT       a named experiment/dataset changes the evidence class
  POSITIONING         a prior-art delta reframes the novelty claim
  FALSIFICATION-PROBE the cheapest test that could kill the headline claim
  CONSISTENCY         internal numbers/statements that must agree
"""
from .profile import COST_CLASSES

_KIND_TO_CLASS = {
    "bound_gap": "CLAIM-TIGHTENING",
    "evidence_class": "EVIDENCE-LIFT",
    "novelty": "POSITIONING",
    "consistency_defect": "CONSISTENCY",
    "missing_analysis": "EVIDENCE-LIFT",
    "missing_definition": "CONSISTENCY",
    "reproducibility": "CONSISTENCY",
    "other": "FALSIFICATION-PROBE",
}


def _hyp(hid, cls, statement, target, effect, test, cost, kill, deciding):
    return {
        "id": hid,
        "class": cls,
        "statement": statement,
        "target": target,
        "predicted_effect": effect,
        "test": test,
        "cost_class": cost,
        "kill_criterion": kill,
        "deciding_test": deciding,
    }


def generate(profile):
    """Return the full hypothesis list for a profile (deterministic order)."""
    hyps = []
    pid = profile["paper_id"]

    # 1. Explicit hypotheses authored in the profile come first, verbatim.
    for i, hyp in enumerate(profile.get("hypotheses", [])):
        merged = {
            "id": hyp.get("id", f"{pid}-X{i + 1}"),
            "class": hyp["class"],
            "statement": hyp["statement"],
            "target": hyp.get("target", ""),
            "predicted_effect": float(hyp.get("predicted_effect", 0.0)),
            "test": hyp.get("test"),
            "cost_class": hyp.get("cost_class", "LOCAL" if hyp.get("test") else "MANUAL"),
            "kill_criterion": hyp.get("kill_criterion", ""),
            "deciding_test": hyp.get("deciding_test", ""),
        }
        if merged["cost_class"] not in COST_CLASSES:
            merged["cost_class"] = "MANUAL"
        hyps.append(merged)

    # 2. One hypothesis per blocker, class from the blocker kind.
    for blocker in profile.get("blockers", []):
        cls = _KIND_TO_CLASS[blocker["kind"]]
        test = blocker.get("test")
        external = blocker.get("external")
        if test:
            cost = "LOCAL"
            deciding = blocker.get("deciding_test", "run the attached local probe")
        elif external:
            cost = external.get("cost_class", "OFFSITE")
            deciding = external.get("deciding_test", "")
        else:
            cost = "MANUAL"
            deciding = blocker.get("deciding_test", "")
        hyps.append(_hyp(
            f"{pid}-{blocker['id']}",
            cls,
            blocker["hypothesis"],
            blocker.get("target", blocker["id"]),
            float(blocker.get("predicted_effect", 0.0)),
            test,
            cost,
            blocker.get("kill_criterion", ""),
            deciding,
        ))

    # 3. CONSISTENCY: every quoted number must recompute from its artifact.
    for num in profile.get("numbers", []):
        artifact = num["artifact"]
        test = dict(artifact)
        test["expect"] = num["value"]
        if "tol" in num:
            test["tol"] = num["tol"]
        hyps.append(_hyp(
            f"{pid}-NUM-{num['id']}",
            "CONSISTENCY",
            f"Quoted number '{num['label']}' = {num['value']} recomputes from "
            f"its artifact ({artifact.get('path')}).",
            f"number:{num['id']}",
            0.1,
            test,
            "LOCAL",
            "Refuted if the artifact value differs beyond tolerance - the "
            "manuscript number is then wrong or the artifact is stale.",
            "recompute the quoted number from its artifact",
        ))

    # 4. FALSIFICATION-PROBE: one per claim that carries a falsify_test.
    for claim in profile.get("claims", []):
        if claim.get("falsify_test"):
            hyps.append(_hyp(
                f"{pid}-FALS-{claim['id']}",
                "FALSIFICATION-PROBE",
                f"Headline claim {claim['id']} survives its cheapest local "
                f"falsification probe.",
                f"claim:{claim['id']}",
                0.2,
                claim["falsify_test"],
                "LOCAL",
                "Refuted if the probe fails - the headline claim does not "
                "survive its own cheapest check and must be weakened.",
                "run the claim's attached falsification probe",
            ))
        # A claim whose evidence pointer does not resolve can never be
        # marked supported; generation records the check explicitly.
        for j, ev in enumerate(claim.get("evidence", [])):
            hyps.append(_hyp(
                f"{pid}-EV-{claim['id']}-{j + 1}",
                "CONSISTENCY",
                f"Evidence artifact for claim {claim['id']} exists: {ev}.",
                f"claim:{claim['id']}",
                0.0,
                {"kind": "text_check", "path": ev, "pattern": ".",
                 "expect": "present"},
                "LOCAL",
                "Untestable-as-supported if the artifact is missing - the "
                "claim's evidence pointer is dangling.",
                "check the evidence artifact exists",
            ))

    return hyps
