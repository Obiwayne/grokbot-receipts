"""Write a case up: report.md for reading, card.html for a screenshot, reply.txt as a draft reply for X."""

import html
import re
from pathlib import Path

from . import rules

BADGE = {
    "supported": ("SUPPORTED", "#1f9d55", "✅"),
    "contradicted": ("CONTRADICTED", "#d64545", "❌"),
    "disputed": ("DISPUTED", "#d9822b", "⚖️"),
    "unclear": ("UNCLEAR", "#6b7a90", "❓"),
    None: ("NO VERDICT YET", "#6b7a90", "…"),
}
X_LIMIT = 280
X_URL_WEIGHT = 23  # X counts every link as 23 characters


def x_length(text: str) -> int:
    """Approximate X's weighted count: links are 23, most non-Latin characters and emoji count double."""
    total = 0
    for part in re.split(r"(\s+)", text):
        if part.startswith(("http://", "https://")):
            total += X_URL_WEIGHT
        else:
            total += sum(1 if ord(c) < 0x1100 else 2 for c in part)
    return total


def evidence(case) -> list[dict]:
    return [s for s in case.sources if s.get("stance") and s["stance"]["label"] != "context"]


def best_links(case) -> list[str]:
    """One link per independent site that counted toward the verdict, supporting first."""
    out, seen = [], set()
    for stance in ("supports", "contradicts"):
        for s in case.sources:
            st = s.get("stance")
            if st and st["label"] == stance and st.get("quote_found") and not s.get("is_origin") and s["site"] not in seen:
                seen.add(s["site"])
                out.append(s["final_url"])
    return out


def reply_text(case) -> str:
    v = case.data.get("verdict") or {}
    label, _, icon = BADGE[v.get("label")]
    links = best_links(case)[:2]
    head = f"Receipts: {label} {icon}"
    tail = ("\n\n" + "\n".join(links)) if links else ""
    why = v.get("why", "Still gathering sources.")
    text = f"{head}\n{why}{tail}"
    while x_length(text) > X_LIMIT and len(why) > 20:
        why = why[: max(20, len(why) - 10)].rsplit(" ", 1)[0].rstrip(",.;:") + "…"
        text = f"{head}\n{why}{tail}"
    return text


def markdown(case) -> str:
    d, v = case.data, case.data.get("verdict") or {}
    label = BADGE[v.get("label")][0]
    lines = [f"# Receipts: {label}", "", f"**Claim:** {d['claim']}", ""]
    if d.get("post_url"):
        lines += [f"**Posted at:** {d['post_url']}", ""]
    if v:
        lines += [f"**Why:** {v['why']}", "", f"**Rule check:** {v['rule']}", "", f"Decided {v['decided_at']}.", ""]
    lines += ["## Sources", "", "| # | Site | Stance | Quote (found in archived copy) | Archived |", "|---|---|---|---|---|"]
    for s in case.sources:
        st = s.get("stance") or {}
        quote = (st.get("quote") or "").replace("|", "\\|")
        tick = " ✔" if st.get("quote_found") else ""
        origin = " (where the claim was posted)" if s.get("is_origin") else ""
        lines.append(
            f"| {s['n']} | [{s['site']}]({s['final_url']}){origin} | {st.get('label', 'not judged')} | "
            f"{quote}{tick} | `{s['snapshot']}` sha256 `{s['sha256'][:12]}` {s['fetched_at']} |"
        )
    lines += ["", "## Best-matching passages", ""]
    for s in case.sources:
        lines.append(f"### {s['n']}. {s['title'] or s['site']}")
        lines.append("")
        for p in s["passages"] or [{"score": 0, "text": "(nothing on this page matched the claim's words)"}]:
            lines.append(f"> {p['text']}")
            lines.append("")
    lines += [
        "## How this verdict was reached",
        "",
        f"Supported or contradicted needs word-for-word quotes from at least {rules.MIN_SITES} independent sites, "
        "with nothing on the other side. Sources from the same site count once, and the site the claim was posted "
        "on never counts as evidence for itself. Every source is archived with a SHA-256 hash at the time it was read.",
        "",
    ]
    return "\n".join(lines)


def card_html(case) -> str:
    d, v = case.data, case.data.get("verdict") or {}
    label, colour, icon = BADGE[v.get("label")]
    e = html.escape
    rows = []
    for s in evidence(case)[:4]:
        st = s["stance"]
        mark = "+" if st["label"] == "supports" else "−"
        cls = "pro" if st["label"] == "supports" else "con"
        quote = st.get("quote") or ""
        if len(quote) > 180:
            quote = quote[:177].rsplit(" ", 1)[0] + "…"
        rows.append(
            f'<li class="{cls}"><span class="mark">{mark}</span><div><b>{e(s["site"])}</b>'
            f'<q>{e(quote)}</q></div></li>'
        )
    why = e(v.get("why", "Sources are still being gathered."))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Receipts: {e(label)}</title>
<style>
  body{{margin:0;background:#0b0f14;font:16px/1.45 "Segoe UI",system-ui,sans-serif;color:#e8edf3}}
  .card{{box-sizing:border-box;width:1200px;height:675px;padding:56px 64px;display:flex;flex-direction:column;gap:22px;
        background:radial-gradient(1200px 500px at 85% -10%,{colour}33,transparent 60%),#0f141b}}
  .top{{display:flex;align-items:center;gap:18px}}
  .badge{{background:{colour};color:#fff;font-weight:800;letter-spacing:.06em;padding:10px 18px;border-radius:999px;font-size:22px}}
  .brand{{margin-left:auto;color:#8a97a8;font-size:18px}}
  .claim{{font-size:34px;line-height:1.25;font-weight:650;margin:0}}
  .why{{font-size:21px;color:#c3ccd8;margin:0}}
  ul{{list-style:none;margin:0;padding:0;display:grid;gap:12px}}
  li{{display:flex;gap:14px;align-items:flex-start;background:#151c25;border-radius:14px;padding:12px 16px;font-size:17px}}
  .mark{{font-weight:900;font-size:22px;width:20px;text-align:center}}
  .pro .mark{{color:#3ecf8e}} .con .mark{{color:#ff6b6b}}
  q{{display:block;color:#aab6c5}}
  .foot{{margin-top:auto;color:#6f7d8f;font-size:15px}}
</style></head>
<body><div class="card">
  <div class="top"><span class="badge">{icon} {e(label)}</span><span class="brand">Receipts for Grok Bot</span></div>
  <p class="claim">“{e(d['claim'])}”</p>
  <p class="why">{why}</p>
  <ul>{''.join(rows)}</ul>
  <div class="foot">{len(case.sources)} sources archived with SHA-256 · quotes checked word for word · 2 independent sites needed for a verdict</div>
</div></body></html>
"""


def write(case) -> dict[str, Path]:
    out = {
        "report": case.folder / "report.md",
        "card": case.folder / "card.html",
        "reply": case.folder / "reply.txt",
    }
    out["report"].write_text(markdown(case), encoding="utf-8")
    out["card"].write_text(card_html(case), encoding="utf-8")
    out["reply"].write_text(reply_text(case) + "\n", encoding="utf-8")
    return out
