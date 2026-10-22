from receipts import rules
from receipts.report import x_length
from receipts.sites import site_of
from receipts.text import passages, quote_in, rank


def test_site_of_groups_hosts_by_publisher():
    assert site_of("https://www.bbc.co.uk/news/1") == "bbc.co.uk"
    assert site_of("https://news.bbc.co.uk/x") == "bbc.co.uk"
    assert site_of("https://edition.cnn.com/a") == "cnn.com"
    assert site_of("https://twitter.com/a/status/1") == "x.com"
    assert site_of("https://mobile.twitter.com/a") == "x.com"
    assert site_of("http://127.0.0.1:8001/a") == "127.0.0.1:8001"
    assert site_of("not a url") == ""


def test_quote_check_ignores_case_markup_and_curly_quotes():
    doc = "Council leader said **“the biggest change”** in a [generation](https://x.y)."
    assert quote_in('said "the biggest change" in a generation', doc)
    assert quote_in("THE BIGGEST CHANGE", doc)
    assert not quote_in("the smallest change", doc)
    assert not quote_in("change", doc)  # too short to prove anything


def test_passages_drop_menus_and_split_long_paragraphs():
    md = "Home | News | Sport\n\n" + ("This sentence is about buses and fares in town. " * 30)
    ps = passages(md, max_chars=300)
    assert all(len(p) <= 300 for p in ps)
    assert not any("Home | News" in p for p in ps)


def test_headings_and_tables_do_not_run_into_paragraphs():
    md = "# Tag @bot on X\nTag @bot in a post or reply on X to hand that post to your Grok Bot as a task.\n| a | b |\n| c | d |"
    ps = passages(md)
    assert ps == ["Tag @bot in a post or reply on X to hand that post to your Grok Bot as a task."]


def test_rank_puts_the_matching_passage_first():
    docs = [
        "The weather this weekend will be sunny with light winds across the region.",
        "Buses will be free for all riders from 1 January after the council vote.",
        "A new bakery has opened on the high street selling sourdough and pastries.",
    ]
    top = rank("Riverside buses free from January", docs)
    assert top and top[0][1].startswith("Buses will be free")


def _src(site, stance, found=True, origin=False):
    return {"site": site, "is_origin": origin, "stance": {"label": stance, "quote": "q" * 20, "quote_found": found}}


def test_supported_needs_two_independent_sites():
    one = [_src("a.com", "supports"), _src("a.com", "supports")]
    assert not rules.check("supported", one)[0]
    two = one + [_src("b.org", "supports")]
    assert rules.check("supported", two)[0]


def test_origin_and_unverified_quotes_do_not_count():
    srcs = [_src("x.com", "supports", origin=True), _src("a.com", "supports"), _src("b.com", "supports", found=False)]
    ok, note = rules.check("supported", srcs)
    assert not ok and "have 1" in note


def test_any_contradiction_blocks_a_clean_verdict():
    srcs = [_src("a.com", "supports"), _src("b.com", "supports"), _src("c.com", "contradicts")]
    assert not rules.check("supported", srcs)[0]
    assert rules.check("disputed", srcs)[0]
    assert rules.check("unclear", srcs)[0]
    assert not rules.check("contradicted", srcs)[0]


def test_x_length_counts_links_as_23():
    assert x_length("hi https://example.com/a/very/long/path/that/goes/on/and/on") == 3 + 23
    assert x_length("✅") == 2
