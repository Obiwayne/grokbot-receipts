# How it works

```
 X post ──@bot receipts──▶ Grok Bot (follows the Receipts skill)
                              │  pins down one checkable claim
                              │  searches the web and X for sources
                              ▼
                    receipts new / add  ──▶  Crawl4AI renders each page ──▶ Markdown snapshot + SHA-256
                              │                                          └─▶ BM25: passages closest to the claim
                    receipts stance     ──▶  quote must appear word for word in the snapshot
                    receipts check      ──▶  which verdicts the evidence allows
                    receipts verdict    ──▶  rules pass? ──▶ report.md · card.html · reply.txt
                              │
                              ▼
                     You approve the reply (or don't). Nothing is posted by the tool or the routine.
```

## The split between the Bot and the tool

The Bot is good at what needs judgement: turning a post into one claim, searching, reading, and deciding what each source says. It is not reliable at the parts where a confident mistake does damage: remembering exactly what a page said, telling one publisher from two, or knowing when it has enough. Those are done by code:

| Job | Who | Why |
|---|---|---|
| Rewrite the post as a claim | Bot | Needs language understanding |
| Find sources | Bot | Has web and X search |
| Fetch and archive pages | `receipts add` (Crawl4AI) | The record must match what was on the page, and survive deletion |
| Pick the relevant passages | `receipts add` (BM25) | Shows the Bot where to look; cheap and deterministic |
| Say what a source claims | Bot, via `stance` | Judgement, but it must quote |
| Check the quote | `receipts stance` | Stops paraphrase and invented quotes |
| Decide what verdicts are allowed | `receipts check/verdict` | Fixed rules, not mood |
| Post a reply | You | Approval |

## The rules

A **receipt** is a source with a stance and a quote that was found in its archived copy.

- Sources are grouped by **registrable domain**: `news.bbc.co.uk` and `www.bbc.co.uk` are one site, and `twitter.com`, `t.co` and `x.com` are one site.
- The site the claim was **posted on** never counts. A post on X can't be confirmed by X's own help pages.
- **supported** needs receipts from 2 or more sites that support, and none that contradict.
- **contradicted** is the mirror image.
- **disputed** needs at least one of each.
- **unclear** is always allowed.
- Adding a source or changing a stance clears the verdict, so it has to be decided again.

## Quote matching

Both the quote and the page are normalised before comparing: lower case, Markdown links reduced to their text, `* _ # > |` markup removed, curly quotes and dashes made plain, runs of whitespace collapsed. The quote must be at least 12 characters after that, so "yes" can't be found by accident.

## Passage ranking

Each page is cut into paragraphs (headings, menus and short fragments dropped, long paragraphs cut at sentence ends near 600 characters) and ranked against the claim with BM25 (k1 1.5, b 0.75), stop words removed and a light plural fold. The top three are kept in `case.json` and printed, so the Bot and you can see at a glance whether a page is even about the claim.

## The draft reply

`reply.txt` is the verdict, the reason, and one link per supporting (then contradicting) site, at most two. It is trimmed to fit X's 280-character weighted count, where every link counts as 23 and most emoji and CJK characters count as 2.

## Limits

- Paywalled or login-only pages come back empty and are refused; the Bot is told to find another source.
- Two sites can both be wrong, or copy the same wire story. The rule raises the bar; it doesn't make the verdict true. The report shows the quotes so a reader can judge.
- Video and images aren't checked, only text on pages.
