"""The verdict rules. A confident verdict needs receipts from at least two independent sites.

A receipt is a source whose stance is set and whose quote was found word for word in its archived copy.
Sources from the same site count once, and the site the claim was posted on never counts as evidence for itself.
"""

LABELS = ("supported", "contradicted", "disputed", "unclear")
MIN_SITES = 2


def receipts(sources: list[dict], stance: str) -> set[str]:
    return {
        s["site"]
        for s in sources
        if s.get("stance")
        and s["stance"]["label"] == stance
        and s["stance"].get("quote_found")
        and not s.get("is_origin")
    }


def check(label: str, sources: list[dict]) -> tuple[bool, str]:
    """Whether the evidence allows this verdict, and a plain-English note saying why or why not."""
    if label not in LABELS:
        return False, f"Verdict must be one of: {', '.join(LABELS)}."
    pro, con = receipts(sources, "supports"), receipts(sources, "contradicts")
    tally = f"{len(pro)} site(s) support, {len(con)} contradict"

    if label == "unclear":
        return True, f"Unclear is always allowed ({tally})."
    if label == "disputed":
        if pro and con:
            return True, f"Independent sources disagree ({tally})."
        return False, f"Disputed needs at least one supporting and one contradicting receipt; there are {tally}."
    want, other, word = (pro, con, "support") if label == "supported" else (con, pro, "contradict")
    if other and not want:
        return False, f"Can't say {label}: {tally}."
    if other:
        return False, f"Can't say {label}: {tally}. Use disputed, or find out why they disagree."
    if len(want) < MIN_SITES:
        have = ", ".join(sorted(want)) or "none"
        return False, (
            f"Can't say {label} yet: it needs quotes from {MIN_SITES} independent sites that {word} the claim "
            f"(have {len(want)}: {have}). Add another source or say unclear."
        )
    return True, f"{len(want)} independent sites {word} the claim: {', '.join(sorted(want))}."
