"""Per-turn activation log and the report built from it.

One JSONL record per turn, appended under `<store>/../logs/<session>.jsonl`.
The report is the point: over a run you learn which keyword-book entries never
fire, which fire on every single turn, and which fire only through a substring
of a longer word — the three failure modes a keyword book actually has.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from .models import Project


class ActivationLog:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def path(self, session_id: str) -> Path:
        return self.root / f"{session_id}.jsonl"

    def append(self, session_id: str, record: dict) -> None:
        p = self.path(session_id)
        p.parent.mkdir(parents=True, exist_ok=True)
        record = {"ts": time.time(), **record}
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    def read(self, session_id: str) -> list[dict]:
        p = self.path(session_id)
        if not p.exists():
            return []
        return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]

    def delete(self, session_id: str) -> bool:
        p = self.path(session_id)
        if p.exists():
            p.unlink()
            return True
        return False

    def sessions(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted(p.stem for p in self.root.glob("*.jsonl"))

    def read_all(self, sessions: list[str] | None = None) -> list[dict]:
        out: list[dict] = []
        for sid in sessions if sessions is not None else self.sessions():
            out.extend(self.read(sid))
        return out


def report(records: list[dict], project: Project, variant: str,
           always_on_ratio: float = 0.9, rare_ratio: float = 0.0,
           min_turns: int = 10) -> dict:
    """Aggregate activation records into per-entry statistics."""
    turns = len(records)
    entries = project.entries(variant)
    fired: dict[str, int] = {e.title: 0 for e in entries}
    by_keyword: dict[str, int] = {}
    by_where: dict[str, int] = {}
    dropped_count: dict[str, int] = {}
    injected_chars = 0
    turns_with_overflow = 0

    for rec in records:
        for a in rec.get("activated", []):
            title = a["title"]
            fired[title] = fired.get(title, 0) + 1
            injected_chars += a.get("chars", 0)
            for kw in a.get("matched", []):
                by_keyword[kw] = by_keyword.get(kw, 0) + 1
            for w in a.get("where", []):
                kind = w.split(":")[0]
                by_where[kind] = by_where.get(kind, 0) + 1
        drops = rec.get("dropped", [])
        if drops:
            turns_with_overflow += 1
        for d in drops:
            dropped_count[d["title"]] = dropped_count.get(d["title"], 0) + 1

    never = sorted(t for t, n in fired.items() if n == 0)
    always = sorted((t for t, n in fired.items() if turns and n / turns >= always_on_ratio),
                    key=lambda t: -fired[t])
    rare = sorted((t for t, n in fired.items()
                   if 0 < n and turns and n / turns <= rare_ratio), key=lambda t: fired[t])

    findings = []
    # A short run says nothing about coverage: three turns will miss most
    # entries no matter how well the keyword book is written.
    if turns >= min_turns:
        for t in never:
            findings.append({"severity": "warn", "rule": "entry_never_fired", "entry": t,
                             "message": f"'{t}' 가 {turns}턴 동안 한 번도 발동 안 함 — "
                                        f"키워드가 실제 대화 어휘와 안 맞음"})
    # An entry that matches on most turns and is registered above others will
    # keep evicting them; the skill's guidance is to push such entries to the
    # bottom of the list, where losing a slot costs nothing.
    order = {e.title: i + 1 for i, e in enumerate(entries)}
    for t, n in fired.items():
        if turns and n / turns >= always_on_ratio and order.get(t, 99) <= 3:
            findings.append({
                "severity": "warn", "rule": "high_match_entry_registered_high",
                "entry": t,
                "message": f"'{t}' 가 {n}/{turns}턴 발동하면서 {order[t]}번째로 등록됨 — "
                           f"매 턴 슬롯을 선점해 다른 엔트리를 밀어냄. 목록 하단으로 옮길 것"})

    if turns_with_overflow:
        findings.append({
            "severity": "warn", "rule": "slot_overflow",
            "entry": "",
            "message": f"{turns_with_overflow}/{turns}턴에서 매칭이 슬롯 수를 초과해 "
                       f"엔트리가 드롭됨 — 드롭 상위: "
                       + ", ".join(f"{t}({n})" for t, n in
                                   sorted(dropped_count.items(), key=lambda kv: -kv[1])[:3])})
    for t in always:
        findings.append({"severity": "warn", "rule": "entry_always_fired", "entry": t,
                         "message": f"'{t}' 가 {fired[t]}/{turns}턴 발동 — "
                                    f"상시 주입되므로 메인 프롬프트로 옮기는 편이 나음"})

    return {
        "turns": turns,
        "variant": variant,
        "entries_total": len(entries),
        "entries_fired": sum(1 for n in fired.values() if n),
        "avg_entries_per_turn": round(
            sum(len(r.get("activated", [])) for r in records) / turns, 2) if turns else 0,
        "avg_injected_chars": round(injected_chars / turns) if turns else 0,
        "fired": dict(sorted(fired.items(), key=lambda kv: -kv[1])),
        "never_fired": never,
        "always_fired": always,
        "rarely_fired": rare,
        "dropped": dict(sorted(dropped_count.items(), key=lambda kv: -kv[1])),
        "turns_with_overflow": turns_with_overflow,
        "by_keyword": dict(sorted(by_keyword.items(), key=lambda kv: -kv[1])),
        "match_source": by_where,
        "findings": findings,
        "coverage_conclusive": turns >= min_turns,
    }
