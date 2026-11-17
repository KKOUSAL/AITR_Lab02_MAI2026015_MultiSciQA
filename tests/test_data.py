import json

import pytest

from src.data import (PROTOCOL, ROOT, assert_no_leak, build_prompt, join_context, load_items,
                      load_protocol, split_sentences)

CFG = load_protocol()
RAW = json.loads((ROOT / CFG["data"]["items"]).read_text())


def test_protocol_hash_enforced(tmp_path):
    p = tmp_path / PROTOCOL.name
    p.write_text(PROTOCOL.read_text() + "\n# edited\n")
    with pytest.raises(RuntimeError):
        load_protocol(p)


def test_split_sizes_disjoint_and_complete():
    test, dev = load_items(CFG, "test"), load_items(CFG, "dev")
    t, d = {x["pmid"] for x in test}, {x["pmid"] for x in dev}
    assert len(t) == 500 and len(d) == 500 and not (t & d) and (t | d) == set(RAW)


def test_test_ids_match_official_ground_truth():
    gt = json.loads((ROOT / "data/raw/pubmedqa_repo/data/test_ground_truth.json").read_text())
    test = load_items(CFG, "test")
    assert {x["pmid"]: x["gold"] for x in test} == gt


@pytest.mark.parametrize("template", ["P0"])
def test_no_leakage_any_item_any_template(template):
    """Leakage unit test over all 1,000 items (P07 checklist)."""
    for split in ("test", "dev"):
        for it in load_items(CFG, split):
            prompt = build_prompt(it["question"], join_context(it["contexts"], CFG), CFG, template)
            assert_no_leak(prompt, RAW[it["pmid"]])
            for section in RAW[it["pmid"]]["LABELS"]:   # section headers are excluded
                assert f"{section}:" not in prompt


def test_leak_detector_fires():
    rec = {"LONG_ANSWER": "Statins reduce risk."}
    with pytest.raises(AssertionError):
        assert_no_leak("... Statins reduce risk. ...", rec)


def test_items_carry_only_allowed_fields():
    it = load_items(CFG, "dev", limit=1)[0]
    assert set(it) == {"pmid", "question", "contexts", "gold"}


def test_sentence_split_is_lossless_up_to_whitespace():
    for it in load_items(CFG, "test", limit=50):
        for c in it["contexts"]:
            assert " ".join(split_sentences(c)).split() == c.split()


def test_prompt_contains_question_and_context():
    it = load_items(CFG, "dev", limit=1)[0]
    ctx = join_context(it["contexts"], CFG)
    p = build_prompt(it["question"], ctx, CFG)
    assert it["question"] in p and ctx in p and "yes, no, or maybe" in p
