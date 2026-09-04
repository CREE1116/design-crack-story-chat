"""Summary memory, character relations and recalled history.

Slot counts come from the observed Crack structure: 4 summary entries under
`[최근 사건 타임라인]`, 5 under `[캐릭터 관계도]`, exactly 3 under
`<recalled_history>`. How Crack *selects* the recalled 3 is unknown, so the
default is `recent` rather than an invented scoring rule.
"""
from __future__ import annotations

from .config import Config
from .lexical import BM25
from .models import Session, Turn

SUMMARY_SYSTEM = (
    "너는 롤플레이 세션의 기록 담당이다. 주어진 대화 조각을 한국어 한 문단으로 압축한다.\n"
    "규칙: 사건·결정·관계 변화만 남긴다. 묘사와 대사는 버린다. 추측 금지. "
    "최대 {max_chars}자. 다른 말 붙이지 말고 요약문만 출력."
)

RELATION_SYSTEM = (
    "너는 롤플레이 세션의 관계 기록 담당이다. 대화에서 등장인물과 플레이어의 관계 상태를 "
    "인물당 한 줄로 정리한다. 형식: `이름 — 관계단계 / 최근 변화 근거`. "
    "최대 {slots}줄. 등장하지 않은 인물은 쓰지 않는다. 추측 금지. 목록만 출력."
)


def evicted_turns(session: Session, window_turns: int) -> list[Turn]:
    """Turns that have fallen out of the live context window."""
    if window_turns <= 0 or len(session.turns) <= window_turns:
        return []
    return session.turns[: len(session.turns) - window_turns]


def live_turns(session: Session, window_turns: int) -> list[Turn]:
    if window_turns <= 0:
        return list(session.turns)
    return session.turns[-window_turns:]


def _render(turns: list[Turn]) -> str:
    return "\n".join(f"[{t.role}] {t.content}" for t in turns)


def should_summarize(session: Session, cfg: Config, window_turns: int) -> bool:
    every = int(cfg.get("memory.summarize_every_turns", 8) or 0)
    if every <= 0:
        return False
    pending = len(evicted_turns(session, window_turns)) - _summarized_count(session)
    return pending >= every


def _summarized_count(session: Session) -> int:
    return int(session.stats.get("_summarized_turns", 0))


def update_summaries(session: Session, cfg: Config, window_turns: int, llm) -> bool:
    """Compress newly evicted turns into one summary slot. Returns True if updated."""
    evicted = evicted_turns(session, window_turns)
    done = _summarized_count(session)
    pending = evicted[done:]
    if not pending:
        return False

    max_chars = int(cfg.get("memory.summary_max_chars", 300))
    text = llm.complete(
        system=SUMMARY_SYSTEM.format(max_chars=max_chars),
        messages=[{"role": "user", "content": _render(pending)}],
        max_tokens=512,
        temperature=0.2,
    ).strip()

    session.summaries.append(text[:max_chars])
    slots = int(cfg.get("memory.summary_slots", 4))
    if slots > 0:
        session.summaries = session.summaries[-slots:]
    session.stats["_summarized_turns"] = len(evicted)
    return True


def update_relations(session: Session, cfg: Config, window_turns: int, llm) -> None:
    slots = int(cfg.get("memory.relation_slots", 5))
    recent = live_turns(session, window_turns)
    if not recent:
        return
    text = llm.complete(
        system=RELATION_SYSTEM.format(slots=slots),
        messages=[{"role": "user", "content": _render(recent)}],
        max_tokens=512,
        temperature=0.2,
    ).strip()
    lines = [ln.strip("-• \t") for ln in text.splitlines() if ln.strip()]
    session.relations = lines[:slots]


def force_refresh(session: Session, cfg: Config, window_turns: int, llm) -> dict:
    """Summarise and re-derive relations right now, regardless of the interval."""
    before = (list(session.summaries), list(session.relations))
    evicted = evicted_turns(session, window_turns)
    summarised = False
    if evicted[_summarized_count(session):]:
        summarised = update_summaries(session, cfg, window_turns, llm)
    update_relations(session, cfg, window_turns, llm)
    return {
        "summarised": summarised,
        "summaries_before": before[0], "summaries_after": list(session.summaries),
        "relations_before": before[1], "relations_after": list(session.relations),
        "pending_turns": len(evicted) - _summarized_count(session),
    }


def snapshot(project_root: str, session: Session, cfg: Config, window_turns: int,
             query: str = "") -> dict:
    """Everything the memory panel needs: slot contents, capacity and provenance."""
    evicted = evicted_turns(session, window_turns)
    live = live_turns(session, window_turns)
    mode = cfg.get("memory.recalled_selection", "recent")
    resolved = select_recalled(session, cfg, window_turns, query)
    return {
        "summary_slots": int(cfg.get("memory.summary_slots", 4)),
        "relation_slots": int(cfg.get("memory.relation_slots", 5)),
        "recalled_slots": int(cfg.get("memory.recalled_slots", 3)),
        "summaries": list(session.summaries),
        "relations": list(session.relations),
        "recalled_manual": list(session.recalled),
        "recalled_resolved": resolved,
        "recalled_selection": mode,
        "summarize_every_turns": int(cfg.get("memory.summarize_every_turns", 8)),
        "summarized_turns": _summarized_count(session),
        "window_turns": window_turns,
        "turns_total": len(session.turns),
        "turns_live": len(live),
        "turns_evicted": len(evicted),
        "pending_turns": max(0, len(evicted) - _summarized_count(session)),
        "evicted_preview": [
            {"index": t.index, "role": t.role, "text": t.content[:160]}
            for t in evicted[-12:]
        ],
    }


def select_recalled(session: Session, cfg: Config, window_turns: int,
                    query: str) -> list[str]:
    """Fill the `<recalled_history>` slots from turns outside the live window."""
    slots = int(cfg.get("memory.recalled_slots", 3))
    mode = cfg.get("memory.recalled_selection", "recent")
    if slots <= 0 or mode == "manual":
        return session.recalled[:slots]

    pool = evicted_turns(session, window_turns)
    if not pool:
        return []
    rendered = [f"[{t.role}] {t.content}" for t in pool]

    if mode == "lexical":
        hits = BM25(rendered).search(query, top_k=slots)
        return [rendered[i] for i, _ in hits]
    return rendered[-slots:]
