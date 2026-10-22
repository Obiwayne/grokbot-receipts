# Grok Bot pack

Everything here is for [Grok Bot](https://docs.x.ai/grok-bot/overview), xAI's hosted AI teammates that work on their own cloud computer. It is **not** the Grok API and not @grok on X.

> **Untested on a real Grok Bot.** The skill is written to xAI's documented behaviour (skills, routines, the shared `/workspace` folder, @bot tagging) but I haven't run it on a Grok Bot plan. The `receipts` command it calls is fully tested (see the main README).

## Set it up (about five minutes)

1. Open Grok Bot and start a chat with the Bot you want to do fact-checks (or create one called "Receipts").
2. Paste the contents of [`skills/receipts.md`](skills/receipts.md) and say: *"Save this as a skill called Receipts."*
3. Ask it: *"Install the receipts tool from the skill and run `receipts --version`."* It runs the two install commands on its computer. Crawl4AI's browser download takes a minute or two.
4. Test it on something harmless: *"/Receipts: is it true that the Eiffel Tower is repainted about every seven years?"*

## Use it from X

[Tag @bot](https://docs.x.ai/grok-bot/tag-on-x) on a post:

> @bot receipts

@bot confirms on X and your Bot runs the skill on its computer. The verdict, card and draft reply wait in the Bot's chat for you. Nothing is posted until you say so.

Tagging needs an X account connected to your Grok account, and isn't available yet for accounts based in the UK, EU, Iceland, Liechtenstein, Norway or Australia. It also won't fire if the post has a video or GIF, or also tags @grok. Outside those regions, paste the post link into the Bot's chat instead.

## Optional routine

> Every day at 6pm, check my X mentions for posts asking "is this true" about anything I posted today. Run the Receipts skill on each, at most five. Post nothing; leave me the cards and draft replies in this chat.

Routines must be at least five minutes apart and can't send approvals while you're away, so this one only prepares drafts.
