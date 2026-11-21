#!/usr/bin/env python3
"""Frozen self-test set for hypothescope.

Builds miniature profiles with PLANTED defects and checks the engine's
verdicts exactly:

  1. an inconsistent quoted number      -> TESTED-REFUTED
  2. a claim with a missing artifact    -> UNTESTED (ARTIFACT_MISSING),
                                           never TESTED-SUPPORTED
  3. a refutable tightening hypothesis  -> TESTED-REFUTED
  4. a sound tightening hypothesis      -> TESTED-SUPPORTED
  5. OFFSITE / MANUAL hypotheses        -> UNTESTED with reason codes,
                                           deciding tests preserved
  6. generation is deterministic

Run: python3 selftests/tests.py   (exit 0 = all pass)
"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from hypothescope.generate import generate          # noqa: E402
from hypothescope.ledger import test_profile         # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def write(d, name, obj):
    path = os.path.join(d, name)
    with open(path, "w", encoding="utf-8") as fh:
        if isinstance(obj, str):
            fh.write(obj)
        else:
            json.dump(obj, fh)
    return path


def by_id(ledger, hid):
    for e in ledger["entries"]:
        if e["id"] == hid:
            return e
    raise AssertionError(f"no ledger entry {hid}")


def main():
    tmp = tempfile.mkdtemp(prefix="hypothescope-selftest-")

    # ---- shared artifacts -------------------------------------------------
    write(tmp, "results.json", {"proved_region": 0.62, "frontier": 7.14})
    write(tmp, "pairs_bad.csv",
          "estimate,truth\n0.10,0.90\n0.20,0.85\n0.15,0.80\n")
    write(tmp, "pairs_good.csv",
          "estimate,truth\n0.80,0.90\n0.70,0.85\n0.75,0.80\n0.82,0.88\n")

    base = {
        "paper_id": "selftest",
        "title": "Self-test miniature",
        "venue": "Nowhere",
        "base_dir": tmp,
        "gate_scores": {"quality": 5.0, "bar": 8.0},
        "claims": [],
        "blockers": [],
        "numbers": [],
    }

    # ---- 1. inconsistent quoted number ------------------------------------
    p = dict(base)
    p["numbers"] = [{
        "id": "proved", "label": "proved region", "value": 0.44, "tol": 0.005,
        "artifact": {"kind": "json_value", "path": "results.json",
                     "key": "proved_region"},
    }]
    entry = by_id(test_profile(p), "selftest-NUM-proved")
    check("inconsistent number is TESTED-REFUTED",
          entry["verdict"] == "TESTED-REFUTED", entry["verdict"])

    # consistent number, for contrast
    p["numbers"][0]["value"] = 0.62
    entry = by_id(test_profile(p), "selftest-NUM-proved")
    check("consistent number is TESTED-SUPPORTED",
          entry["verdict"] == "TESTED-SUPPORTED", entry["verdict"])

    # ---- 1b. dotted keys containing dots -----------------------------------
    write(tmp, "dotted.json", {"a0.85_c0.1": {"err_pct": {"mean": 164.27}},
                               "tau3": {"0.05": {"full": 0.0078}}})
    p = dict(base)
    p["numbers"] = [{
        "id": "dotted", "label": "dotted key", "value": 164.27, "tol": 0.01,
        "artifact": {"kind": "json_value", "path": "dotted.json",
                     "key": "a0.85_c0.1.err_pct.mean"},
    }, {
        "id": "dotted2", "label": "numeric dotted key", "value": 0.0078,
        "tol": 0.0001,
        "artifact": {"kind": "json_value", "path": "dotted.json",
                     "key": "tau3.0.05.full"},
    }]
    ledger = test_profile(p)
    check("keys containing dots resolve (a0.85_c0.1)",
          by_id(ledger, "selftest-NUM-dotted")["verdict"] == "TESTED-SUPPORTED")
    check("keys containing dots resolve (0.05)",
          by_id(ledger, "selftest-NUM-dotted2")["verdict"] == "TESTED-SUPPORTED")

    # ---- 2. unsupported claim (missing evidence artifact) ------------------
    p = dict(base)
    p["claims"] = [{
        "id": "C1", "statement": "A claim whose artifact does not exist.",
        "evidence": ["no_such_artifact.json"],
    }]
    ledger = test_profile(p)
    ev = [e for e in ledger["entries"] if e["id"].startswith("selftest-EV-C1")]
    check("missing-evidence entry exists", len(ev) == 1, str(len(ev)))
    if ev:
        check("missing evidence is UNTESTED / ARTIFACT_MISSING",
              ev[0]["verdict"] == "UNTESTED"
              and ev[0]["reason_code"] == "ARTIFACT_MISSING",
              f"{ev[0]['verdict']} / {ev[0]['reason_code']}")
    check("no entry for the unsupported claim is SUPPORTED",
          all(e["verdict"] != "TESTED-SUPPORTED" for e in ledger["entries"]))

    # ---- 3 + 4. tightening hypotheses --------------------------------------
    def factor_blocker(path):
        return [{
            "id": "B1", "kind": "bound_gap",
            "hypothesis": "A calibration factor reaches 90% coverage.",
            "predicted_effect": 0.5,
            "test": {"kind": "factor_search", "path": path,
                     "value_column": "estimate", "target_column": "truth",
                     "factors": [1.2, 1.5, 1.8, 2.0],
                     "coverage_target": 0.9, "max_median_ratio": 2.0},
        }]

    p = dict(base)
    p["blockers"] = factor_blocker("pairs_bad.csv")
    entry = by_id(test_profile(p), "selftest-B1")
    check("refutable tightening is TESTED-REFUTED",
          entry["verdict"] == "TESTED-REFUTED", entry["verdict"])

    p["blockers"] = factor_blocker("pairs_good.csv")
    entry = by_id(test_profile(p), "selftest-B1")
    check("sound tightening is TESTED-SUPPORTED",
          entry["verdict"] == "TESTED-SUPPORTED", entry["verdict"])

    # ---- 5. untestable hypotheses stay UNTESTED -----------------------------
    p = dict(base)
    p["blockers"] = [
        {"id": "B2", "kind": "evidence_class",
         "hypothesis": "A real-system run changes the evidence class.",
         "predicted_effect": 1.0,
         "external": {"cost_class": "OFFSITE",
                      "deciding_test": "Run the named real-system evaluation."}},
        {"id": "B3", "kind": "novelty",
         "hypothesis": "A literature delta reframes novelty.",
         "predicted_effect": 0.3,
         "deciding_test": "Read the two nearest prior works."},
    ]
    ledger = test_profile(p)
    e2 = by_id(ledger, "selftest-B2")
    e3 = by_id(ledger, "selftest-B3")
    check("OFFSITE hypothesis is UNTESTED / COST_OFFSITE with deciding test",
          e2["verdict"] == "UNTESTED" and e2["reason_code"] == "COST_OFFSITE"
          and "real-system" in e2["deciding_test"],
          f"{e2['verdict']} / {e2['reason_code']}")
    check("MANUAL hypothesis is UNTESTED / COST_MANUAL",
          e3["verdict"] == "UNTESTED" and e3["reason_code"] == "COST_MANUAL",
          f"{e3['verdict']} / {e3['reason_code']}")

    # ---- 6. determinism ------------------------------------------------------
    g1 = json.dumps(generate(p), sort_keys=True)
    g2 = json.dumps(generate(p), sort_keys=True)
    check("generation is deterministic", g1 == g2)

    print()
    if FAILURES:
        print(f"SELF-TESTS FAILED: {len(FAILURES)}: {FAILURES}")
        return 1
    print("SELF-TESTS PASSED: planted defects caught (inconsistent number, "
          "unsupported claim, refutable tightening); sound tightening "
          "supported; untestable hypotheses refused, never promoted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
