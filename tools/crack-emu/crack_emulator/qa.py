"""Validate a model response against the build's output contract.

Every rule traces back to a clause in `# 8. 출력 계약 & 상태창(HUD)` and
`# 1. 필수 추론 및 사칭·에코 방지 잠금` of the integrated prompt, so a finding
always points at authored text the user can go read.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from .models import Project, Session, Shortcut

CRITICAL, ERROR, WARN, INFO = "critical", "error", "warn", "info"

_IMG = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$")
_IMG_ANY = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
def _dialogue_re(separators: list[str]) -> re.Pattern:
    """Match this project's dialogue line, whatever separator it declared."""
    seps = separators or ["|", ":"]
    cls = "".join(re.escape(x) for x in set(seps) | ({"｜"} if "|" in seps else set())
                  | ({"："} if ":" in seps else set()))
    return re.compile(rf"^([^{cls}\n]{{1,40}})\s*[{cls}]\s*[\"“](.*)[\"”]\s*$")


_DIALOGUE = _dialogue_re(["|"])   # replaced per project inside check()
def _hud_re(label: str) -> re.Pattern:
    if label == "":
        return re.compile(r"```[ \t]*\n(.*?)\n```", re.S)
    return re.compile(rf"```{re.escape(label)}\s*\n(.*?)\n```", re.S)


_HUD = _hud_re("Info")
_FENCE_LINE = re.compile(r"^```")
_NUMBERED = re.compile(r"^\s*(?:[1-3]|[①-③])[.)]\s+\S")
_CHOICE_PROMPT = re.compile(r"(어떻게 (?:할|하시겠)|무엇을 (?:할|하시겠)|선택하(?:세요|십시오))")
# Internal scaffolding that must never surface in a roleplay reply. Bare names
# count too: a model that says "knowledge_base 에 따르면" has leaked just as
# surely as one that echoes the literal tag.
_META_LEAK = re.compile(
    r"(</?(?:knowledge_base|recalled_history|system_note)>|"
    r"\b(?:knowledge_base|recalled_history|system_note)\b|"
    r"Additional Information & Rules|\[User Message\]|\[Roleplay Response\]|"
    r"\[System Message\]|\[Story State|\[Previous History\]|"
    r"키워드북|메인 ?프롬프트|시스템 ?프롬프트|system prompt|integrated[- ]prompt)",
    re.I,
)
_ITALIC_LINE = re.compile(r"^\*[^*].*\*$")
_HUD_FIELDS: tuple[str, ...] = ()
_SCENE_SEGMENT = re.compile(r"/(scene|bg|background|장면|배경)/", re.I)


def _is_scene_image(url: str) -> bool:
    return bool(_SCENE_SEGMENT.search(url))

# Everyday words short enough to sit one syllable from a character name.
_COMMON_WORDS = {
    "누나", "언니", "오빠", "형님", "그녀", "그들", "우리", "저희", "당신", "자신",
    "사람", "사원", "직원", "회사", "부서", "팀장", "대리", "사장", "신입", "표정",
    "이제", "다시", "정말", "조금", "잠시", "여기", "거기", "저기", "지금", "모두",
    "하나", "둘째", "서류", "자리", "손끝", "눈빛", "목소", "마음", "머리", "얼굴",
}


@dataclass
class Finding:
    rule: str
    severity: str
    message: str
    line: int | None = None
    evidence: str = ""
    clause: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


_RP_HALT = re.compile(r"(즉시 중단|일시 중단|롤플레이.{0,6}(중단|정지)|오직 아래|"
                      r"만 출력|해설 모드|순수 해설)")


def _suppresses_hud(shortcut: Shortcut | None) -> bool:
    return bool(shortcut and _RP_HALT.search(shortcut.prompt))


def _lines(text: str) -> list[tuple[int, str]]:
    return list(enumerate(text.splitlines(), start=1))


def _outside_fences(text: str) -> list[tuple[int, str]]:
    out, inside = [], False
    for n, line in _lines(text):
        if _FENCE_LINE.match(line.strip()):
            inside = not inside
            continue
        if not inside:
            out.append((n, line))
    return out


def _quoted_spans(text: str) -> list[str]:
    return [m.strip() for m in re.findall(r"[\"“]([^\"”\n]{4,})[\"”]", text)]


def check(response: str, project: Project, session: Session, *,
          user_input: str = "", shortcut: Shortcut | None = None,
          prev_response: str | None = None,
          baseline_chars: int | None = None,
          length_tolerance: float = 0.6) -> list[Finding]:
    f: list[Finding] = []
    add = f.append

    # Rules run only where this build declares the convention they police.
    # A project that writes dialogue as `이름: "대사"` must not be told it broke
    # a pipe rule it never adopted.
    c = getattr(project, "contract", None)
    dialogue_re = _dialogue_re(getattr(c, "dialogue_separators", []) if c else [])
    narration_mark = getattr(c, "narration_wrapper", None) if c else "*"
    hud_label = getattr(c, "hud_fence", None) if c else "Info"
    hud_fields = tuple(getattr(c, "hud_fields", ()) or ()) if c else ()
    hud_required = bool(getattr(c, "hud_required", False)) if c else True
    forbid_user_dialogue = getattr(c, "forbid_user_dialogue", True) if c else True
    forbid_choices = getattr(c, "forbid_numbered_choices", True) if c else True
    forbid_meta = getattr(c, "forbid_meta", True) if c else True
    notation = list(getattr(c, "notation_symbols", ["ⓤ", "ⓒ"])) if c else ["ⓤ", "ⓒ"]

    body = _outside_fences(response)
    # The contract exempts only /OOC from the HUD. A shortcut is exempt as well,
    # but just when its own prompt tells the model to stop the roleplay and emit
    # nothing but its panel; a narrative shortcut like /야근 is an ordinary turn
    # and still owes a status window.
    ooc = user_input.strip().startswith("/OOC") or _suppresses_hud(shortcut)

    # ── 사칭 / 에코 (6중 잠금) ──────────────────────────────────────
    persona_names = {"{{user}}", "{user}", session.persona_name.strip()}
    persona_names.discard("")
    for n, line in body:
        m = dialogue_re.match(line.strip())
        if not m or not forbid_user_dialogue:
            continue
        speaker = m.group(1).strip()
        if speaker in persona_names:
            add(Finding("user_impersonation", CRITICAL,
                        f"{speaker} 대사 블록 출력 — ⓤ 자율성 6중 잠금 위반",
                        n, line.strip(), "# 1. Anti-Echo"))

    user_quotes = _quoted_spans(user_input) if forbid_user_dialogue else []
    for n, line in body:
        if dialogue_re.match(line.strip()):
            continue
        for q in user_quotes:
            if q and q in line:
                add(Finding("user_echo", ERROR,
                            "지문 안에서 ⓤ 대사를 재인용함",
                            n, q[:60], "# 1. Anti-Echo"))
                break

    # ── 선택지 유도 금지 ───────────────────────────────────────────
    numbered = [(n, l) for n, l in body if _NUMBERED.match(l)] if forbid_choices else []
    if len(numbered) >= 2:
        add(Finding("numbered_choices", ERROR, "번호 선택지 제시 금지 위반",
                    numbered[0][0], numbered[0][1].strip(), "# 1. 선택지 금지"))
    for n, line in body:
        if forbid_choices and _CHOICE_PROMPT.search(line):
            add(Finding("choice_prompt", WARN, "'어떻게 할 것인가'식 유도문",
                        n, line.strip()[:70], "# 1. 선택지 금지"))
            break

    # ── 서술 형식 ─────────────────────────────────────────────────
    for n, line in (body if narration_mark else []):
        s = line.strip()
        if not s or _IMG.match(s) or dialogue_re.match(s) or s.startswith("["):
            continue
        if _ITALIC_LINE.match(s):
            continue
        if s.startswith("*") or s.endswith("*"):
            add(Finding("narration_italic", WARN, "지문 기울임표가 열리거나 닫히지 않음",
                        n, s[:70], "# 8. 기본 서술 규칙"))
        else:
            add(Finding("narration_italic", WARN,
                        "지문/나레이션이 `*…*` 로 감싸이지 않음",
                        n, s[:70], "# 8. 기본 서술 규칙"))

    primary_sep = (getattr(c, "dialogue_separators", None) or ["|"])[0] if c else "|"
    for n, line in body:
        s = line.strip()
        if primary_sep in s and not dialogue_re.match(s) and not _IMG.match(s) \
                and not s.startswith("["):
            if re.match(rf"^[^{re.escape(primary_sep)}]{{1,40}}\s*{re.escape(primary_sep)}", s):
                add(Finding("dialogue_format", WARN,
                            f'대사 형식이 `이름 {primary_sep} "대사"` 와 다름',
                            n, s[:70], "# 8. 기본 서술 규칙"))

    # ── 메타 누출 ─────────────────────────────────────────────────
    for n, line in (body if forbid_meta else []):
        m = _META_LEAK.search(line)
        if m:
            add(Finding("meta_leak", CRITICAL,
                        f"프롬프트 내부 구조 누출: {m.group(1)}",
                        n, line.strip()[:70], "# 8. 금지: 메타 설명문"))
            break
    leaked = [sym for sym in notation if sym in response]
    if leaked:
        add(Finding("notation_leak", ERROR,
                    f"내부 표기 기호({'/'.join(leaked)}) 가 응답에 노출됨",
                    None, "", "# 표기"))

    # ── 명부 밖 화자 ──────────────────────────────────────────────
    # A one-syllable slip turns 니아 into 리아 and the prose still reads fine,
    # so nothing but a roster check catches it.
    roster = {c.name for c in project.characters}
    if roster:
        allowed = roster | persona_names | {"익명", "ㅇㅇ"}
        for n, line in body:
            m = dialogue_re.match(line.strip())
            if not m:
                continue
            speaker = m.group(1).strip()
            if speaker in allowed:
                continue
            # An extra speaking by role ("경비 | …") is allowed by the contract;
            # only flag a near-miss on a real character's name.
            near = [r for r in roster
                    if len(r) == len(speaker)
                    and sum(a != b for a, b in zip(r, speaker)) == 1]
            if near:
                add(Finding("unknown_speaker_name", ERROR,
                            f"명부에 없는 화자 '{speaker}' — '{near[0]}' 오기로 보임",
                            n, line.strip()[:60], "# 7. 주연 인물 명부"))

    if roster:
        # A misspelt name is only worth reporting when it behaves like a name:
        # it starts a word, carries a subject/object marker, and the character it
        # resembles is actually on stage. Verb endings collide with short names
        # constantly (팔아, 박아), so the marker set stays narrow.
        present = {r for r in roster if r in response}
        authored = _authored_vocabulary(project)
        flagged: set[str] = set()
        for n, line in body:
            for m in re.finditer(r"(?<![가-힣])([가-힣]{2,4})(?=[은는이가을를]|에게)", line):
                token = m.group(1)
                if token in roster or token in flagged or token in _COMMON_WORDS:
                    continue
                if token in authored:
                    continue        # a word this build actually uses
                near = [r for r in present
                        if len(r) == len(token)
                        and sum(a != b for a, b in zip(r, token)) == 1]
                if near:
                    flagged.add(token)
                    add(Finding("roster_name_typo", WARN,
                                f"'{token}' 이 이번 응답에 등장하는 '{near[0]}' 와 한 글자 차이 — 오기 의심",
                                n, line.strip()[:60], "# 7. 주연 인물 명부"))

    # ── 이미지 규칙 ───────────────────────────────────────────────
    f.extend(_check_images(response, project, prev_response, dialogue_re))

    # ── 상태창 ────────────────────────────────────────────────────
    huds = _hud_re(hud_label).findall(response) if hud_label is not None else []
    if hud_label is None:
        pass                        # this build declares no status window
    elif ooc:
        if huds:
            add(Finding("hud_on_ooc", ERROR, "/OOC·단축어 응답인데 상태창을 출력함",
                        None, "", "# 8. 상태창 규격"))
    elif not huds and hud_required:
        add(Finding("hud_missing", ERROR,
                    f"응답 최하단 ```{hud_label} 상태창 누락",
                    None, "", "# 8. 상태창 규격"))
    elif huds:
        if len(huds) > 1:
            add(Finding("hud_duplicate", WARN, f"상태창이 {len(huds)}개 출력됨",
                        None, "", "# 8. 상태창 규격"))
        hud = huds[-1]
        for field in hud_fields:
            if field not in hud:
                add(Finding("hud_field_missing", WARN, f"상태창 항목 {field} 누락",
                            None, field, "# 8. 상태창 규격"))
        if not response.rstrip().endswith("```"):
            add(Finding("hud_not_last", WARN, "상태창이 응답 최하단이 아님",
                        None, "", "# 8. 상태창 규격"))

    # ── 분량: 프롬프트가 절대 범위를 선언했을 때만 ─────────────────
    length_min = getattr(c, "length_min", None) if c else None
    length_max = getattr(c, "length_max", None) if c else None
    if length_min or length_max:
        # Measure the prose, not the status window: a long HUD would otherwise
        # disguise a response that said almost nothing.
        prose = (_hud_re(hud_label).sub("", response).strip()
                 if hud_label is not None else response)
        unit = getattr(c, "length_unit", "char") if c else "char"
        # Korean has no word delimiter beyond the space, so "word" means 어절.
        n = len(prose.split()) if unit == "word" else len(prose)
        label = "단어" if unit == "word" else "자"
        if length_min and n < length_min:
            add(Finding("length_below_floor", WARN,
                        f"본문 {n}{label} — 하한 {length_min}{label} 미달",
                        None, "", "# 4. 응답분량"))
        elif length_max and n > length_max:
            add(Finding("length_above_ceiling", WARN,
                        f"본문 {n}{label} — 상한 {length_max}{label} 초과",
                        None, "", "# 4. 응답분량"))

    # ── 분량 드리프트 ─────────────────────────────────────────────
    if baseline_chars and not (length_min or length_max):
        ratio = len(response) / baseline_chars
        if ratio > 1 + length_tolerance or ratio < 1 - length_tolerance:
            add(Finding("length_drift", WARN,
                        f"응답 분량이 기준선의 {ratio:.0%} ({len(response)}자 vs {baseline_chars}자)",
                        None, "", "# 4. 응답분량"))

    # ── 단축어별 추가 계약 ────────────────────────────────────────
    if shortcut:
        f.extend(_check_shortcut(response, shortcut))

    order = {CRITICAL: 0, ERROR: 1, WARN: 2, INFO: 3}
    f.sort(key=lambda x: (order.get(x.severity, 9), x.line or 0))
    return f


def _authored_vocabulary(project: Project) -> str:
    """Everything the author wrote, as one haystack of legitimate words."""
    cached = getattr(project, "_vocab_cache", None)
    if cached is not None:
        return cached
    parts = [project.prologue, project.opening_situation]
    parts += list(project.main_prompt.values())
    for entries in project.keyword_entries.values():
        parts += [e.content for e in entries]
    vocab = "\n".join(parts)
    try:
        object.__setattr__(project, "_vocab_cache", vocab)
    except Exception:
        pass
    return vocab


def _check_images(response: str, project: Project, prev_response: str | None,
                  dialogue_re: re.Pattern) -> list[Finding]:
    out: list[Finding] = []
    rule = project.image_rule
    c = getattr(project, "contract", None)
    id_pat = (getattr(c, "image_id_pattern", None) or r"(\d{2})") if c else r"(\d{2})"
    if not rule.base_url and not (c and getattr(c, "image_base", None)):
        return out                  # no image convention to police
    known_numbers = project.character_numbers()
    name_by_number = {c.number: c.name for c in project.characters if c.number}

    lines = response.splitlines()
    seq: list[tuple[int, str, str, str]] = []  # line, label, number, situation
    for i, line in enumerate(lines, start=1):
        m = _IMG_ANY.search(line)
        if not m:
            continue
        label, url = m.group(1).strip(), m.group(2).strip()
        if rule.base_url and not url.startswith(rule.base_url):
            out.append(Finding("image_bad_host", ERROR,
                               f"이미지 URL 이 계약된 base 와 다름: {url}",
                               i, url[:80], "# 8. 이미지 출력 규칙"))
            continue
        if _is_scene_image(url):
            seq.append((i, label, "scene", "scene"))
            continue
        mm = re.search(rf"/{id_pat}/([sSaA]\d{{2}})\.(?:webp|png|jpg)$", url)
        if not mm:
            out.append(Finding("image_bad_path", ERROR,
                               f"이미지 경로 형식 위반 (…/{{인물}}/{{상황}}.webp): {url}",
                               i, url[:80], "# 8. 이미지 출력 규칙"))
            continue
        num, sit = mm.group(1), mm.group(2).lower()
        seq.append((i, label, num, sit))

        if num not in known_numbers:
            out.append(Finding("image_unknown_character", ERROR,
                               f"인물번호 {num} 가 명부에 없음", i, url[:80],
                               "# 8. 이미지 출력 규칙"))
        elif label and name_by_number.get(num) and label != name_by_number[num]:
            out.append(Finding("image_label_mismatch", WARN,
                               f"이미지 라벨 '{label}' 이 인물번호 {num}"
                               f"({name_by_number[num]}) 와 불일치",
                               i, url[:80], "# 8. 이미지 출력 규칙"))
        if rule.situation_codes and sit not in rule.situation_codes:
            out.append(Finding("image_unknown_situation", ERROR,
                               f"상황코드 {sit} 가 정의에 없음", i, url[:80],
                               "# 8. 이미지 출력 규칙"))
        allowed = rule.restricted_codes.get(sit)
        if allowed is not None and num not in allowed:
            out.append(Finding("image_restricted_code", ERROR,
                               f"{sit} 는 인물 {allowed[0]}~{allowed[-1]} 만 보유 (요청 {num})",
                               i, url[:80], "# 8. 이미지 출력 규칙"))

        nxt = lines[i].strip() if i < len(lines) else ""
        if _is_scene_image(url):
            continue                # a background plate has no speaker
        if not dialogue_re.match(nxt):
            out.append(Finding("image_not_above_dialogue", WARN,
                               "이미지 바로 아래 줄이 대사가 아님", i, nxt[:60],
                               "# 8. 이미지 출력 규칙"))

    # Once a response has called an adult code, a clothed emotion image landing
    # later in the same response breaks the scene on screen even though the
    # prose reads fine.
    adult_at = next((i for i, _l, _n, sit in seq if sit.startswith("a")), None)
    if adult_at is not None:
        for i, _label, num, sit in seq:
            if i > adult_at and sit.startswith("s"):
                out.append(Finding("clothed_image_in_adult_scene", ERROR,
                                   f"성인 코드 이후 S 코드({sit}) 이미지 — "
                                   f"성인씬 도중 옷 입은 컷이 노출됨",
                                   i, "", "# 8. 이미지 출력 규칙"))
                break

    # same character repeated with the same situation code inside one response
    seen: dict[str, str] = {}
    for i, _label, num, sit in seq:
        if seen.get(num) == sit:
            out.append(Finding("image_repeat_same_emotion", WARN,
                               f"인물 {num} 가 같은 감정({sit})으로 이미지 반복 출력",
                               i, "", "# 8. 이미지 출력 규칙"))
        seen[num] = sit

    if prev_response:
        prev_last: dict[str, str] = {}
        for m in _IMG_ANY.finditer(prev_response):
            mm = re.search(rf"/{id_pat}/([sSaA]\d{{2}})\.(?:webp|png|jpg)$", m.group(2))
            if mm:
                prev_last[mm.group(1)] = mm.group(2)
        for i, _label, num, sit in seq[:1]:
            if prev_last.get(num) == sit:
                out.append(Finding("image_repeat_across_turns", INFO,
                                   f"직전 응답과 같은 인물{num}·감정{sit} 이미지",
                                   i, "", "# 8. 이미지 출력 규칙"))
    return out


def _check_shortcut(response: str, shortcut: Shortcut) -> list[Finding]:
    out: list[Finding] = []
    prompt = shortcut.prompt
    has_fence = "```" in response
    if "코드블럭" in prompt and ("배제" in prompt or "금지" in prompt):
        if has_fence:
            out.append(Finding("shortcut_codeblock_banned", ERROR,
                               f"{shortcut.name}: 코드블럭 금지인데 출력함",
                               None, "", shortcut.id))
    elif "코드블럭" in prompt and not has_fence:
        out.append(Finding("shortcut_codeblock_missing", ERROR,
                           f"{shortcut.name}: 코드블럭 UI 출력이 요구되는데 없음",
                           None, "", shortcut.id))
    return out


def summarize(findings: list[Finding]) -> dict:
    counts = {CRITICAL: 0, ERROR: 0, WARN: 0, INFO: 0}
    for x in findings:
        counts[x.severity] = counts.get(x.severity, 0) + 1
    return {
        "total": len(findings),
        "counts": counts,
        "passed": counts[CRITICAL] == 0 and counts[ERROR] == 0,
    }
