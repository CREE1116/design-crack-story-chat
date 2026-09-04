"""Parse a Crack `build/` directory into a Project.

Recognised layout (as produced by the design-crack-story-chat skill):

    build/
      integrated-prompt-safe.md      main prompt, `safe` variant
      integrated-prompt-unsafe.md    main prompt, `unsafe` variant
      keyword-book.md                keyword book, `default` variant
      keyword-book-safe.md
      keyword-book-unsafe.md
      prologue.md                    assistant turn 0
      start-prompt.md                opening situation + input parse contract
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from pathlib import Path as pathlib_Path

from . import contract as contract_mod
from .models import (Character, ImageRule, KeywordEntry, Project, Shortcut,
                     StartSet)

_H2 = re.compile(r"^##[ \t]+(.+?)[ \t]*$", re.M)
_ROSTER = re.compile(r"^▶(?:(\d{2})\.)?([^:：\[]+)[:：]\s*\[(.*)\]\s*$", re.M)
_IMG_TEMPLATE = re.compile(r"!\[[^\]]*\]\((https?://[^)]*?)\{")
_SITUATION = re.compile(r"상황\s*=\s*((?:s\d{2}\S*\s*)+)")
_SIT_CODE = re.compile(r"(s\d{2})")
_RESTRICT = re.compile(r"(s\d{2})\s*은?\s*(\d{2})\s*[~-]\s*(\d{2})\s*만")
_FENCE = re.compile(r"^```[a-zA-Z]*\n(.*?)\n```\s*$", re.S)


class ParseError(Exception):
    pass


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _split_h2(text: str) -> list[tuple[str, str]]:
    """Split markdown on level-2 headings -> [(heading, body), ...]."""
    matches = list(_H2.finditer(text))
    out = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((m.group(1).strip(), text[m.end():end].strip("\n")))
    return out


def _field(body: str, label: str) -> tuple[str, str]:
    """Pull `- {label}: value` out of a block.

    Returns (inline value, remaining text after the field line). A field whose
    value is empty carries its payload on the following lines instead.
    """
    pat = re.compile(rf"^-[ \t]*{re.escape(label)}[ \t]*:[ \t]*(.*)$", re.M)
    m = pat.search(body)
    if not m:
        return "", body
    return m.group(1).strip(), body[m.end():].lstrip("\n")


def _strip_fence(text: str) -> str:
    t = text.strip()
    if not t.startswith("```") or not t.endswith("```"):
        return text
    nl = t.find("\n")
    if nl == -1 or len(t) < nl + 4:
        return text
    return t[nl + 1:-3].rstrip()


# ── keyword book ──────────────────────────────────────────────────
# Kept deliberately in step with `tools/sync/crack_sync.py`, which is the
# convention of record: it is the parser that actually pushes a build into
# Crack. A harness that read these files differently from the tool that
# uploads them would be measuring a build nobody ships.

_SC_SECTION = re.compile(
    r"^#+\s*(?:Shortcuts?|단축어|Shortcut\s+`?[a-zA-Z0-9_-]+`?)\b",
    re.M | re.I)
_HEADING = re.compile(r"^(#{1,3})\s+(.+)$", re.M)
_META_HEADING = re.compile(
    r"^(?:등록 순서|3슬롯|Entry text|입력 본문|본문|내용|Shortcuts?|단축어)\b", re.I)
_KW_LINE = re.compile(r"^-\s*(?:키워드|keywords?):\s*(.+)$", re.M | re.I)
_COMMENT = re.compile(r"<!--.*?-->", re.S)


def parse_keywords(raw: str | None) -> list[str]:
    if raw is None:
        return []
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]
    return [item.strip().strip("'\"`") for item in raw.split(",") if item.strip()]


def parse_keyword_body(text: str) -> str:
    m = re.search(r"^##\s+(?:Entry text|입력 본문|본문|내용)\s*\n(.*?)(?=^## |\Z)",
                  text, re.M | re.S | re.I)
    if m:
        return _COMMENT.sub("", m.group(1)).strip()

    m = re.search(r"^-\s*(?:내용|본문|entry|body):\s*\n?(.*?)(?=^-\s*[a-zA-Z가-힣_]+:|\Z)",
                  text, re.M | re.S | re.I)
    if m:
        return _COMMENT.sub("", m.group(1)).strip()

    body_lines: list[str] = []
    found_kw = False
    for line in text.splitlines():
        if re.match(r"^-\s*(?:키워드|keywords?):", line, re.I):
            found_kw = True
            continue
        if found_kw:
            if re.match(r"^-\s*(?:activation|setting|when):", line, re.I):
                continue
            body_lines.append(line)
    if body_lines:
        return _COMMENT.sub("", "\n".join(body_lines)).strip()
    return ""


def _clean_title(raw: str) -> str:
    t = re.sub(r"^`?kb\.[^`\s]+`?\s*—?\s*", "", raw.strip())
    return re.sub(r"^[0-9]+\.\s*", "", t).strip()


def parse_keyword_book(text: str, source: str) -> tuple[list[KeywordEntry], list[Shortcut]]:
    entries: list[KeywordEntry] = []
    shortcuts: list[Shortcut] = []

    sc = _SC_SECTION.search(text)
    kb_part, sc_part = (text[: sc.start()], text[sc.start():]) if sc else (text, "")

    heads = [m for m in _HEADING.finditer(kb_part)
             if not _META_HEADING.match(m.group(2).strip())]
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(kb_part)
        block = kb_part[m.start():end]
        kw = _KW_LINE.search(block)
        if not kw:
            continue
        entries.append(KeywordEntry(
            title=_clean_title(m.group(2)),
            keywords=parse_keywords(kw.group(1)),
            content=parse_keyword_body(block),
            order=len(entries),
            source=source,
        ))

    if sc_part:
        heads = list(re.finditer(
            r"^#+\s+(?:Shortcut\s+`?([^`\n]+)`?|sc\.([a-zA-Z0-9_-]+)|([^#\n]+))$",
            sc_part, re.M | re.I))
        valid = []
        for m in heads:
            h = m.group(0).strip()
            if re.match(r"^#+\s*(?:Shortcuts?|단축어)(?:\s*\(.*?\))?\s*$", h, re.I):
                continue
            if re.search(r"^##\s+(?:Shortcut prompt|프롬프트|내용)\b", h, re.I):
                continue
            valid.append(m)

        for i, m in enumerate(valid):
            end = valid[i + 1].start() if i + 1 < len(valid) else len(sc_part)
            block = sc_part[m.start():end]
            sc_id = (m.group(1) or m.group(2) or m.group(3) or "shortcut").strip()
            name_m = re.search(r"^-\s*(?:name|이름):\s*(.+)$", block, re.M | re.I)
            desc_m = re.search(r"^-\s*(?:description|설명):\s*(.+)$", block, re.M | re.I)
            prompt_m = re.search(r"^##\s+(?:Shortcut prompt|프롬프트)\s*\n(.*?)(?=^#|\Z)",
                                 block, re.M | re.S | re.I)
            if not prompt_m:
                prompt_m = re.search(
                    r"^-\s*(?:prompt|프롬프트):\s*\n?(.*?)"
                    r"(?=^-\s*(?:name|이름|desc|description|설명):|^#|\Z)",
                    block, re.M | re.S | re.I)
            # Crack's UI prepends the slash itself, so the stored name carries none.
            raw_name = (name_m.group(1).strip() if name_m else sc_id)
            shortcuts.append(Shortcut(
                id=sc_id,
                name=raw_name.lstrip("/"),
                description=desc_m.group(1).strip() if desc_m else "",
                prompt=_strip_fence(
                    _COMMENT.sub("", prompt_m.group(1)).strip() if prompt_m else ""),
                order=len(shortcuts),
                source=source,
                declared_slash=raw_name.startswith("/"),
            ))
    return entries, shortcuts


def parse_roster(main_prompt: str) -> list[Character]:
    out = []
    for m in _ROSTER.finditer(main_prompt):
        num, name, body = m.group(1), m.group(2).strip(), m.group(3)
        out.append(Character(number=num, name=name, fields=[f.strip() for f in body.split("｜")]))
    return out


def parse_image_rule(main_prompt: str) -> ImageRule:
    base = None
    m = _IMG_TEMPLATE.search(main_prompt)
    if m:
        base = m.group(1)
    codes: list[str] = []
    ms = _SITUATION.search(main_prompt)
    if ms:
        seen: set[str] = set()
        for code in _SIT_CODE.findall(ms.group(1)):
            if code not in seen:
                seen.add(code)
                codes.append(code)
    restricted: dict[str, list[str]] = {}
    for code, lo, hi in _RESTRICT.findall(main_prompt):
        restricted[code] = [f"{n:02d}" for n in range(int(lo), int(hi) + 1)]
    return ImageRule(base_url=base, situation_codes=codes, restricted_codes=restricted)


def parse_hud_example(main_prompt: str) -> str | None:
    """The sample status window, whether or not its fence carries a label."""
    m = re.search(r"^```Info\n(.*?)\n```", main_prompt, re.S | re.M)
    if m:
        return m.group(1)
    sec = re.search(r"^#+\s*[^\n]*상태\s?창[^\n]*$", main_prompt, re.M)
    if sec:
        blocks = re.findall(r"^```[^\n]*\n(.*?)\n```", main_prompt[sec.end():], re.S | re.M)
        for block in blocks:
            if "[" in block:
                return block
    return None


def parse_start_prompt(text: str) -> tuple[str, str]:
    """-> (opening situation, input parse contract).

    Section titles vary between projects and the numbering does not line up:
    one file opens with `## 1. 첫 턴 상황 압력` while another puts `## 1. 배속 및 사수`
    first and the situation second. Match on what the heading says, never on
    its number, or a roster section gets read as the opening scene.
    """
    parts = _split_h2(text)
    opening = parse = ""
    for heading, body in parts:
        title = re.sub(r"^\d+[.)]\s*", "", heading).strip()
        if not opening and ("첫 턴" in title or "첫 상황" in title
                            or "상황 압력" in title or "오프닝" in title):
            opening = body.strip()
        elif not parse and ("파싱" in title or "입력 계약" in title
                            or "parse" in title.lower()):
            parse = body.strip()
    if not opening:
        # No recognisable heading: the longest section is the scene.
        opening = max((b.strip() for _h, b in parts), key=len, default=text.strip())
    return opening, parse


# A story may ship several openings. `start-sets/` is the current name;
# `departments/` is the earlier one and is still read.
START_SET_DIRS = ("start-sets", "departments")


def _set_meta(folder: pathlib_Path, index: int) -> dict:
    """Read `meta.md`: first heading is the title, `- key: value` lines are settings.

    Everything is optional. Without the file a set still works, taking its name
    from the folder and its order from the directory listing.
    """
    fallback = re.sub(r"^\d+[_-]", "", folder.name)
    meta = {"title": fallback, "description": "", "default": False, "order": index}
    path = folder / "meta.md"
    if not path.is_file():
        return meta
    desc: list[str] = []
    for line in _read(path).splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            if meta["title"] == fallback:
                meta["title"] = stripped.lstrip("#").strip() or fallback
            continue
        m = re.match(r"^-\s*(default|order|title)\s*:\s*(.+)$", stripped, re.I)
        if m:
            key, value = m.group(1).lower(), m.group(2).strip()
            if key == "default":
                meta["default"] = value.lower() in {"true", "yes", "1", "y"}
            elif key == "order":
                try:
                    meta["order"] = int(value)
                except ValueError:
                    pass
            else:
                meta["title"] = value
            continue
        if stripped:
            desc.append(stripped)
    meta["description"] = " ".join(desc).strip()
    return meta


def load_start_sets(project_root: pathlib_Path) -> list[StartSet]:
    """Discover selectable openings next to the build directory."""
    out: list[StartSet] = []
    root = project_root.parent if project_root.name == "build" else project_root
    for dirname in START_SET_DIRS:
        base = root / dirname
        if not base.is_dir():
            continue
        for folder in sorted(p for p in base.iterdir() if p.is_dir()):
            prologue_p = folder / "prologue.md"
            start_p = folder / "start-prompt.md"
            if not prologue_p.is_file() and not start_p.is_file():
                continue
            opening, contract = (parse_start_prompt(_read(start_p))
                                 if start_p.is_file() else ("", ""))
            meta = _set_meta(folder, len(out))
            out.append(StartSet(
                id=folder.name,
                title=meta["title"],
                description=meta["description"],
                prologue=_read(prologue_p).strip() if prologue_p.is_file() else "",
                start_prompt=_read(start_p).strip() if start_p.is_file() else "",
                opening_situation=opening,
                parse_contract=contract,
                source=str(folder.relative_to(root)),
                is_default=bool(meta["default"]),
                order=int(meta["order"]),
            ))
        if out:
            break
    out.sort(key=lambda x: (x.order, x.id))
    if out and not any(x.is_default for x in out):
        out[0].is_default = True
    return out


def _variant_of(stem: str, prefix: str) -> str:
    rest = stem[len(prefix):].lstrip("-")
    return rest or "default"


def load_project(root: str | Path) -> Project:
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise ParseError(f"build directory not found: {root}")

    main_prompt: dict[str, str] = {}
    for path in sorted(root.glob("integrated-prompt*.md")):
        main_prompt[_variant_of(path.stem, "integrated-prompt")] = _read(path)
    if not main_prompt:
        raise ParseError(f"no integrated-prompt*.md in {root}")

    kw_entries: dict[str, list[KeywordEntry]] = {}
    kw_shortcuts: dict[str, list[Shortcut]] = {}
    for path in sorted(root.glob("keyword-book*.md")):
        variant = _variant_of(path.stem, "keyword-book")
        entries, shortcuts = parse_keyword_book(_read(path), path.name)
        kw_entries[variant] = entries
        kw_shortcuts[variant] = shortcuts
    if not kw_entries:
        raise ParseError(f"no keyword-book*.md in {root}")

    prologue_path = root / "prologue.md"
    start_path = root / "start-prompt.md"
    prologue = _read(prologue_path) if prologue_path.exists() else ""
    start_prompt_raw = _read(start_path).strip() if start_path.exists() else ""
    opening, contract = parse_start_prompt(start_prompt_raw) if start_prompt_raw else ("", "")

    reference = main_prompt.get("safe") or next(iter(main_prompt.values()))
    variants = sorted(set(main_prompt) | set(kw_entries))

    start_sets = load_start_sets(root)
    if prologue.strip() or opening.strip():
        # build/ holds a copy of whichever set was materialised; keep it visible
        # so a project without a start-sets/ directory still runs, but mark it
        # generated so nobody edits it by mistake.
        already = next((x for x in start_sets if x.prologue == prologue.strip()), None)
        start_sets.insert(0, StartSet(
            id="build",
            title="build (현재 반영본)" + (f" = {already.title}" if already else ""),
            description="build/ 에 놓인 사본. 정본은 start-sets/ 입니다.",
            prologue=prologue.strip(), start_prompt=start_prompt_raw,
            opening_situation=opening,
            parse_contract=contract, source="build",
            is_default=not start_sets, order=-1, generated=True,
        ))

    return Project(
        root=str(root),
        name=root.parent.name if root.name == "build" else root.name,
        variants=variants,
        main_prompt=main_prompt,
        keyword_entries=kw_entries,
        shortcuts=kw_shortcuts,
        prologue=prologue,
        opening_situation=opening,
        parse_contract=contract,
        characters=parse_roster(reference),
        image_rule=parse_image_rule(reference),
        hud_example=parse_hud_example(reference),
        start_sets=start_sets,
        contract=contract_mod.load(reference, parse_hud_example(reference), root),
    )


# ── build integrity lint ──────────────────────────────────────────

def lint(project: Project, max_entry_chars: int = 400,
         target_entry_chars: int = 360, max_slots: int = 3) -> list[dict]:
    """Static checks on the authored build, before any model is called."""
    findings: list[dict] = []

    def add(severity: str, rule: str, message: str, **extra):
        findings.append({"severity": severity, "rule": rule, "message": message, **extra})

    numbers = project.character_numbers()
    names = {c.name for c in project.characters}
    slash_names: dict[str, str] = {}
    empty_shortcuts: set[str] = set()

    for variant in project.variants:
        entries = project.entries(variant)
        seen: dict[str, str] = {}
        for e in entries:
            if e.char_count > max_entry_chars:
                add("error", "entry_too_long",
                    f"{e.title}: 내용 {e.char_count}자 (상한 {max_entry_chars})",
                    variant=variant, entry=e.title)
            elif e.char_count > target_entry_chars:
                add("info", "entry_near_limit",
                    f"{e.title}: 내용 {e.char_count}자 (권장 {target_entry_chars} 초과)",
                    variant=variant, entry=e.title)
            if not e.keywords:
                add("error", "entry_no_keyword", f"{e.title}: 키워드 없음",
                    variant=variant, entry=e.title)
            if len(e.keywords) > 5:
                add("warn", "entry_keyword_overflow",
                    f"{e.title}: 키워드 {len(e.keywords)}개 (크랙 상한 5)",
                    variant=variant, entry=e.title)
            for k in e.keywords:
                norm = unicodedata.normalize("NFKC", k).casefold()
                if norm in seen and seen[norm] != e.title:
                    add("warn", "keyword_collision",
                        f"키워드 '{k}' 가 '{seen[norm]}' 와 '{e.title}' 양쪽에 있음",
                        variant=variant, entry=e.title)
                seen[norm] = e.title

        for s in project.shortcut_list(variant):
            if s.declared_slash:
                slash_names[s.id] = s.name
            if not s.prompt.strip():
                empty_shortcuts.add(s.id)

    # The skill's image-output rules are explicit: adult scene codes live only in
    # the keyword book. In the always-on prompt they burn budget and invite the
    # model to call an A-code in an everyday scene.
    for variant in project.variants:
        for m in re.finditer(r"(?<![A-Za-z0-9])A\d{2}(?!\d)", project.prompt(variant)):
            add("error", "adult_code_in_main_prompt",
                f"메인 프롬프트에 성인 코드 {m.group(0)} 노출 — "
                f"키워드북 성애 모듈 본문에만 적을 것",
                variant=variant, keyword=m.group(0))
            break

    for sc_id, sc_name in sorted(slash_names.items()):
        add("warn", "shortcut_name_slash",
            f"{sc_id}: name 이 '/' 로 시작 — 크랙 UI 가 슬래시를 자동으로 붙이므로 "
            f"'//{sc_name}' 로 두 번 입력됨. 슬래시를 뺄 것", entry=sc_id)
    for sc_id in sorted(empty_shortcuts):
        add("error", "shortcut_empty", f"{sc_id}: prompt 비어 있음", entry=sc_id)

    if not project.prologue.strip():
        add("error", "missing_prologue", "prologue.md 없음 또는 비어 있음")
    if not project.opening_situation.strip():
        add("error", "missing_opening", "start-prompt.md 의 첫 상황 섹션을 못 찾음")
    # A numbered roster only has to exist when the images cite numbers. A build
    # whose image convention is slug-based owes no `▶NN.이름` table.
    numbered_images = getattr(project.contract, "image_id_kind", None) == "numbered"
    if not project.image_rule.base_url and numbered_images:
        add("warn", "no_image_base", "메인 프롬프트에서 이미지 base URL 을 못 찾음")
    if not project.characters:
        if numbered_images:
            add("error", "no_roster",
                "이미지가 인물번호를 인용하는데 명부(▶NN.이름)가 없음")
        else:
            add("info", "no_roster",
                "인물 명부(▶NN.이름) 없음 — 이 빌드는 번호 기반 이미지가 아니라 검사 생략")

    # A keyword that is a substring of a longer word appearing in the build will
    # fire on that longer word. `라임` inside `슬라임` is the canonical case.
    # Slot economics. Crack loads at most `max_slots` entries per turn and drops
    # from the bottom of the list, so registration order is a real design
    # decision: an entry that fires constantly and sits high permanently costs
    # one of three slots, and a priority module registered low gets dropped in
    # exactly the turn it exists for.
    priority = re.compile(r"(19금|성애|🔞|결전|특수 ?연출|키스|스킨십)")
    hud_labels = {
        unicodedata.normalize("NFKC", t).casefold()
        for t in re.findall(r"\[([^\]\n]{1,14})\]", project.hud_example or "")
    }
    always_on: dict[tuple[str, str], set[str]] = {}
    for variant in project.variants:
        entries = project.entries(variant)
        for rank, e in enumerate(entries, start=1):
            if priority.search(e.title) and rank > max_slots:
                add("error", "priority_module_low",
                    f"'{e.title}' 가 {rank}번째 등록 — 슬롯 {max_slots}개 밖이라 "
                    f"정작 필요한 턴에 드롭됨. 목록 최상단으로 옮길 것",
                    variant=variant, entry=e.title, rank=rank)

        # A trigger that matches the HUD's own furniture fires on every turn.
        # Only the structural labels count: the sample values inside the example
        # HUD (a character's name, this scene's item) are content, not template.
        for e in entries:
            for kw in e.keywords:
                nk = unicodedata.normalize("NFKC", kw).casefold()
                if len(nk) >= 2 and nk in hud_labels:
                    always_on[(kw, e.title)] = always_on.get((kw, e.title), set())
                    always_on[(kw, e.title)].add(variant)

    for (kw, title), variants_hit in sorted(always_on.items()):
        add("error", "always_on_trigger",
            f"'{title}' 의 키워드 '{kw}' 가 상태창 고정 항목명 — "
            f"매 턴 발동해 3슬롯 중 1개를 영구 점유함",
            variant=",".join(sorted(variants_hit)), entry=title, keyword=kw)

    hazards: dict[tuple[str, str], tuple[set[str], set[str]]] = {}
    for variant in project.variants:
        corpus = "\n".join(
            [project.prologue, project.opening_situation, project.prompt(variant)]
            + [e.content for e in project.entries(variant)]
        )
        corpus_n = unicodedata.normalize("NFKC", corpus).casefold()
        for e in project.entries(variant):
            for kw in e.keywords:
                nk = unicodedata.normalize("NFKC", kw).casefold()
                if len(nk) < 2:
                    continue
                hosts = _false_trigger_hosts(corpus_n, nk)
                if not hosts:
                    continue
                key = (kw, e.title)
                acc = hazards.setdefault(key, (set(), set()))
                acc[0].update(hosts)
                acc[1].add(variant)
    for (kw, title), (hosts, variants_hit) in sorted(hazards.items()):
        add("warn", "keyword_substring_hazard",
            f"'{kw}' 가 {sorted(hosts)[:3]} 안에 묻혀 있어 "
            f"'{title}' 가 의도치 않게 발동함",
            variant=",".join(sorted(variants_hit)), entry=title, keyword=kw)

    # Every start set's prologue, not just the copy sitting in build/. A wrong
    # number here is invisible in review — the markdown reads correctly and only
    # the rendered image is somebody else.
    name_by_number = {c.number: c.name for c in project.characters if c.number}
    sources = [(x.id, x.prologue) for x in project.start_sets] or \
              [("build", project.prologue)]
    for set_id, text in sources:
        for name, num, sit in _prologue_images_in(text):
            where = f"{set_id}/prologue.md"
            if num and num not in numbers:
                add("error", "prologue_unknown_number",
                    f"{where}: 이미지 인물번호 {num} 가 명부에 없음",
                    entry=name, start_set=set_id)
            elif num and name and name_by_number.get(num) and name != name_by_number[num]:
                expected = next((n for n, nm in name_by_number.items() if nm == name), None)
                add("error", "prologue_image_wrong_number",
                    f"{where}: '{name}' 이미지가 {num}번을 부르는데 "
                    f"{num}번은 '{name_by_number[num]}' 입니다"
                    + (f". '{name}' 은 {expected}번" if expected else ""),
                    entry=name, start_set=set_id)
            if sit and project.image_rule.situation_codes \
                    and sit not in project.image_rule.situation_codes:
                add("error", "prologue_unknown_situation",
                    f"{where}: 이미지 상황코드 {sit} 가 정의에 없음",
                    entry=name, start_set=set_id)
            allowed = project.image_rule.restricted_codes.get(sit or "")
            if allowed is not None and num and num not in allowed:
                add("error", "prologue_restricted_code",
                    f"{where}: {sit} 는 인물 {allowed[0]}~{allowed[-1]} 만 보유 (요청 {num})",
                    entry=name, start_set=set_id)

    # Each set needs both halves of the pair, or turn one runs on half a setup.
    for x in project.start_sets:
        if x.generated:
            continue
        if not x.prologue.strip():
            add("error", "start_set_no_prologue",
                f"{x.id}: prologue.md 가 없거나 비어 있음", start_set=x.id)
        if not x.start_prompt.strip():
            add("error", "start_set_no_start_prompt",
                f"{x.id}: start-prompt.md 가 없거나 비어 있음", start_set=x.id)
        elif not x.opening_situation.strip():
            add("warn", "start_set_no_opening",
                f"{x.id}: start-prompt.md 에서 첫 턴 상황 절을 못 찾음", start_set=x.id)
    return findings


_WORD = re.compile(r"[0-9A-Za-z\uac00-\ud7a3]+")

# A keyword followed by one of these is the match the author intended:
# Korean attaches particles directly to the noun, so `바알은` triggering `바알`
# is correct behaviour, not a false positive.
_PARTICLES = (
    "은", "는", "이", "가", "을", "를", "의", "도", "만", "과", "와", "야", "아", "여",
    "에", "에서", "에게", "에선", "에는", "에도", "에만", "으로", "로", "부터", "까지",
    "처럼", "보다", "라도", "이라도", "나", "이나", "께", "께서", "님", "씨", "랑", "이랑",
    "하고", "다", "이다", "인", "인데", "이며", "며", "들", "등", "쯤", "이라", "라",
    "님은", "님이", "님을", "님의", "님께", "님도", "님과",
)


def _false_trigger_hosts(corpus: str, keyword: str) -> set[str]:
    """Words containing `keyword` in a way the author almost certainly did not mean.

    A host is ignored when it is just the keyword plus a Korean particle; it is
    reported when the keyword is buried inside a different word (`라임` inside
    `슬라임`, `니아` inside `라비니아`).
    """
    out = set()
    for w in _WORD.findall(corpus):
        if len(w) <= len(keyword) or keyword not in w:
            continue
        if w.startswith(keyword) and w[len(keyword):] in _PARTICLES:
            continue
        out.add(w)
    return out


_PROLOGUE_IMG = re.compile(r"!\[([^\]]*)\]\((https?://[^)]+)\)")


def _prologue_images_in(text: str) -> list[tuple[str, str | None, str | None]]:
    out = []
    for label, url in _PROLOGUE_IMG.findall(text):
        m = re.search(r"/(\d{2})/(s\d{2})\.webp", url)
        out.append((label.strip(), m.group(1) if m else None, m.group(2) if m else None))
    return out
