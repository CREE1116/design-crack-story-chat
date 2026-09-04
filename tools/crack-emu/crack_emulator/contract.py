"""Derive a project's output contract from its own prompt.

Nothing here is a house style. Every rule the validator runs has to point at a
line in *this* build's prompt; where the evidence is missing the rule turns
itself off rather than guess. A checker that reports violations of a convention
the project never adopted is worse than no checker, because it buries the real
findings.

A project can override any of it with `qa-contract.yaml` next to the build
artifacts, for the cases detection cannot reach.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

OVERRIDE_FILE = "qa-contract.yaml"


@dataclass
class Contract:
    # Each field is None/empty when the build gives no evidence for it, and the
    # rules that depend on it are skipped.
    dialogue_separators: list[str] = field(default_factory=list)
    narration_wrapper: str | None = None          # e.g. "*"
    hud_fence: str | None = None                  # e.g. "Info"
    hud_fields: list[str] = field(default_factory=list)
    hud_required: bool = False
    image_template: str | None = None             # raw template from the prompt
    image_base: str | None = None
    image_id_kind: str | None = None              # "numbered" | "slug"
    image_id_pattern: str | None = None
    situation_codes: list[str] = field(default_factory=list)
    restricted_codes: dict[str, list[str]] = field(default_factory=dict)
    forbid_user_dialogue: bool = False
    forbid_numbered_choices: bool = False
    forbid_meta: bool = False
    notation_symbols: list[str] = field(default_factory=list)
    length_min: int | None = None
    length_max: int | None = None
    length_unit: str = "char"        # "char" | "word"
    detected: dict[str, str] = field(default_factory=dict)   # rule -> evidence line
    source: str = "detected"

    def has(self, name: str) -> bool:
        return bool(getattr(self, name, None))


_DIALOGUE_EXAMPLES = re.compile(r"`?([^`\n|:：]{1,20})\s*([|｜:：])\s*[\"“][^\"”\n]*[\"”]`?")
_IMG_TEMPLATE = re.compile(r"!\[([^\]]*)\]\((\S*?\{[^)]*)\)")
_IMG_PLAIN = re.compile(r"!\[([^\]]*)\]\((https?://\S+?)\)")
_FENCE_LABEL = re.compile(r"```([A-Za-z][A-Za-z0-9_-]{0,20})\b")
_SITUATION = re.compile(r"상황\s*=\s*((?:[sS]\d{2}\S*\s*)+)")
_SIT_CODE = re.compile(r"([sS]\d{2})")
_RESTRICT = re.compile(r"([sS]\d{2})\s*은?\s*(\d{2})\s*[~-]\s*(\d{2})\s*만")
_HUD_FIELD = re.compile(r"\[([^\]\n]{1,14})\]")


def detect(main_prompt: str, hud_example: str | None) -> Contract:
    c = Contract()

    # ── dialogue shape: read it off the examples the prompt itself gives ──
    seps: dict[str, int] = {}
    for m in _DIALOGUE_EXAMPLES.finditer(main_prompt):
        sep = m.group(2)
        sep = "|" if sep in "|｜" else ":"
        seps[sep] = seps.get(sep, 0) + 1
        c.detected.setdefault("dialogue", m.group(0)[:60])
    c.dialogue_separators = [s for s, _ in sorted(seps.items(), key=lambda kv: -kv[1])]

    # ── narration wrapper ──
    m = re.search(r"지문[^\n]{0,40}?[`\"']?(\*)[^\n]{0,12}?\1", main_prompt)
    if m or re.search(r"기울임", main_prompt):
        c.narration_wrapper = "*"
        c.detected["narration"] = (m.group(0) if m else "기울임")[:60]

    # ── status window ──
    if hud_example:
        c.hud_fields = sorted({f"[{x}]" for x in _HUD_FIELD.findall(hud_example)
                               if not x.startswith("⌛")})
    fence = None
    for fm in _FENCE_LABEL.finditer(main_prompt):
        label = fm.group(1)
        if label.lower() not in {"markdown", "md", "text", "python", "json", "bash"}:
            fence = label
            break
    hud_section = re.search(r"^#+\s*[^\n]*상태\s?창[^\n]*$", main_prompt, re.M)
    if fence:
        c.hud_fence = fence
        c.detected["hud"] = f"```{fence}"
    elif hud_section or hud_example:
        # An unlabelled fence: several projects explicitly forbid a language tag.
        c.hud_fence = ""
        c.detected["hud"] = (hud_section.group(0)[:40] if hud_section else "상태창 예시")
    c.hud_required = c.hud_fence is not None and bool(
        re.search(r"(매\s?응답|every response|첫 응답부터)[^\n]{0,60}"
                  r"(필수|must|예외 없이|반드시)", main_prompt))

    # ── images ──
    tm = _IMG_TEMPLATE.search(main_prompt)
    if tm:
        c.image_template = tm.group(2)
        c.detected["image"] = tm.group(0)[:80]
        base = re.split(r"\{", c.image_template, 1)[0]
        c.image_base = base
        tail = c.image_template[len(base):]
        # `{인물}/{상황}.webp` -> two path segments; the first is the identity.
        c.image_id_kind = "numbered" if re.search(r"인물\s*번호|\{인물\}", main_prompt) else "slug"
    else:
        pm = _IMG_PLAIN.search(main_prompt)
        if pm:
            c.detected["image"] = pm.group(0)[:80]
    if c.image_id_kind == "numbered":
        c.image_id_pattern = r"(\d{2})"
    elif c.image_id_kind == "slug":
        c.image_id_pattern = r"([a-z0-9][a-z0-9-]*)"

    ms = _SITUATION.search(main_prompt)
    if ms:
        seen: set[str] = set()
        for code in _SIT_CODE.findall(ms.group(1)):
            low = code.lower()
            if low not in seen:
                seen.add(low)
                c.situation_codes.append(low)
    for code, lo, hi in _RESTRICT.findall(main_prompt):
        c.restricted_codes[code.lower()] = [f"{n:02d}" for n in range(int(lo), int(hi) + 1)]

    # ── prohibitions: only claim them when the prompt says so ──
    impersonation = re.search(
        r"(사칭"
        r"|대리\s*서술"
        r"|Anti-?Echo"
        r"|\{\{user\}\}\s*[|｜:：]\s*[\"“]"
        r"|ⓤ[^\n]{0,40}(창작하지\s*않|대신\s*진행하지\s*않|임의로\s*(쓰|서술))"
        r"|(대사|행동|생각|선택)[^\n]{0,20}(대리|대행|창작하지\s*않))",
        main_prompt)
    if impersonation:
        c.forbid_user_dialogue = True
        c.detected["user_dialogue"] = impersonation.group(0)[:50]
    if re.search(r"선택지[^\n]{0,20}금지|번호\s*선택지", main_prompt):
        c.forbid_numbered_choices = True
        c.detected["choices"] = "선택지 금지"
    if re.search(r"메타[^\n]{0,20}(금지|설명문)", main_prompt):
        c.forbid_meta = True
        c.detected["meta"] = "메타 금지"

    c.notation_symbols = [s for s in ("ⓤ", "ⓒ", "ⓝ") if s in main_prompt]

    # An absolute length range, when the prompt commits to one. Relative wording
    # ("keep the baseline") gives nothing to measure against.
    unit_re = r"(자|단어|words?)"
    lm = re.search(rf"응답\s*분량[^\n]*?([\d,]{{2,6}})\s*[~-]\s*([\d,]{{2,6}})\s*{unit_re}",
                   main_prompt)
    if lm:
        c.length_min = int(lm.group(1).replace(",", ""))
        c.length_max = int(lm.group(2).replace(",", ""))
        c.length_unit = "char" if lm.group(3) == "자" else "word"
        c.detected["length"] = lm.group(0)[:60]
    floor = re.search(rf"([\d,]{{2,6}})\s*{unit_re}\s*미만\s*금지", main_prompt)
    if floor:
        c.length_min = int(floor.group(1).replace(",", ""))
        c.length_unit = "char" if floor.group(2) == "자" else "word"
    ceil = re.search(rf"([\d,]{{2,6}})\s*{unit_re}\s*(?:초과\s*금지|초과×)", main_prompt)
    if ceil:
        c.length_max = int(ceil.group(1).replace(",", ""))
        c.length_unit = "char" if ceil.group(2) == "자" else "word"
    return c


def load(main_prompt: str, hud_example: str | None, build_dir: str | Path | None) -> Contract:
    c = detect(main_prompt, hud_example)
    if not build_dir:
        return c
    path = Path(build_dir) / OVERRIDE_FILE
    if not path.is_file():
        return c
    data: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for key, value in data.items():
        if hasattr(c, key):
            setattr(c, key, value)
    c.source = f"detected + {OVERRIDE_FILE}"
    return c
