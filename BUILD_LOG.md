# Build log

How Receipts for Grok Bot was built on 22 October 2026, what it was built with, and why. The whole build was screen-recorded.

## The brief

Find what people want from Grok Bot right now, build it from tools listed on [RepoQuarry](https://repoquarry.dev), follow the structure of earlier builds (repo, docs, tests, BUILD_LOG), document and test everything, and record the process.

## Research and decisions

1. **What's trending.** Two things lined up. Grok Bot added [@bot tagging on X](https://docs.x.ai/grok-bot/tag-on-x) around 20 October ([Tesla North](https://teslanorth.com/2026/10/20/grok-bot-x-dms-android-assistant/)): reply to a post with `@bot …` and your own Bot picks it up as a task. And "@grok is this true?" has become a mass habit on X, with repeated reports of confident wrong answers ([Al Jazeera](https://www.aljazeera.com/economy/2025/7/11/as-millions-adopt-grok-to-fact-check-misinformation-abounds), [Alt News](https://www.altnews.in/you-know-nothing-grok-why-xs-ai-bot-cant-be-a-trusted-with-fact-checks/), [BOOM](https://www.boomlive.in/explainers/grok-x-misinformation-fake-news-fact-checking-verification-28680)). So: a fact-check that runs on your own Bot when you tag it, with guard rails against exactly those failures.
2. **Grok Bot, precisely.** RepoQuarry lists [Grok Bot](https://repoquarry.dev/alternatives/grok-bot) as xAI's hosted AI teammates, which is not the Grok API and not @grok. Per xAI's docs, a Bot has a persistent cloud computer with a terminal and a shared `/workspace`, and learns reusable **skills** from written instructions. There's no documented public plugin API for third parties, so the integration is a skill (instructions) plus a CLI the Bot runs on its computer.
3. **What code should do, and what the Bot should do.** The failures in the press are about confidence, misremembered sources and one-sided evidence. Those are things rules can enforce: archive the page, check quotes literally, count independent sites, block a clean verdict when anything disagrees. Judgement (what's the claim, what does this page say) stays with the Bot. See [How it works](docs/how-it-works.md).
4. **Crawl4AI for fetching** (from the RepoQuarry catalogue, `web-scraping`). It renders pages in a headless browser and outputs Markdown, which is what both the archive and the quote check want. Its Apache-2.0 licence adds an attribution requirement, which is met in the README, NOTICE and `receipts --help`. A plain `urllib` fetcher is the fallback when Crawl4AI isn't installed.
5. **No LLM in the tool.** The Bot is the model. Passage ranking is BM25 in pure Python, so the tool has no runtime dependencies and gives the same answer every time.
6. **Two independent sites** as the bar, grouped by registrable domain, with the post's own site excluded. Picked as the smallest rule that would have stopped the reported failures (single-source answers, and posts "confirming" themselves).
7. **Never posts.** The skill and routine only draft. That matches xAI's own guidance to keep publishing behind approval, and it's the user's call what goes out under their name.

## Built with

| Piece | Role |
|---|---|
| [Crawl4AI](https://github.com/unclecode/crawl4ai) 0.9.5 | Headless-browser fetch to Markdown ([RepoQuarry](https://repoquarry.dev/projects/crawl4ai)) |
| [Grok Bot](https://docs.x.ai/grok-bot/overview) | Runs the skill: claim, search, judgement ([RepoQuarry](https://repoquarry.dev/alternatives/grok-bot)) |
| Python 3.13 (3.10+ supported) | The `receipts` CLI, standard library only |
| pytest 9 | Tests |
| Playwright (installed by Crawl4AI) | Renders `card.html` to PNG for docs and posts |

## Testing

- **14 tests, all passing** (`pytest -v`, 6 s): rules (two sites, origin excluded, unverified quotes ignored, contradictions force *disputed*), quote matching through markup and curly quotes, site grouping (`bbc.co.uk`, `x.com` aliases), passage splitting and BM25 ranking, X's weighted character count, four full CLI cases against local stand-in sites on separate ports (a post, a newspaper, a council page and a blog that disagrees), and one real Crawl4AI headless-browser fetch.
- **Live run** on a real claim, "You can now tag @bot on X to hand a post to your Grok Bot", with three real sources fetched by Crawl4AI. The tool refused *supported* with only xAI's docs, accepted it once Tesla North was added, and correctly treated help.x.com as the same site as the post (X), so it didn't count.
- **Not tested here**: the Grok Bot skill on a real Grok Bot plan, and @bot tagging (not available for UK-based X accounts).

## Things found on the way

- The first passage ranking ran headings and tables into the article text on Crawl4AI pages. Spotted in the live run's report. The new test for it failed first (a heading at the very top of a page still ran on), and the fix gives headings and table rows their own blocks.
- The `check` message suggested "disputed" for a verdict that had nothing to dispute. Reworded.
- Windows PowerShell 5 shows UTF-8 emoji in `reply.txt` as mojibake with `Get-Content`; the file itself is fine (`Get-Content -Encoding utf8`).
- help.x.com archived under X's own site rule. That is the intended behaviour, and a nice example for the docs.
- Tesla North says the X plugin must be installed for @bot to work; xAI's docs say it's optional. Recorded as context, not a contradiction of the claim.
- Archived article text isn't committed (`demo/` is git-ignored): the repo shouldn't republish other sites' articles. Only the rendered card is in `docs/img`.
