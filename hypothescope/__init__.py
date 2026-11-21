"""hypothescope - a hypothesis generation + testing engine for
research-paper improvement.

Given a paper's structured profile and its known blockers, hypothescope
generates improvement hypotheses across five classes and tests the ones
that are locally testable, emitting a ledger in which every hypothesis is
TESTED-SUPPORTED, TESTED-REFUTED, or UNTESTED with a reason code and the
exact deciding test named. Untested hypotheses are never asserted as true.
"""

__version__ = "0.1.0"
