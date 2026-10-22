"""End to end through the CLI, against local stand-in sites, with the plain fetcher."""

import json

import pytest
from conftest import CLAIM

from receipts.cli import main
from receipts.report import X_LIMIT, x_length


def run(capsys, home, *args):
    main(["--home", str(home), "--json", *args])
    return json.loads(capsys.readouterr().out)


def fail(capsys, home, *args):
    with pytest.raises(SystemExit) as e:
        main(["--home", str(home), *args])
    return e.value.code, capsys.readouterr().err


def test_full_case_reaches_supported_only_with_two_receipts(tmp_path, capsys, sites):
    case = run(capsys, tmp_path, "new", CLAIM, "--post", sites["post"])
    cid = case["id"]

    for name in ("post", "gazette", "council"):
        run(capsys, tmp_path, "add", cid, sites[name], "--fetcher", "plain")
    data = run(capsys, tmp_path, "show", cid)
    post, gazette, council = data["sources"]

    # The post is archived but can't vouch for itself.
    assert post["is_origin"] and not gazette["is_origin"]
    # Scripts, menus and footers are not in the archived copy; the article is.
    snap = (tmp_path / cid / gazette["snapshot"]).read_text(encoding="utf-8")
    assert "analytics" not in snap and "Cookie settings" not in snap
    assert "free for all riders from 1 January" in snap
    assert len(gazette["sha256"]) == 64
    # The best passage is the one about fares, not the byline.
    assert "free for all riders" in gazette["passages"][0]["text"]

    # A made-up quote is refused.
    code, err = fail(capsys, tmp_path, "stance", cid, "2", "supports", "--quote", "buses are free forever for everyone")
    assert code == 2 and "not in source 2" in err

    run(capsys, tmp_path, "stance", cid, "1", "supports", "--quote", "Riverside buses will be free for everyone from 1 January")
    run(capsys, tmp_path, "stance", cid, "2", "supports", "--quote", "buses will be free for all riders from 1 January")

    # One independent site plus the post itself is not enough.
    code, err = fail(capsys, tmp_path, "verdict", cid, "supported", "--why", "The council voted for it on Tuesday.")
    assert code == 2 and "have 1" in err

    run(capsys, tmp_path, "stance", cid, "3", "supports",
        "--quote", "travel on all Riverside bus routes will be free for everyone")
    allowed = run(capsys, tmp_path, "check", cid)
    assert allowed["supported"]["allowed"] and not allowed["contradicted"]["allowed"]

    out = run(capsys, tmp_path, "verdict", cid, "supported",
              "--why", "The council approved fare-free buses for all riders from 1 January 2027, by 7 votes to 2.")
    assert out["verdict"]["label"] == "supported"

    reply = (tmp_path / cid / "reply.txt").read_text(encoding="utf-8").strip()
    assert reply.startswith("Receipts: SUPPORTED")
    assert x_length(reply) <= X_LIMIT
    assert sites["gazette"] in reply and sites["council"] in reply and sites["post"] not in reply

    card = (tmp_path / cid / "card.html").read_text(encoding="utf-8")
    assert "SUPPORTED" in card and "Riverside" in card
    md = (tmp_path / cid / "report.md").read_text(encoding="utf-8")
    assert "where the claim was posted" in md and gazette["sha256"][:12] in md


def test_contradicting_source_forces_disputed(tmp_path, capsys, sites):
    cid = run(capsys, tmp_path, "new", CLAIM)["id"]
    for name in ("gazette", "council", "blog"):
        run(capsys, tmp_path, "add", cid, sites[name], "--fetcher", "plain")
    run(capsys, tmp_path, "stance", cid, "1", "supports", "--quote", "buses will be free for all riders from 1 January")
    run(capsys, tmp_path, "stance", cid, "2", "supports",
        "--quote", "travel on all Riverside bus routes will be free for everyone")
    run(capsys, tmp_path, "stance", cid, "3", "contradicts",
        "--quote", "free buses are only for residents over 60 and under 18 from January")

    code, err = fail(capsys, tmp_path, "verdict", cid, "supported", "--why", "Two outlets say the buses are free.")
    assert code == 2 and "disputed" in err
    out = run(capsys, tmp_path, "verdict", cid, "disputed",
              "--why", "The council and the Gazette say free for everyone; a ratepayers' blog says only under-18s and over-60s.")
    assert out["verdict"]["label"] == "disputed"


def test_new_evidence_reopens_a_decided_case(tmp_path, capsys, sites):
    cid = run(capsys, tmp_path, "new", CLAIM)["id"]
    run(capsys, tmp_path, "add", cid, sites["gazette"], "--fetcher", "plain")
    run(capsys, tmp_path, "verdict", cid, "unclear", "--why", "Only one source so far, need a second.")
    run(capsys, tmp_path, "add", cid, sites["council"], "--fetcher", "plain")
    assert run(capsys, tmp_path, "show", cid)["verdict"] is None


def test_unreachable_source_is_skipped_not_fatal(tmp_path, capsys, sites):
    cid = run(capsys, tmp_path, "new", CLAIM)["id"]
    main(["--home", str(tmp_path), "add", cid, "http://127.0.0.1:9/nothing", sites["gazette"], "--fetcher", "plain"])
    captured = capsys.readouterr()
    assert "skipped http://127.0.0.1:9/nothing" in captured.err
    assert run(capsys, tmp_path, "list")[0]["sources"] == 1
