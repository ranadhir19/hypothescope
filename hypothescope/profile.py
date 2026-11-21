"""Profile loading and validation for hypothescope.

A paper profile is a JSON document describing one paper: its claims with
evidence pointers, its gate scores, its known blockers, and the numbers it
quotes (each tied to the artifact that produced it). Profiles are data, not
code: the engine never executes anything a profile names except the bounded
test specifications defined in probes.py.
"""
import json
import os

REQUIRED_KEYS = ("paper_id", "title", "venue")
BLOCKER_KINDS = (
    "bound_gap",
    "evidence_class",
    "novelty",
    "consistency_defect",
    "missing_analysis",
    "missing_definition",
    "reproducibility",
    "other",
)
COST_CLASSES = ("LOCAL", "OFFSITE", "MANUAL")


class ProfileError(ValueError):
    pass


def load_profile(path):
    with open(path, "r", encoding="utf-8") as fh:
        profile = json.load(fh)
    validate_profile(profile)
    if "base_dir" not in profile:
        profile["base_dir"] = os.path.dirname(os.path.abspath(path))
    return profile


def validate_profile(profile):
    for key in REQUIRED_KEYS:
        if key not in profile:
            raise ProfileError(f"profile missing required key: {key}")
    for blocker in profile.get("blockers", []):
        if blocker.get("kind") not in BLOCKER_KINDS:
            raise ProfileError(
                f"blocker {blocker.get('id')!r} has unknown kind "
                f"{blocker.get('kind')!r}; expected one of {BLOCKER_KINDS}")
    for hyp in profile.get("hypotheses", []):
        if hyp.get("cost_class", "LOCAL") not in COST_CLASSES:
            raise ProfileError(
                f"hypothesis {hyp.get('id')!r} has unknown cost_class "
                f"{hyp.get('cost_class')!r}")
    return True


def resolve(profile, relpath):
    """Resolve an artifact path against the profile's base_dir."""
    if os.path.isabs(relpath):
        return relpath
    return os.path.join(profile["base_dir"], relpath)
