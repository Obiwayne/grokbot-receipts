"""Text helpers: normalising for quote checks, splitting into passages, BM25 ranking."""

import math
import re
from collections import Counter

_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
_MARKUP = re.compile(r"[*_`#>|]+")
_SPACE = re.compile(r"\s+")
_QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", " ": " "})
_WORD = re.compile(r"[a-z0-9]+(?:[.,][0-9]+)*")

STOPWORDS = set(
    "a an and are as at be been but by can could did do does for from had has have he her his how i if in into is it "
    "its just me more most my no not of on or our out over said says she so than that the their them then there these "
    "they this those to too up us was we were what when where which who why will with would you your".split()
)


def normalise(text: str) -> str:
    """Lower-case plain text with Markdown links, markup, curly quotes and runs of spaces flattened."""
    text = _LINK.sub(r"\1", text.translate(_QUOTES))
    text = _MARKUP.sub(" ", text)
    return _SPACE.sub(" ", text).strip().lower()


def quote_in(quote: str, document: str) -> bool:
    """True when the quote appears word for word in the document, ignoring case, markup and spacing."""
    q = normalise(quote).strip(" \"'.")
    return len(q) >= 12 and q in normalise(document)


def tokens(text: str) -> list[str]:
    out = []
    for w in _WORD.findall(normalise(text)):
        if w in STOPWORDS:
            continue
        if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.append(w)
    return out


def passages(markdown: str, max_chars: int = 600) -> list[str]:
    """Split a page into readable passages: paragraphs, with long ones cut at sentence ends."""
    out = []
    # Headings and table rows start their own block even without a blank line before them.
    markdown = re.sub(r"(?m)^([ \t]*#{1,6}\s.*)$", r"\n\1\n", markdown)
    markdown = re.sub(r"\n(?=[ \t]*\|)", "\n\n", markdown)
    for block in re.split(r"\n\s*\n", markdown):
        if re.match(r"\s*#{1,6}\s", block) and "\n" not in block.strip():
            continue  # a heading on its own
        block = _SPACE.sub(" ", _LINK.sub(r"\1", block)).strip()
        if len(block) < 40 or block.count(" ") < 6:
            continue  # menus, buttons, captions
        while len(block) > max_chars:
            cut = max(block.rfind(". ", 0, max_chars), block.rfind("? ", 0, max_chars), block.rfind("! ", 0, max_chars))
            cut = cut + 1 if cut > max_chars // 3 else max_chars
            out.append(block[:cut].strip())
            block = block[cut:].strip()
        if block:
            out.append(block)
    return out


def rank(query: str, docs: list[str], top: int = 3, k1: float = 1.5, b: float = 0.75) -> list[tuple[float, str]]:
    """BM25 over the passages; returns up to `top` (score, passage) pairs with a positive score."""
    q = set(tokens(query))
    toks = [tokens(d) for d in docs]
    if not q or not docs:
        return []
    avg = sum(len(t) for t in toks) / len(toks) or 1
    df = Counter(w for t in toks for w in set(t) if w in q)
    n = len(docs)
    scored = []
    for d, t in zip(docs, toks):
        tf = Counter(t)
        s = 0.0
        for w in q:
            if not tf[w]:
                continue
            idf = math.log(1 + (n - df[w] + 0.5) / (df[w] + 0.5))
            s += idf * tf[w] * (k1 + 1) / (tf[w] + k1 * (1 - b + b * len(t) / avg))
        if s > 0:
            scored.append((round(s, 3), d))
    scored.sort(key=lambda x: -x[0])
    return scored[:top]
