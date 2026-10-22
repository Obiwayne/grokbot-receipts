"""A case: one claim, the sources gathered for it, each source's stance, and the verdict. Stored as JSON on disk."""

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from . import rules
from .fetch import Page, fetch
from .sites import site_of
from .text import passages, quote_in, rank

STANCES = ("supports", "contradicts", "context")


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def home(path: str | None = None) -> Path:
    return Path(path or os.environ.get("RECEIPTS_HOME") or "receipts-cases")


def slug(text: str, words: int = 6) -> str:
    w = re.findall(r"[a-z0-9]+", text.lower())[:words]
    return "-".join(w) or "claim"


class CaseError(Exception):
    pass


class Case:
    def __init__(self, folder: Path, data: dict):
        self.folder = folder
        self.data = data

    # --- storage -----------------------------------------------------------------------------------------------

    @classmethod
    def create(cls, root: Path, claim: str, post_url: str | None = None) -> "Case":
        claim = claim.strip()
        if len(claim) < 8:
            raise CaseError("Write the claim out as a full sentence.")
        base = f"{datetime.now(timezone.utc):%Y-%m-%d}-{slug(claim)}"
        folder, n = root / base, 2
        while folder.exists():
            folder, n = root / f"{base}-{n}", n + 1
        (folder / "sources").mkdir(parents=True)
        data = {
            "id": folder.name,
            "claim": claim,
            "post_url": post_url,
            "post_site": site_of(post_url) if post_url else None,
            "created_at": now(),
            "sources": [],
            "verdict": None,
        }
        case = cls(folder, data)
        case.save()
        return case

    @classmethod
    def load(cls, root: Path, case_id: str) -> "Case":
        if case_id == "latest":
            found = sorted((p for p in root.glob("*/case.json")), key=lambda p: p.stat().st_mtime)
            if not found:
                raise CaseError(f"No cases in {root}.")
            folder = found[-1].parent
        else:
            folder = root / case_id
        try:
            data = json.loads((folder / "case.json").read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise CaseError(f"No case called {case_id!r} in {root}.") from None
        return cls(folder, data)

    def save(self) -> None:
        tmp = self.folder / "case.json.tmp"
        tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(self.folder / "case.json")

    # --- sources -----------------------------------------------------------------------------------------------

    @property
    def claim(self) -> str:
        return self.data["claim"]

    @property
    def sources(self) -> list[dict]:
        return self.data["sources"]

    def source(self, n: int) -> dict:
        for s in self.sources:
            if s["n"] == n:
                return s
        raise CaseError(f"Case {self.data['id']} has no source {n}.")

    def snapshot(self, s: dict) -> str:
        return (self.folder / s["snapshot"]).read_text(encoding="utf-8")

    def add(self, url: str, fetcher: str = "auto", page: Page | None = None) -> dict:
        """Fetch a page, archive it as Markdown with its hash, and keep the passages that best match the claim."""
        if any(s["url"] == url for s in self.sources):
            raise CaseError(f"{url} is already in this case.")
        page = page or fetch(url, fetcher)
        if len(page.markdown.strip()) < 80:
            raise CaseError(f"{url} came back nearly empty; it may need a login or block automated reading.")
        n = max((s["n"] for s in self.sources), default=0) + 1
        site = site_of(page.final_url or url)
        name = f"sources/{n:02d}-{re.sub(r'[^a-z0-9.-]+', '-', site)}.md"
        header = f"<!-- receipts snapshot of {page.final_url} fetched {now()} with {page.fetcher} -->\n\n"
        body = header + page.markdown
        (self.folder / name).write_text(body, encoding="utf-8")
        record = {
            "n": n,
            "url": url,
            "final_url": page.final_url,
            "site": site,
            "title": page.title,
            "fetched_at": now(),
            "fetcher": page.fetcher,
            "snapshot": name,
            "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "is_origin": bool(self.data.get("post_site")) and site == self.data["post_site"],
            "passages": [{"score": sc, "text": t} for sc, t in rank(self.claim, passages(page.markdown))],
            "stance": None,
        }
        self.sources.append(record)
        self.data["verdict"] = None  # new evidence reopens the case
        self.save()
        return record

    def set_stance(self, n: int, stance: str, quote: str | None) -> dict:
        if stance not in STANCES:
            raise CaseError(f"Stance must be one of: {', '.join(STANCES)}.")
        s = self.source(n)
        if stance != "context" and not quote:
            raise CaseError("A source that supports or contradicts the claim needs --quote, copied word for word from it.")
        found = quote_in(quote, self.snapshot(s)) if quote else None
        if quote and not found:
            raise CaseError(
                f"That quote is not in source {n}'s archived copy ({s['snapshot']}). Copy the exact words from the page."
            )
        s["stance"] = {"label": stance, "quote": quote, "quote_found": found, "set_at": now()}
        self.data["verdict"] = None
        self.save()
        return s

    # --- verdict -----------------------------------------------------------------------------------------------

    def decide(self, label: str, why: str) -> dict:
        if len(why.strip()) < 15:
            raise CaseError("Give a one or two sentence reason with --why.")
        ok, note = rules.check(label, self.sources)
        if not ok:
            raise CaseError(note)
        self.data["verdict"] = {"label": label, "why": why.strip(), "rule": note, "decided_at": now()}
        self.save()
        return self.data["verdict"]
