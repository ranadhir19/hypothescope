# hypothescope

**A hypothesis generation + testing engine for research-paper improvement.**

Give hypothescope a paper's structured profile — its claims, its gate
scores, its known blockers, and the numbers it quotes, each tied to the
artifact that produced it — and it does two things:

1. **Generates** improvement hypotheses, deterministically, across five
   classes: CLAIM-TIGHTENING, EVIDENCE-LIFT, POSITIONING,
   FALSIFICATION-PROBE, and CONSISTENCY. Every hypothesis carries a
   statement, a target, a predicted effect, a cost class
   (LOCAL / OFFSITE / MANUAL), a pre-registered kill criterion, and the
   exact deciding test that would settle it.
2. **Tests** the hypotheses that are locally testable — recomputing quoted
   numbers from their artifacts, running bounded numeric probes (bound
   re-derivations, calibration-factor searches, Monte-Carlo-free
   consistency checks), and cross-checking statements against data — and
   emits a **ledger** in which every hypothesis is stamped:

   - `TESTED-SUPPORTED` — the deciding test ran locally and passed
   - `TESTED-REFUTED` — the deciding test ran locally and failed
   - `UNTESTED` — the deciding test did not run, with a reason code
     (`NO_LOCAL_TEST`, `COST_OFFSITE`, `COST_MANUAL`, `ARTIFACT_MISSING`,
     `PROBE_ERROR`) and the deciding test named precisely enough to become
     a run-spec

An untested hypothesis is **never** asserted as true. That is the design:
the same verified-or-refuse discipline as the rest of this portfolio
(pairseal's agree-or-refuse extraction, evalcrucible's graded verdicts),
applied to research strategy. An improvement loop driven by a
hypothescope ledger cannot quietly promote a guess into a plan — every
line is either evidence or a labelled, priced, named test.

## Quickstart

No installs, no API keys, no network. Pure Python 3 standard library.

```bash
# run the frozen self-test set + the worked example
python3 validate.py

# generate hypotheses for the worked example paper
python3 -m hypothescope generate examples/sample_profile.json

# test them and write sample-paper.ledger.json / sample-paper.ledger.md
python3 -m hypothescope test examples/sample_profile.json --out sample-paper

# re-render the Markdown report from a saved ledger
python3 -m hypothescope report sample-paper.ledger.json
```

## The profile

A profile is one JSON file per paper:

- `paper_id`, `title`, `venue`, optional `base_dir` (artifact paths
  resolve against it; default: the profile's own directory)
- `gate_scores` — e.g. the current quality score, the bar, the ceiling
- `claims[]` — each with `evidence` artifact pointers and an optional
  `falsify_test`, the cheapest local probe that could kill the claim
- `blockers[]` — each with a `kind` (`bound_gap`, `evidence_class`,
  `novelty`, `consistency_defect`, `missing_analysis`,
  `missing_definition`, `reproducibility`, `other`), a `hypothesis`
  statement, a predicted effect, and either a local `test` or an
  `external` deciding test with its cost class
- `numbers[]` — every quoted number with the artifact spec that
  recomputes it (the generator turns each into a CONSISTENCY hypothesis)
- `hypotheses[]` — optional hand-authored hypotheses, taken verbatim

Local tests are declarative probes, never code from the profile:
`json_value`, `json_compare`, `csv_stat`, `csv_count`, `expr` (bounded
arithmetic over artifact-bound values), `factor_search` (smallest
calibration factor reaching a coverage target, with a median-ratio
ceiling), `text_check`, `text_count`. See `hypothescope/probes.py`.

## How the ledger disciplines an improvement loop

Run hypothescope before spending effort on a paper. Work the ledger from
the top (it is ranked by predicted effect ÷ cost). A TESTED-REFUTED
hypothesis closes a route cheaply and permanently — the kill criterion was
registered before the test ran. An UNTESTED hypothesis is a shopping list
of exactly-named experiments, each already priced by cost class; when one
runs elsewhere, its result re-enters the ledger as evidence. What the
ledger will not do is let "we believe this would help" stand in for a
test.

## Scope and honest limitations

- v1 generates hypotheses from **templates keyed to blocker kinds**, not
  from reading the manuscript. Hypothesis *quality* is bounded by the
  quality of the profile: garbage blockers in, generic hypotheses out.
  The ledger's job is to keep verdicts honest, not to make the generator
  wise.
- Local probes recompute and cross-check; they do not re-run a paper's
  full experiments, train models, or read PDFs. Evidence-class lifts
  (real data, real systems, GPU runs) are OFFSITE by construction and are
  recorded UNTESTED with their deciding tests.
- Predicted effects are the profile author's estimates, used only for
  ranking. A high rank is not evidence.
- The engine never modifies the paper, the profile, or any artifact. It
  reads, computes, and reports.

## Layout

```
hypothescope/     the engine (profile, generate, probes, ledger, cli)
examples/         a worked miniature paper, profile + artifacts
selftests/        the frozen self-test set (planted defects, exact verdicts)
validate.py       repo harness: structure + self-tests + worked example
NAME_CHECK.md     the name collision record
COMPLIANCE.md     IP/legal compliance record
LICENSE           MIT
```

## License

MIT — see `LICENSE`.
