"""Turn loop: assemble -> call -> validate -> persist."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import memory, qa
from .log import ActivationLog
from .activation import activate_detail, match_shortcut
from .assembler import AssembledPrompt, assemble
from .config import Config
from .llm import Client
from .models import Project, Session, Turn
from .parser import load_project
from .session import Store


@dataclass
class TurnResult:
    session_id: str
    turn_index: int
    user_input: str
    reply: str
    activations: list[dict]
    dropped: list[dict]
    recalled: list[str]
    summaries: list[str]
    findings: list[dict]
    qa: dict
    prompt_stats: dict
    shortcut: str | None = None
    usage: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


class Engine:
    def __init__(self, project_root: str, cfg: Config, client: Client,
                 store: Store | None = None, variant: str = "safe",
                 log: ActivationLog | None = None):
        self.project: Project = load_project(project_root)
        self.cfg = cfg
        self.client = client
        self.store = store or Store()
        self.log = log or ActivationLog(self.store.root.parent / "logs")
        if variant not in self.project.variants:
            raise ValueError(
                f"variant '{variant}' not in {self.project.variants}"
            )
        self.variant = variant

    # ── session lifecycle ─────────────────────────────────────────
    def start(self, session_id: str, *, persona_name: str = "{{user}}",
              persona_body: str = "", user_note: str = "", goal: str = "",
              seed_prologue: bool = True, start_set: str | None = None) -> Session:
        chosen = self.project.start_set(start_set)
        prologue = (chosen.prologue if chosen else self.project.prologue).strip()
        s = Session(id=session_id, project_root=self.project.root, variant=self.variant,
                    start_set=chosen.id if chosen else "build",
                    persona_name=persona_name, persona_body=persona_body,
                    user_note=user_note, goal=goal)
        if seed_prologue and prologue:
            s.turns.append(Turn(index=0, role="assistant", content=prologue,
                                meta={"source": chosen.source if chosen else "prologue.md"}))
        s.stats["_baseline_chars"] = len(prologue)
        self.store.save(s)
        return s

    def load(self, session_id: str) -> Session:
        return self.store.load(session_id)

    # ── one turn ──────────────────────────────────────────────────
    def build_prompt(self, session: Session, user_input: str) -> AssembledPrompt:
        window = int(self.cfg.get("context.window_turns", 20))
        shortcut, _rest = match_shortcut(user_input, self.project.shortcut_list(self.variant))
        acts, dropped = activate_detail(
            self.project.entries(self.variant), session.turns, user_input, self.cfg)
        recalled = memory.select_recalled(session, self.cfg, window, user_input)
        history = memory.live_turns(session, window)
        prompt = assemble(self.project, session, self.cfg, self.variant,
                          user_input, history, acts, recalled, shortcut)
        prompt.dropped = dropped
        return prompt

    def turn(self, session: Session, user_input: str, *, run_qa: bool = True,
             update_memory: bool = True) -> TurnResult:
        window = int(self.cfg.get("context.window_turns", 20))
        prompt = self.build_prompt(session, user_input)

        reply = self.client.complete(prompt.system, prompt.messages).strip()

        prev = next((t.content for t in reversed(session.turns) if t.role == "assistant"), None)
        idx = len(session.turns)
        session.turns.append(Turn(index=idx, role="user", content=user_input))
        session.turns.append(Turn(
            index=idx + 1, role="assistant", content=reply,
            meta={"activated": [a.entry.title for a in prompt.activations],
                  "shortcut": prompt.shortcut.id if prompt.shortcut else None},
        ))

        findings: list[qa.Finding] = []
        if run_qa:
            findings = qa.check(
                reply, self.project, session,
                user_input=user_input, shortcut=prompt.shortcut,
                prev_response=prev,
                baseline_chars=session.stats.get("_baseline_chars"),
            )

        if update_memory and memory.should_summarize(session, self.cfg, window):
            memory.update_summaries(session, self.cfg, window, self.client)
            memory.update_relations(session, self.cfg, window, self.client)

        self.store.save(session)

        def _acts(items):
            return [{"title": a.entry.title, "matched": a.matched, "where": a.where,
                     "chars": a.entry.char_count} for a in items]

        activations = _acts(prompt.activations)
        dropped = _acts(prompt.dropped)
        self.log.append(session.id, {
            "session": session.id,
            "turn": idx + 1,
            "variant": self.variant,
            "fidelity": self.cfg.fidelity,
            "model": getattr(self.client, "model", None),
            "input": user_input,
            "shortcut": prompt.shortcut.id if prompt.shortcut else None,
            "activated": activations,
            "dropped": dropped,
            "max_entries": self.cfg.get("keyword.max_entries"),
            "scanned_turns": int(self.cfg.get("keyword.scan_turns", 1) or 0),
            "prompt_chars": prompt.char_count,
            "reply_chars": len(reply),
            "findings": [{"rule": x.rule, "severity": x.severity} for x in findings],
        })

        return TurnResult(
            session_id=session.id,
            turn_index=idx + 1,
            user_input=user_input,
            reply=reply,
            activations=activations,
            dropped=dropped,
            recalled=memory.select_recalled(session, self.cfg, window, user_input),
            summaries=list(session.summaries),
            findings=[x.to_dict() for x in findings],
            qa=qa.summarize(findings),
            prompt_stats={
                "system_chars": len(prompt.system),
                "history_messages": len(prompt.messages) - 1,
                "total_chars": prompt.char_count,
                "window_turns": window,
                "fidelity": self.cfg.fidelity,
                "variant": self.variant,
            },
            shortcut=prompt.shortcut.name if prompt.shortcut else None,
            usage=dict(self.client.last_usage),
        )
