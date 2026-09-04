"""Data model for a parsed Crack project and a running session."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class KeywordEntry:
    """One `## 제목` / `- 키워드:` / `- 내용:` block from a keyword book."""

    title: str
    keywords: list[str]
    content: str
    order: int
    source: str

    @property
    def char_count(self) -> int:
        return len(self.content)


@dataclass
class Shortcut:
    """One `## shortcut_*` block: a slash command the player can type."""

    id: str
    name: str
    description: str
    prompt: str
    order: int
    source: str
    declared_slash: bool = False


@dataclass
class Character:
    """One `▶NN.이름:[...]` line from the roster section of the main prompt."""

    number: str | None
    name: str
    fields: list[str]

    @property
    def gender(self) -> str | None:
        return self.fields[0] if self.fields else None


@dataclass
class ImageRule:
    """Image output contract extracted from the main prompt."""

    base_url: str | None
    situation_codes: list[str]
    restricted_codes: dict[str, list[str]]  # code -> character numbers allowed


@dataclass
class StartSet:
    """One selectable opening: a prologue paired with its start prompt.

    A story can offer several entry points (a different department, route or
    protagonist). Each is a directory holding `prologue.md` and
    `start-prompt.md`; the pair travels together because a prologue only makes
    sense with the opening situation written for it.
    """

    id: str
    title: str
    description: str
    prologue: str
    start_prompt: str          # the whole start-prompt.md — what Crack uploads
    opening_situation: str     # parsed out for display and linting only
    parse_contract: str
    source: str
    is_default: bool = False
    order: int = 0
    generated: bool = False   # True for the copy materialised into build/


@dataclass
class Project:
    root: str
    name: str
    variants: list[str]
    main_prompt: dict[str, str]
    keyword_entries: dict[str, list[KeywordEntry]]
    shortcuts: dict[str, list[Shortcut]]
    prologue: str
    opening_situation: str
    parse_contract: str
    characters: list[Character]
    image_rule: ImageRule
    hud_example: str | None
    start_sets: list[StartSet] = field(default_factory=list)
    contract: Any = None      # crack_emulator.contract.Contract

    def start_set(self, set_id: str | None) -> "StartSet | None":
        if not self.start_sets:
            return None
        if set_id:
            for s in self.start_sets:
                if s.id == set_id:
                    return s
        for s in self.start_sets:
            if s.is_default:
                return s
        return self.start_sets[0]

    def entries(self, variant: str) -> list[KeywordEntry]:
        return self.keyword_entries.get(variant, self.keyword_entries.get("default", []))

    def shortcut_list(self, variant: str) -> list[Shortcut]:
        return self.shortcuts.get(variant, self.shortcuts.get("default", []))

    def prompt(self, variant: str) -> str:
        return self.main_prompt.get(variant) or next(iter(self.main_prompt.values()))

    def character_numbers(self) -> set[str]:
        return {c.number for c in self.characters if c.number}


@dataclass
class Turn:
    index: int
    role: str  # "user" | "assistant"
    content: str
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    id: str
    project_root: str
    variant: str
    start_set: str = "build"
    persona_name: str = "{{user}}"
    persona_body: str = ""
    user_note: str = ""
    turns: list[Turn] = field(default_factory=list)
    summaries: list[str] = field(default_factory=list)
    relations: list[str] = field(default_factory=list)
    recalled: list[str] = field(default_factory=list)
    goal: str = ""
    stats: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Session":
        turns = [Turn(**t) for t in d.pop("turns", [])]
        return cls(turns=turns, **d)
