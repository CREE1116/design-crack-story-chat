"""Keyword-book activation.

Crack triggers a keyword-book entry when one of its keywords literally appears
in the text it scans. Scan scope per user report: the previous turn(s) plus the
current user input. Everything about the exact scope is marked UNVERIFIED in
the spec and driven from config, never hardcoded here.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from .config import Config
from .models import KeywordEntry, Turn


@dataclass
class Activation:
    entry: KeywordEntry
    matched: list[str]
    where: list[str]  # "input" | "turn:<index>:<role>"


def _norm(text: str, cfg: Config) -> str:
    if cfg.get("keyword.normalize_nfkc", True):
        text = unicodedata.normalize("NFKC", text)
    if cfg.get("keyword.case_insensitive", True):
        text = text.casefold()
    if cfg.get("keyword.strip_whitespace", False):
        text = "".join(text.split())
    return text


def scan_scope(turns: list[Turn], user_input: str, cfg: Config) -> list[tuple[str, str]]:
    """-> [(label, text), ...] oldest first, current input last."""
    n = int(cfg.get("keyword.scan_turns", 1) or 0)
    roles = set(cfg.get("keyword.scan_roles", ["user", "assistant"]))
    scoped = [t for t in turns if t.role in roles]
    window = scoped[-n:] if n > 0 else []
    out = [(f"turn:{t.index}:{t.role}", t.content) for t in window]
    out.append(("input", user_input))
    return out


def activate(entries: list[KeywordEntry], turns: list[Turn], user_input: str,
             cfg: Config) -> list[Activation]:
    return activate_detail(entries, turns, user_input, cfg)[0]


def activate_detail(entries: list[KeywordEntry], turns: list[Turn], user_input: str,
                    cfg: Config) -> tuple[list[Activation], list[Activation]]:
    """-> (loaded, dropped).

    Crack loads at most `keyword.max_entries` entries per turn and drops the
    rest, so which matches lose their slot is as much a QA signal as which ones
    win: a keyword that fires by accident does not merely add noise, it evicts
    an entry the turn actually needed.
    """
    scope = scan_scope(turns, user_input, cfg)
    normed = [(label, _norm(text, cfg)) for label, text in scope]

    hits: list[Activation] = []
    for entry in entries:
        matched: list[str] = []
        where: list[str] = []
        for kw in entry.keywords:
            nk = _norm(kw, cfg)
            if not nk:
                continue
            found = [label for label, text in normed if nk in text]
            if found:
                matched.append(kw)
                where.extend(f for f in found if f not in where)
        if matched:
            hits.append(Activation(entry=entry, matched=matched, where=where))

    # Document order is the tie-break; Crack's own ordering is unverified.
    hits.sort(key=lambda a: a.entry.order)

    dropped: list[Activation] = []

    max_entries = cfg.get("keyword.max_entries")
    if max_entries:
        n = int(max_entries)
        dropped.extend(hits[n:])
        hits = hits[:n]

    max_chars = cfg.get("keyword.max_chars")
    if max_chars:
        budget, kept = int(max_chars), []
        for h in hits:
            if budget - h.entry.char_count < 0:
                dropped.append(h)
                continue
            budget -= h.entry.char_count
            kept.append(h)
        hits = kept
    return hits, dropped


def match_shortcut(user_input: str, shortcuts) -> tuple[object | None, str]:
    """-> (Shortcut, remaining argument text) if the input starts with a slash command."""
    text = user_input.strip()
    if not text.startswith("/"):
        return None, user_input
    head = text.split(None, 1)
    # Stored shortcut names carry no slash (Crack's UI adds it), so compare the
    # bare command against the bare name.
    cmd = head[0].lstrip("/")
    rest = head[1] if len(head) > 1 else ""
    for s in shortcuts:
        if cmd == s.name.lstrip("/"):
            return s, rest
    return None, user_input
