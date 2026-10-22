# Skill: Receipts

Paste this into a Grok Bot chat and ask: *"Save this as a skill called Receipts."*

---

## When to use

When I tag @bot on a post with "receipts", "is this true", "fact check" or "check this", or when I paste a link or a claim in chat and ask whether it's true.

## Inputs and access

- The post @bot forwarded (and the post it replied to or quoted), or the link or claim I pasted.
- Web search and X search, which you already have. No connectors are needed.
- The `receipts` command on your computer. If `receipts --version` fails, install it once:

  ```
  pip install "grokbot-receipts[crawl4ai] @ git+https://github.com/Obiwayne/grokbot-receipts"
  crawl4ai-setup
  ```

- Keep cases in `/workspace/receipts`: run every command with `--home /workspace/receipts`.

## Steps

1. **Pin down one checkable claim.** Rewrite the post as one plain sentence that could be true or false ("The council voted to make all buses free from 1 January"). Drop opinions and jokes. If there's nothing checkable, say so and stop.
2. **Open a case:** `receipts --home /workspace/receipts new "<claim>" --post <post link>`.
3. **Find sources.** Search the web and X for the claim. Prefer primary sources (the official site, the document, the full video, the agency or company itself) and at least one independent news outlet. Look on purpose for a source that disagrees.
4. **Archive them:** `receipts --home /workspace/receipts add latest <url> <url> ...` (three to six links). Read the passages it prints. Each page is archived with a hash in the case folder, so the evidence survives deletion.
5. **Record each source's stance:** `receipts ... stance latest <n> supports|contradicts|context --quote "<exact words>"`. Copy the quote word for word from the archived page. The command refuses a quote it can't find, so never paraphrase.
6. **Ask what the evidence allows:** `receipts ... check latest`.
7. **Give the verdict:** `receipts ... verdict latest <supported|contradicted|disputed|unclear> --why "<one or two sentences>"`. If the command refuses, do not argue with it. Add sources, or use the verdict it allows.

## Validate before replying

- Every supporting or contradicting source has a quote that was found (`✔` in report.md).
- The verdict's reason mentions any important catch (dates, regions, only some people).
- The post's own site never counted as evidence for itself. The tool enforces this, so don't work around it.

## What to return

In this chat: the verdict, the reason, the two strongest links, and attach `card.html` (or a screenshot of it) and `report.md` from the case folder. Then show me `reply.txt` as a draft reply for X.

## Approval

Never post, reply, quote or DM on X, or anywhere else, without my explicit OK in this chat for that exact text. A routine may prepare a case and a draft. It must not post.

## When something goes wrong

- A page comes back empty or blocked: say which one, and find another source. Don't use a cached copy from memory.
- Sources are paywalled: use the free primary source, or say unclear.
- Breaking news under 6 hours old: default to unclear and say why.
