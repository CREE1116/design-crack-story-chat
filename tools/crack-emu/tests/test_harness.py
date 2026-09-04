"""Unit tests. Run: python3 -m pytest tests/ -q   (or: python3 tests/test_harness.py)"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crack_emulator import qa
from crack_emulator.activation import activate
from crack_emulator.config import Config
from crack_emulator.models import Session, Turn
from crack_emulator.parser import load_project

def _find_build() -> Path:
    """Prefer $CRACK_BUILD, else the example build shipped with this repo."""
    env = os.environ.get("CRACK_BUILD")
    if env:
        return Path(env)
    bundled = Path(__file__).resolve().parent / "fixtures" / "build"
    if bundled.is_dir():
        return bundled
    raise SystemExit("set CRACK_BUILD to a Crack build directory")


BUILD = _find_build()


def _project():
    return load_project(BUILD)


def _session(p):
    return Session(id="t", project_root=p.root, variant="safe")


def _rules(findings):
    return {f.rule for f in findings}


def _sep(project) -> str:
    """This project's dialogue separator, so fixtures are written in its dialect."""
    c = getattr(project, "contract", None)
    return (getattr(c, "dialogue_separators", None) or ["|"])[0] if c else "|"


def _declares(project, flag: str) -> bool:
    """True when this build's contract actually turns the rule on."""
    c = getattr(project, "contract", None)
    return bool(getattr(c, flag, False)) if c else True


# ── parser ────────────────────────────────────────────────────────

def test_parses_variants_and_entries():
    p = _project()
    assert {"safe", "unsafe", "default"} <= set(p.variants)
    assert len(p.entries("safe")) > 0
    assert all(e.keywords for e in p.entries("safe"))


def test_parses_roster_and_image_rule():
    """The current convention: a numbered roster plus `{인물}/{상황}.webp`.

    Legacy builds predate it and carry neither, so there is nothing to assert.
    """
    p = _project()
    if not p.characters:
        return
    assert p.character_numbers()
    assert p.image_rule.base_url and p.image_rule.base_url.startswith("https://")
    assert "s01" in p.image_rule.situation_codes


def test_shortcut_fence_is_stripped():
    p = _project()
    shortcuts = [x for v in p.variants for x in p.shortcut_list(v)]
    assert shortcuts, "no shortcuts parsed"
    assert all(not x.prompt.startswith("```") for x in shortcuts)


# ── activation ────────────────────────────────────────────────────

def test_keyword_matches_through_korean_particle():
    """A keyword still matches once a Korean particle is attached to it."""
    p, c = _project(), Config.load()
    entry = next(e for e in p.entries("safe") if e.keywords)
    kw = max(entry.keywords, key=len)
    hits = activate(p.entries("safe"), [], kw + "께 보고드립니다", c)
    assert any(h.entry.title == entry.title for h in hits)


def test_scan_depth_is_configurable():
    p, c = _project(), Config.load()
    kw = max((e.keywords[0] for e in p.entries("safe") if e.keywords), key=len)
    turns = [Turn(0, "assistant", kw + " 관련 장면."), Turn(1, "user", "네")]
    shallow = activate(p.entries("safe"), turns, "안녕", c.override({"keyword.scan_turns": 0}))
    deep = activate(p.entries("safe"), turns, "안녕", c.override({"keyword.scan_turns": 5}))
    assert len(deep) > len(shallow)


def test_max_entries_cap_is_applied():
    p, c = _project(), Config.load()
    text = " ".join(e.keywords[0] for e in p.entries("safe")[:6] if e.keywords)
    uncapped = activate(p.entries("safe"), [], text, c)
    capped = activate(p.entries("safe"), [], text, c.override({"keyword.max_entries": 2}))
    assert len(uncapped) > 2 and len(capped) == 2


# ── qa contract ───────────────────────────────────────────────────

def test_flags_user_impersonation():
    p = _project()
    if not _declares(p, "forbid_user_dialogue"):
        return  # this build declares no such rule
    r = qa.check(f'{{{{user}}}} {_sep(p)} "안녕하세요"', p, _session(p))
    assert "user_impersonation" in _rules(r)
    assert any(f.severity == qa.CRITICAL for f in r if f.rule == "user_impersonation")


def test_flags_meta_leak_without_angle_brackets():
    p = _project()
    r = qa.check("*knowledge_base 에 따르면 그렇다.*", p, _session(p))
    assert "meta_leak" in _rules(r)


def test_flags_unknown_character_and_situation():
    p = _project()
    if not p.character_numbers() or not p.image_rule.situation_codes:
        return  # legacy build without the numbered image convention
    base = p.image_rule.base_url or "https://example.invalid/"
    body = f'![X]({base}99/s99.webp)\nX | "안녕"'
    rules = _rules(qa.check(body, p, _session(p)))
    assert "image_unknown_character" in rules
    assert "image_unknown_situation" in rules


def test_flags_restricted_situation_code():
    p = _project()
    if not p.image_rule.restricted_codes:
        return  # this build declares no restricted situation codes
    code, allowed = next(iter(p.image_rule.restricted_codes.items()))
    outsider = next((n for n in sorted(p.character_numbers()) if n not in allowed), None)
    
    if outsider is None:
        return
    body = f'![x]({p.image_rule.base_url}{outsider}/{code}.webp)\nx | "네"'
    assert "image_restricted_code" in _rules(qa.check(body, p, _session(p)))


def test_flags_foreign_image_host():
    p = _project()
    if not p.image_rule.base_url:
        return
    body = '![x](https://elsewhere.invalid/01/s01.webp)\nx | "왔는가"'
    assert "image_bad_host" in _rules(qa.check(body, p, _session(p)))


def test_flags_user_echo_in_narration():
    p = _project()
    if not _declares(p, "forbid_user_dialogue"):
        return  # this build declares no such rule
    r = qa.check('*그는 "잘 부탁드립니다" 라고 한 말을 떠올린다.*', p, _session(p),
                 user_input='안녕하세요 "잘 부탁드립니다"')
    assert "user_echo" in _rules(r)


def test_flags_numbered_choices():
    p = _project()
    if not _declares(p, "forbid_numbered_choices"):
        return  # this build declares no such rule
    assert "numbered_choices" in _rules(qa.check("1. 인사한다\n2. 도망친다", p, _session(p)))


def test_flags_missing_hud():
    p = _project()
    c = getattr(p, "contract", None)
    if c and (c.hud_fence is None or not c.hud_required):
        return  # this build declares no mandatory status window
    sep = (getattr(c, "dialogue_separators", None) or ["|"])[0] if c else "|"
    assert "hud_missing" in _rules(qa.check(f'라임 {sep} "네"', p, _session(p)))


def test_hud_is_not_required_for_ooc():
    p = _project()
    rules = _rules(qa.check("해설입니다.", p, _session(p), user_input="/OOC 설명해줘"))
    assert "hud_missing" not in rules


def test_narrative_shortcut_still_requires_hud():
    """A scene shortcut is an ordinary turn; only a panel shortcut skips the HUD."""
    from crack_emulator.models import Shortcut
    p = _project()
    narrative = Shortcut(id="sc_scene", name="야근", description="",
                         prompt="- 심야 사무실로 장면 전환\n- 소설 문체로 서술",
                         order=0, source="t")
    panel = Shortcut(id="sc_panel", name="상태창", description="",
                     prompt="- 롤플레잉을 즉시 중단하고 오직 아래 코드블럭만 출력",
                     order=1, source="t")
    c = getattr(p, "contract", None)
    if c and (c.hud_fence is None or not c.hud_required):
        return
    sep = (getattr(c, "dialogue_separators", None) or ["|"])[0] if c else "|"
    assert "hud_missing" in _rules(
        qa.check(f'하연 {sep} "네"', p, _session(p), shortcut=narrative))
    assert "hud_missing" not in _rules(qa.check("패널", p, _session(p), shortcut=panel))


def test_rules_follow_the_build_not_the_house_style():
    """The same text must be judged by each project's own contract."""
    p = _project()
    c = getattr(p, "contract", None)
    assert c is not None, "project carries no detected contract"
    # Whatever was detected has to be backed by a line in the prompt.
    for key in c.detected:
        assert c.detected[key], f"{key} detected with no evidence"


def test_clean_response_passes():
    p = _project()
    if not p.character_numbers():
        return  # legacy build without a numbered roster
    num = sorted(p.character_numbers())[0]
    sit = (p.image_rule.situation_codes or ["s01"])[0]
    base = p.image_rule.base_url or "https://example.invalid/"
    body = (
        "*그가 자리에서 일어난다.*\n\n"
        f"![x]({base}{num}/{sit}.webp)\n"
        f'x {_sep(p)} "어서 와요."\n\n'
        "```Info\n[신입]: x\n[실적]: x\n[현장]: x\n[관계]: x\n[상황]: x\n```"
    )
    findings = qa.check(body, p, _session(p))
    assert qa.summarize(findings)["passed"], [f.to_dict() for f in findings]


def test_agent_self_response_mode():
    """Engine.turn with injected reply must record the turn and run QA without external API."""
    from crack_emulator.engine import Engine
    from crack_emulator.llm import make_client
    from crack_emulator.config import Config
    from crack_emulator.session import Store
    import tempfile
    import shutil

    p = _project()
    cfg = Config.load()
    client = make_client(cfg, provider="agent")
    temp_dir = tempfile.mkdtemp()
    try:
        store = Store(temp_dir)
        eng = Engine(p.root, cfg, client, store=store, variant="safe")
        session = eng.start("test_agent_sess")
        res = eng.turn(session, "안녕", reply='*테스트 지문*\n\n라임 | "안녕하세요"')
        assert res.reply == '*테스트 지문*\n\n라임 | "안녕하세요"'
        assert len(session.turns) == 3  # prologue + user + assistant
        assert res.turn_index == 2
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"  ok   {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    raise SystemExit(1 if failed else 0)


# ── agreement with the convention of record ───────────────────────

def test_matches_crack_sync_parser():
    """crack_sync.py is what actually uploads a build; parse it the same way.

    Skipped when the sync tool is not alongside (crack-emu also ships alone).
    """
    sync_dir = None
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "sync" / "crack_sync.py"
        if candidate.is_file():
            sync_dir = candidate.parent
            break
    if sync_dir is None:
        return
    sys.path.insert(0, str(sync_dir))
    try:
        import crack_sync  # type: ignore
    except Exception:
        return

    from crack_emulator.parser import parse_keyword_book

    checked = 0
    for kb in sorted(BUILD.glob("keyword-book*.md")):
        text = kb.read_text(encoding="utf-8")
        mine_e, mine_s = parse_keyword_book(text, kb.name)
        theirs_e, theirs_s = crack_sync.parse_keyword_book(text)
        assert [(e.title, e.keywords, e.content) for e in mine_e] == \
               [(e.title, e.keywords, e.content) for e in theirs_e], kb.name
        assert [(x.id, x.name, x.description) for x in mine_s] == \
               [(x.id, x.name, x.description) for x in theirs_s], kb.name
        checked += 1
    assert checked, "no keyword book found to cross-check"


def test_shortcut_name_carries_no_slash():
    """Crack's UI prepends the slash; a stored `/name` becomes `//name`."""
    p = _project()
    for v in p.variants:
        for s in p.shortcut_list(v):
            assert not s.name.startswith("/"), f"{s.id} kept its slash"


def test_slash_input_still_matches_a_shortcut():
    from crack_emulator.activation import match_shortcut
    p = _project()
    shortcuts = p.shortcut_list("default") or p.shortcut_list("safe")
    if not shortcuts:
        return
    target = shortcuts[0]
    found, _rest = match_shortcut("/" + target.name, shortcuts)
    assert found is not None and found.id == target.id
