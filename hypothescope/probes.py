"""Bounded local test executors ("probes") for hypothescope.

Every probe is a small, declarative specification from a paper profile.
Probes only READ artifacts (JSON, CSV, text) and run bounded arithmetic.
They never write, never call the network, and never execute code named by
a profile. A probe returns (outcome, detail) where outcome is one of:

  "pass"    - the deciding test ran and the hypothesis held
  "fail"    - the deciding test ran and the hypothesis did not hold
  "error"   - the test could not run (e.g. artifact missing); the engine
              records the hypothesis as UNTESTED, never as supported

Supported probe kinds:
  json_value     read a dotted key from a JSON artifact, compare to expect
  json_compare   compare two dotted keys inside one JSON artifact
  csv_stat       median/mean/min/max/count/nunique of a CSV column (filtered)
  csv_count      count CSV rows satisfying column-vs-value/column conditions
  expr           arithmetic over values bound from json_value/csv_stat probes
  factor_search  smallest calibration factor reaching a coverage target on a
                 CSV of (estimate, truth) pairs, with a median-ratio ceiling
  text_check     regex present/absent in a text artifact
  text_count     count regex matches in a text artifact
"""
import ast
import csv
import json
import math
import operator
import os
import re
import statistics

from .profile import resolve

_OPS = {
    ">": operator.gt, "<": operator.lt, ">=": operator.ge,
    "<=": operator.le, "==": operator.eq, "!=": operator.ne,
}


class ProbeError(Exception):
    pass


def _load_json(profile, path):
    full = resolve(profile, path)
    if not os.path.isfile(full):
        raise ProbeError(f"artifact missing: {path}")
    with open(full, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _dig(data, dotted):
    """Descend a dotted key path. Keys in real artifacts often contain
    dots themselves ("0.8", "a0.85_c0.1"), so at each level the longest
    remaining candidate that is an actual key wins."""
    if not isinstance(data, (dict, list)):
        if dotted:
            raise ProbeError(f"cannot descend into {dotted}")
        return data
    if isinstance(data, list):
        head, _, rest = dotted.partition(".")
        return _dig(data[int(head)], rest) if rest else data[int(head)]
    # dict: try candidates from longest to shortest
    parts = dotted.split(".")
    for cut in range(len(parts), 0, -1):
        candidate = ".".join(parts[:cut])
        if candidate in data:
            rest = ".".join(parts[cut:])
            return _dig(data[candidate], rest) if rest else data[candidate]
    raise ProbeError(f"key not found: {dotted}")


def _load_csv(profile, path):
    full = resolve(profile, path)
    if not os.path.isfile(full):
        raise ProbeError(f"artifact missing: {path}")
    with open(full, "r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _filtered(rows, where):
    if not where:
        return rows
    out = []
    for row in rows:
        ok = True
        for col, want in where.items():
            got = row.get(col)
            if str(got) != str(want):
                # tolerate numeric spellings ("1" vs "1.0")
                try:
                    if float(got) != float(want):
                        ok = False
                except (TypeError, ValueError):
                    ok = False
            if not ok:
                break
        if ok:
            out.append(row)
    return out


def _close(got, expect, tol):
    return abs(float(got) - float(expect)) <= float(tol)


# ---------------------------------------------------------------- probes

def probe_json_value(profile, spec):
    data = _load_json(profile, spec["path"])
    got = _dig(data, spec["key"])
    tol = spec.get("tol", 0.0)
    ok = _close(got, spec["expect"], tol)
    return ok, f"{spec['path']}:{spec['key']} = {got} (expect {spec['expect']} +/- {tol})"


def probe_json_compare(profile, spec):
    data = _load_json(profile, spec["path"])
    a = _dig(data, spec["key_a"])
    b = _dig(data, spec["key_b"])
    rel = spec.get("relation", ">")
    ok = _OPS[rel](float(a), float(b))
    return ok, f"{spec['key_a']} = {a} {rel} {spec['key_b']} = {b} -> {ok}"


def probe_csv_stat(profile, spec):
    rows = _filtered(_load_csv(profile, spec["path"]), spec.get("where"))
    stat = spec["stat"]
    if stat == "count":
        got = len(rows)
    else:
        vals = []
        for row in rows:
            try:
                vals.append(float(row[spec["column"]]))
            except (TypeError, ValueError, KeyError):
                continue
        if not vals:
            raise ProbeError(f"no numeric values in column {spec['column']}")
        if stat == "median":
            got = statistics.median(vals)
        elif stat == "mean":
            got = statistics.fmean(vals)
        elif stat == "min":
            got = min(vals)
        elif stat == "max":
            got = max(vals)
        elif stat == "nunique":
            got = len(set(vals))
        else:
            raise ProbeError(f"unknown stat: {stat}")
    tol = spec.get("tol", 0.0)
    ok = _close(got, spec["expect"], tol)
    return ok, (f"{spec['path']}:{spec['column']} {stat} over {len(rows)} rows "
                f"= {got} (expect {spec['expect']} +/- {tol})")


def probe_csv_count(profile, spec):
    rows = _load_csv(profile, spec["path"])
    n = 0
    for row in rows:
        ok = True
        for cond in spec["conditions"]:
            left = float(row[cond["column"]])
            if "other_column" in cond:
                right = float(row[cond["other_column"]])
            else:
                right = float(cond["value"])
            if not _OPS[cond["op"]](left, right):
                ok = False
                break
        if ok:
            n += 1
    ok = n == int(spec["expect"])
    return ok, f"{spec['path']}: {n} rows satisfy conditions (expect {spec['expect']})"


def _eval_expr(expression, bindings):
    tree = ast.parse(expression, mode="eval")
    allowed_funcs = {"min": min, "max": max, "abs": abs, "sqrt": math.sqrt}

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ProbeError("non-numeric constant in expression")
        if isinstance(node, ast.Name):
            if node.id in bindings:
                return bindings[node.id]
            raise ProbeError(f"unbound name in expression: {node.id}")
        if isinstance(node, ast.BinOp):
            left, right = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.Pow):
                return left ** right
            raise ProbeError("operator not allowed in expression")
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -ev(node.operand)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in allowed_funcs:
            return allowed_funcs[node.func.id](*[ev(a) for a in node.args])
        raise ProbeError("expression element not allowed")

    return ev(tree)


def probe_expr(profile, spec):
    bindings = {}
    for name, sub in spec["bindings"].items():
        bindings[name] = _probe_value(profile, sub)
    got = _eval_expr(spec["expression"], bindings)
    tol = spec.get("tol", 0.0)
    ok = _close(got, spec["expect"], tol)
    return ok, f"expr {spec['expression']!r} = {got} (expect {spec['expect']} +/- {tol}); bindings={bindings}"


def _probe_value(profile, spec):
    kind = spec["kind"]
    if kind == "json_value":
        return float(_dig(_load_json(profile, spec["path"]), spec["key"]))
    if kind == "csv_stat":
        rows = _filtered(_load_csv(profile, spec["path"]), spec.get("where"))
        vals = [float(r[spec["column"]]) for r in rows]
        stat = spec["stat"]
        if stat == "median":
            return statistics.median(vals)
        if stat == "mean":
            return statistics.fmean(vals)
        if stat == "min":
            return min(vals)
        if stat == "max":
            return max(vals)
        if stat == "count":
            return float(len(rows))
        if stat == "nunique":
            return float(len(set(vals)))
    raise ProbeError(f"probe kind {kind} cannot bind a value")


def probe_factor_search(profile, spec):
    rows = _filtered(_load_csv(profile, spec["path"]), spec.get("where"))
    pairs = []
    for row in rows:
        try:
            est = float(row[spec["value_column"]])
            truth = float(row[spec["target_column"]])
        except (TypeError, ValueError, KeyError):
            continue
        if truth > 0:
            pairs.append((est, truth))
    if not pairs:
        raise ProbeError("no usable (estimate, truth) pairs")
    target_cov = float(spec["coverage_target"])
    ceiling = float(spec["max_median_ratio"])
    found = None
    for factor in spec["factors"]:
        covered = sum(1 for est, truth in pairs if est * factor >= truth)
        cov = covered / len(pairs)
        if cov >= target_cov:
            ratios = sorted((est * factor) / truth for est, truth in pairs)
            med = statistics.median(ratios)
            found = (float(factor), cov, med)
            break
    if found is None:
        return False, (f"no factor in {spec['factors']} reaches coverage "
                       f"{target_cov} over {len(pairs)} pairs")
    factor, cov, med = found
    ok = med <= ceiling
    return ok, (f"smallest factor reaching coverage {target_cov}: {factor} "
                f"(coverage {cov:.3f}, median ratio {med:.3f}, ceiling {ceiling}) "
                f"over {len(pairs)} pairs")


def probe_text_check(profile, spec):
    full = resolve(profile, spec["path"])
    if not os.path.isfile(full):
        raise ProbeError(f"artifact missing: {spec['path']}")
    with open(full, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    found = re.search(spec["pattern"], text) is not None
    want = spec.get("expect", "present") == "present"
    return found == want, f"pattern {spec['pattern']!r} in {spec['path']}: found={found} (expect {spec.get('expect', 'present')})"


def probe_text_count(profile, spec):
    full = resolve(profile, spec["path"])
    if not os.path.isfile(full):
        raise ProbeError(f"artifact missing: {spec['path']}")
    with open(full, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    n = len(re.findall(spec["pattern"], text))
    ok = n == int(spec["expect"])
    return ok, f"pattern {spec['pattern']!r} occurs {n}x in {spec['path']} (expect {spec['expect']})"


_PROBES = {
    "json_value": probe_json_value,
    "json_compare": probe_json_compare,
    "csv_stat": probe_csv_stat,
    "csv_count": probe_csv_count,
    "expr": probe_expr,
    "factor_search": probe_factor_search,
    "text_check": probe_text_check,
    "text_count": probe_text_count,
}


def run_probe(profile, spec):
    """Run one probe spec. Returns (passed: bool, detail: str).
    Raises ProbeError when the test cannot run at all."""
    kind = spec.get("kind")
    if kind not in _PROBES:
        raise ProbeError(f"unknown probe kind: {kind}")
    return _PROBES[kind](profile, spec)
