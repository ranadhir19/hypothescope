"""Command-line interface for hypothescope.

    python3 -m hypothescope generate PROFILE.json [--out HYPOTHESES.json]
    python3 -m hypothescope test     PROFILE.json [--out PREFIX]
    python3 -m hypothescope report   LEDGER.json   [--out REPORT.md]

`test` writes PREFIX.ledger.json and PREFIX.ledger.md (default PREFIX is
the profile's paper_id). `report` re-renders Markdown from a saved ledger.
"""
import argparse
import json
import sys

from .generate import generate
from .ledger import render_markdown, test_profile
from .profile import load_profile


def _dump(obj, out):
    text = json.dumps(obj, indent=2)
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    else:
        print(text)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="hypothescope")
    sub = parser.add_subparsers(dest="command", required=True)

    p_gen = sub.add_parser("generate", help="generate hypotheses from a profile")
    p_gen.add_argument("profile")
    p_gen.add_argument("--out")

    p_test = sub.add_parser("test", help="generate + run all local tests, emit a ledger")
    p_test.add_argument("profile")
    p_test.add_argument("--out", help="output prefix (default: paper_id)")

    p_rep = sub.add_parser("report", help="render Markdown from a ledger JSON")
    p_rep.add_argument("ledger")
    p_rep.add_argument("--out")

    args = parser.parse_args(argv)

    if args.command == "generate":
        profile = load_profile(args.profile)
        _dump(generate(profile), args.out)
        return 0

    if args.command == "test":
        profile = load_profile(args.profile)
        ledger = test_profile(profile)
        prefix = args.out or profile["paper_id"]
        with open(prefix + ".ledger.json", "w", encoding="utf-8") as fh:
            json.dump(ledger, fh, indent=2)
            fh.write("\n")
        with open(prefix + ".ledger.md", "w", encoding="utf-8") as fh:
            fh.write(render_markdown(ledger))
        c = ledger["counts"]
        print(f"{ledger['paper_id']}: {c['TESTED-SUPPORTED']} supported, "
              f"{c['TESTED-REFUTED']} refuted, {c['UNTESTED']} untested "
              f"-> {prefix}.ledger.json / {prefix}.ledger.md")
        return 0

    if args.command == "report":
        with open(args.ledger, "r", encoding="utf-8") as fh:
            ledger = json.load(fh)
        md = render_markdown(ledger)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(md)
        else:
            print(md)
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
