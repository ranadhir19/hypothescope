#!/usr/bin/env python3
"""hypothescope repo harness: structural checks + the frozen self-test
set + an end-to-end run of the worked example. Exit 0 only when
everything passes.

    python3 validate.py
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
PKG = "hypothescope"


def structural_checks():
    problems = []
    for rel in ["README.md", "LICENSE", "NAME_CHECK.md", "COMPLIANCE.md",
                os.path.join(PKG, "__init__.py"),
                os.path.join(PKG, "__main__.py"),
                os.path.join(PKG, "cli.py"),
                os.path.join(PKG, "profile.py"),
                os.path.join(PKG, "generate.py"),
                os.path.join(PKG, "probes.py"),
                os.path.join(PKG, "ledger.py"),
                os.path.join("selftests", "tests.py"),
                os.path.join("examples", "sample_profile.json"),
                os.path.join("examples", "artifacts", "results.json"),
                os.path.join("examples", "artifacts", "pairs.csv")]:
        if not os.path.isfile(os.path.join(ROOT, rel)):
            problems.append(f"missing {rel}")
    return problems


def run(cmd, cwd):
    proc = subprocess.run([sys.executable] + cmd, cwd=cwd,
                          capture_output=True, text=True, timeout=300)
    return proc.returncode, (proc.stdout + proc.stderr)


def main():
    failures = []

    print("== structural checks ==")
    problems = structural_checks()
    if problems:
        for p in problems:
            print("  MISSING:", p)
        failures.extend(problems)
    else:
        print("  all required files present")

    print("\n== frozen self-test set ==")
    rc, out = run([os.path.join(ROOT, "selftests", "tests.py")], ROOT)
    for ln in out.strip().splitlines():
        print("  " + ln)
    if rc != 0:
        failures.append("selftests")

    print("\n== worked example (end to end) ==")
    with tempfile.TemporaryDirectory() as tmp:
        prefix = os.path.join(tmp, "sample")
        rc, out = run(["-m", PKG, "test",
                       os.path.join(ROOT, "examples", "sample_profile.json"),
                       "--out", prefix], ROOT)
        print("  " + out.strip().splitlines()[-1] if out.strip() else "  (no output)")
        if rc != 0:
            failures.append("example run")
        else:
            with open(prefix + ".ledger.json", encoding="utf-8") as fh:
                ledger = json.load(fh)
            counts = ledger["counts"]
            expected = {"TESTED-SUPPORTED": 5, "TESTED-REFUTED": 0,
                        "UNTESTED": 2}
            if counts == expected:
                print(f"  example ledger verdicts as expected: {counts}")
            else:
                print(f"  example ledger verdicts {counts} != expected {expected}")
                failures.append("example verdicts")

    print("\n== summary ==")
    if failures:
        print(f"FAIL: {len(failures)} problem(s): {failures}")
        return 1
    print("PASS: structure OK, self-tests green, worked example reproduces.")
    print("Coverage (honest): unit-level checks of profile validation, the "
          "eight probe kinds used by the self-tests and example, verdict "
          "stamping, and the CLI end to end. The generator's templates are "
          "exercised on miniature profiles only; no claim is made about "
          "hypothesis quality on real papers - that is what the ledger's "
          "UNTESTED verdicts are for.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
