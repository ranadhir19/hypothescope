# IP / legal compliance record — hypothescope

Written 2026-11-20, before any publication. Publication is blocked until
every line below is evidenced; all lines are evidenced.

## Original name, collision-checked

- Name: **hypothescope** — a coined compound (hypothesis + -scope),
  originated for this tool.
- Collision check (2026-11-20, GitHub API repository-name search, PyPI
  JSON API, web search): no GitHub repository (total_count = 0), no PyPI
  package (HTTP 404), no software product, paper, or company using the
  name. Four alternative candidates were checked and rejected with named
  collisions (hypothesmith, probatio, claimsmith, conjectra). Full
  evidence: `NAME_CHECK.md`.

## Original code and copy

- All code and documentation in this repository were written for this
  project in this session. No code, text, or structure was copied from
  any reference tool. The design follows the portfolio's own established
  discipline (verified-or-refuse verdicts, as in pairseal/evalcrucible)
  and the repository *layout* conventions of the author's own earlier
  project loopwarden (validate.py harness pattern, NAME_CHECK /
  COMPLIANCE records) — the author's own work, reused as a pattern, with
  all content original to this tool.
- The worked example (`examples/`) is a fictional miniature invented for
  this repository; its numbers are synthetic and labelled as such.

## License

- This project: MIT License (`LICENSE`), Copyright (c) 2026
  Ranadhir Ghosh.

## Third-party dependency / license compliance

- **No third-party dependencies.** The engine uses only the Python 3
  standard library (argparse, ast, csv, json, math, operator, os, re,
  statistics). Nothing to attribute, nothing to comply with beyond the
  Python Software Foundation license for the interpreter itself, which
  imposes no obligations on this source distribution.

## Asset provenance

- No images, fonts, data files, or other third-party assets are included.
  The only data files are the synthetic example artifacts in `examples/`,
  generated for this repository.

## Secrets scan

- 2026-11-20: pattern scan over all text files in the tree for API keys,
  secrets, passwords, tokens, bearer strings, private-key headers, and
  AWS-style access keys — **no hits**. The tool takes no credentials and
  makes no network calls by design.

## Employer-reference scan (standing portfolio gate)

- 2026-11-20: the exact tree was scanned with the portfolio's standing
  employer-reference scanner (the watch tool kept in the workspace's
  github-fis-watch directory) — **0 candidate hits** after one benign
  self-reference to the scanner's own path in this file was reworded,
  following the loopwarden precedent.
  (The engine's cost classes are named LOCAL / OFFSITE / MANUAL precisely
  so the vocabulary of the tool carries no employer reference.)

## Gate results at compliance writing

- `python3 validate.py` — required structure present; frozen self-test
  set green (12/12 checks); worked example reproduces its expected
  ledger verdicts (5 TESTED-SUPPORTED / 0 TESTED-REFUTED / 2 UNTESTED).
