"""receipts: the command line a Grok Bot (or you) uses to work a fact-check case."""

import argparse
import json
import sys

from . import __version__, report, rules
from .case import STANCES, Case, CaseError, home
from .fetch import FetchError

# Required by Crawl4AI's licence for command-line tools that use it.
CRAWL4AI_CREDIT = (
    "This product includes software developed by UncleCode (https://x.com/unclecode) "
    "as part of the Crawl4AI project (https://github.com/unclecode/crawl4ai)."
)


def _out(args, data, text: str) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False) if args.json else text)


def cmd_new(args):
    case = Case.create(home(args.home), args.claim, args.post)
    _out(args, case.data, f"Opened case {case.data['id']}\n  folder: {case.folder}")


def cmd_add(args):
    case = Case.load(home(args.home), args.case)
    failed = 0
    for url in args.urls:
        try:
            s = case.add(url, args.fetcher)
        except (CaseError, FetchError) as e:
            failed += 1
            print(f"  skipped {url}: {e}", file=sys.stderr)
            continue
        origin = "  (where the claim was posted: not counted as evidence)" if s["is_origin"] else ""
        _out(args, s, f"[{s['n']}] {s['site']}  {s['title'][:70]}{origin}\n     archived {s['snapshot']}  sha256 {s['sha256'][:12]}")
        if not args.json:
            for p in s["passages"]:
                print(f"     ~ {p['text'][:220]}")
    if failed and failed == len(args.urls):
        sys.exit(1)


def cmd_stance(args):
    case = Case.load(home(args.home), args.case)
    s = case.set_stance(args.n, args.stance, args.quote)
    note = " (quote found in the archived copy)" if s["stance"]["quote_found"] else ""
    _out(args, s, f"Source {args.n} ({s['site']}): {args.stance}{note}")


def cmd_check(args):
    case = Case.load(home(args.home), args.case)
    result = {label: rules.check(label, case.sources) for label in rules.LABELS}
    lines = [f"{'ok ' if ok else 'no '} {label:<13} {note}" for label, (ok, note) in result.items()]
    _out(args, {k: {"allowed": ok, "note": n} for k, (ok, n) in result.items()}, "\n".join(lines))


def cmd_verdict(args):
    case = Case.load(home(args.home), args.case)
    v = case.decide(args.label, args.why)
    paths = report.write(case)
    _out(args, {"verdict": v, "files": {k: str(p) for k, p in paths.items()}},
         f"Verdict: {args.label}. {v['rule']}\n" + "\n".join(f"  {k}: {p}" for k, p in paths.items()))


def cmd_report(args):
    case = Case.load(home(args.home), args.case)
    paths = report.write(case)
    _out(args, {k: str(p) for k, p in paths.items()}, "\n".join(f"{k}: {p}" for k, p in paths.items()))


def cmd_show(args):
    case = Case.load(home(args.home), args.case)
    if args.json:
        _out(args, case.data, "")
        return
    print(report.markdown(case))


def cmd_list(args):
    root = home(args.home)
    rows = []
    for p in sorted(root.glob("*/case.json")):
        c = Case.load(root, p.parent.name)
        rows.append({"id": c.data["id"], "claim": c.claim, "sources": len(c.sources),
                     "verdict": (c.data["verdict"] or {}).get("label")})
    _out(args, rows, "\n".join(f"{r['id']}  [{r['verdict'] or 'open'}]  {r['sources']} sources" for r in rows) or "No cases yet.")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="receipts",
        description="Fact-check a claim with archived sources and verified quotes.",
        epilog=CRAWL4AI_CREDIT,
    )
    p.add_argument("--version", action="version", version=f"receipts {__version__}")
    p.add_argument("--home", help="where cases are kept (default $RECEIPTS_HOME or ./receipts-cases)")
    p.add_argument("--json", action="store_true", help="print JSON instead of text")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("new", help="open a case for a claim")
    s.add_argument("claim")
    s.add_argument("--post", help="link to the post the claim came from (it won't count as evidence for itself)")
    s.set_defaults(fn=cmd_new)

    s = sub.add_parser("add", help="fetch and archive sources")
    s.add_argument("case", help="case id, or 'latest'")
    s.add_argument("urls", nargs="+")
    s.add_argument("--fetcher", choices=["auto", "crawl4ai", "plain"], default="auto")
    s.set_defaults(fn=cmd_add)

    s = sub.add_parser("stance", help="record what a source says about the claim")
    s.add_argument("case")
    s.add_argument("n", type=int, help="source number")
    s.add_argument("stance", choices=STANCES)
    s.add_argument("--quote", help="the words, copied exactly from the source")
    s.set_defaults(fn=cmd_stance)

    s = sub.add_parser("check", help="which verdicts the evidence allows right now")
    s.add_argument("case")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("verdict", help="give a verdict and write the report, card and draft reply")
    s.add_argument("case")
    s.add_argument("label", choices=rules.LABELS)
    s.add_argument("--why", required=True)
    s.set_defaults(fn=cmd_verdict)

    s = sub.add_parser("report", help="rewrite report.md, card.html and reply.txt")
    s.add_argument("case")
    s.set_defaults(fn=cmd_report)

    s = sub.add_parser("show", help="print a case")
    s.add_argument("case")
    s.set_defaults(fn=cmd_show)

    s = sub.add_parser("list", help="list cases")
    s.set_defaults(fn=cmd_list)
    return p


def main(argv=None) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    try:
        args.fn(args)
    except CaseError as e:
        print(f"receipts: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
