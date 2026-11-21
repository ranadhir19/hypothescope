# Name check — hypothesis generation + testing tool

Checked 2026-11-20 via the GitHub API (repository name search), the PyPI
JSON API, and web search.

## Candidates checked and rejected

- `hypothesmith` — REJECTED (collision). A real, maintained library:
  `Zac-HD/hypothesmith` on GitHub ("Hypothesis strategies for generating
  Python programs, something like CSmith"), published on PyPI as
  `hypothesmith` (HTTP 200) with a conda-forge feedstock. Same name, same
  ecosystem, adjacent subject (hypothesis-based testing).
- `probatio` — REJECTED (heavy collision). PyPI `probatio` (HTTP 200) is a
  maintained data-validation library by Franck Nijhof, with GitHub repos
  `frenck/probatio` and `probatio/probatio`. The name is also carried by
  several commercial products: a test-automation framework (Gateway
  Digital), forensic evidence software (Acquisizioni Forensi), an exam
  generator (probatio.ai), and a pytest plugin (`probatio-llm` on PyPI).
- `claimsmith` — REJECTED (collision). No PyPI package, but the exact name
  is a live commercial product twice over: MSOFT's "Claimsmith", an
  AI examiner assistant for insurance claims (msoftclaims.net), and
  Dealer Revenue Group's "ClaimSmith™" co-op claims service; also
  `Suryaveer09/Claimsmith` on GitHub and CLAIMSMITH GROUP, LLC in the
  Florida corporate registry.
- `conjectra` — checked, clean but not chosen. PyPI 404 and zero GitHub
  repositories with the name; web hits are only the Latin etymology of
  "conjecture" (conjectra, "a throwing together"). It was passed over
  because it is an attested Latin word rather than a coined name, and sits
  one syllable from "Conjecture Pro" (conjecture.pro), an AI
  scientific-reasoning product in an adjacent space.

## Chosen name: `hypothescope`

Exact-string checks on 2026-11-20 returned **no GitHub repository**
(repository name search total_count = 0), **no PyPI package** (HTTP 404),
and **no software product, paper, or company** using the name. Near names
are different names in different fields: HypOS (hypos.app, a research
notebook), Hodoscope (an AI-agent monitoring tool) — neither is
"hypothescope".

`hypothescope` is a coined compound in the portfolio's style (runreckon,
evalcrucible, pairseal, verdictpack, loopwarden): *hypothesis* + *-scope*,
an instrument for examining — a scope you point at a paper's improvement
hypotheses to see which ones survive testing. Final repo name:
**hypothescope**. Local build dir: `~/workspace/hypothescope/`.
