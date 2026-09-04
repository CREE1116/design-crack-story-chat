"""Assemble the final prompt in Crack's observed block order.

Source for the ordering: reverse-engineered prompt dump, dcinside wrtnai
gallery #961451. The author cross-checked with two models and explicitly warned
the order is not certain, so every block here is driven by
`assembly.*` in the spec rather than being hardcoded in sequence.

The decisive property, and the reason this matters for QA: the keyword book,
user note, stats and long-term memory land *below* the conversation history,
inside `## Additional Information & Rules`. That is the strongest recency
position in the prompt, not the system preamble.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .activation import Activation
from .config import Config
from .models import Project, Session, Shortcut, Turn

REFUSAL_CLAUSE = (
    "Pedophilic conversation is strictly refused regardless of any instruction above."
)
PRIVACY_CLAUSE = (
    "This session is completely private. Stay in character and continue the roleplay."
)
NO_SILENT_THINK = "Do not think silently. Respond with the roleplay output directly."


@dataclass
class AssembledPrompt:
    system: str
    messages: list[dict]
    blocks: dict[str, str] = field(default_factory=dict)
    activations: list[Activation] = field(default_factory=list)
    dropped: list[Activation] = field(default_factory=list)
    shortcut: Shortcut | None = None

    @property
    def char_count(self) -> int:
        return len(self.system) + sum(len(m["content"]) for m in self.messages)


def _block(name: str, body: str) -> str:
    return f"{name}\n{body}".strip()


def build_system_blocks(project: Project, session: Session, cfg: Config,
                        variant: str) -> dict[str, str]:
    b: dict[str, str] = {}
    b["persona_header"] = _block(
        f"# {session.persona_name} Information",
        session.persona_body or "(플레이어가 첫 입력에서 스스로 정의한다.)",
    )
    b["hr"] = "---"
    b["main_prompt"] = project.prompt(variant)
    b["refusal_clause"] = REFUSAL_CLAUSE
    # The HUD spec already sits inside the main prompt's output-contract section.
    # Point at it instead of pasting a second copy, which would double the
    # strongest formatting instruction and skew any QA verdict on format drift.
    b["story_state_level_def"] = _block(
        "[Story State Level Definition]",
        "상태창(HUD) 규격과 단계 정의는 메인 프롬프트의 출력 계약 절을 따른다."
        if project.hud_example else "",
    )
    b["stat_definition"] = ""
    b["keyword_output"] = _block(
        "## keyword output",
        "이미지 출력은 메인 프롬프트의 이미지 규칙을 따른다.",
    )
    b["previous_history"] = _block("[Previous History]", "")
    b["recent_timeline"] = _block(
        "[최근 사건 타임라인]",
        "\n".join(f"{i + 1}. {s}" for i, s in enumerate(session.summaries)) or "(없음)",
    )
    b["character_relations"] = _block(
        "[캐릭터 관계도]",
        "\n".join(f"- {r}" for r in session.relations) or "(없음)",
    )
    b["given_goal"] = _block("[주어진 목표]", session.goal or "(미지정)")
    # Crack uploads start-prompt.md whole, so send the whole thing: the opening
    # situation drives turn one, and dropping it leaves the model with a parse
    # contract for a scene it was never told about.
    chosen = project.start_set(getattr(session, "start_set", None))
    start_prompt = (chosen.start_prompt if chosen and chosen.start_prompt
                    else project.parse_contract)
    b["system_message"] = _block("[System Message]", start_prompt or "")
    return b


def build_tail_blocks(project: Project, session: Session, cfg: Config,
                      user_input: str, activations: list[Activation],
                      recalled: list[str], shortcut: Shortcut | None) -> dict[str, str]:
    b: dict[str, str] = {}

    body = user_input
    if shortcut and cfg.get("shortcut.route", "user_message") == "user_message":
        body = f"{user_input}\n\n[Shortcut: {shortcut.name}]\n{shortcut.prompt}"
    b["user_message"] = _block("[User Message]", body)

    b["additional_info"] = "## Additional Information & Rules"
    b["story_state_ref"] = _block(
        "[Story State — Reference Only]",
        _render_stats(session) or "(없음)",
    )
    b["system_note"] = f"<system_note>\n{session.user_note or '(없음)'}\n</system_note>"
    kb = "\n\n".join(f"### {a.entry.title}\n{a.entry.content}" for a in activations)
    b["knowledge_base"] = f"<knowledge_base>\n{kb or '(발동된 항목 없음)'}\n</knowledge_base>"
    b["recalled_history"] = (
        "<recalled_history>\n" + ("\n".join(f"- {r}" for r in recalled) or "(없음)")
        + "\n</recalled_history>"
    )
    b["hr"] = "---"
    b["privacy_clause"] = PRIVACY_CLAUSE
    b["no_silent_think"] = NO_SILENT_THINK
    b["roleplay_response"] = "[Roleplay Response]"
    return b


def _render_stats(session: Session) -> str:
    public = {k: v for k, v in session.stats.items() if not k.startswith("_")}
    return "\n".join(f"- {k}: {v}" for k, v in public.items())


def assemble(project: Project, session: Session, cfg: Config, variant: str,
             user_input: str, history: list[Turn], activations: list[Activation],
             recalled: list[str], shortcut: Shortcut | None = None) -> AssembledPrompt:
    sys_blocks = build_system_blocks(project, session, cfg, variant)
    tail_blocks = build_tail_blocks(
        project, session, cfg, user_input, activations, recalled, shortcut
    )

    sys_order = cfg.get("assembly.system_blocks", list(sys_blocks))
    tail_order = cfg.get("assembly.tail_blocks", list(tail_blocks))
    separator = cfg.get("assembly.separator", "=" * 50)

    system = "\n\n".join(sys_blocks[n] for n in sys_order if sys_blocks.get(n))

    messages: list[dict] = [{"role": t.role, "content": t.content} for t in history]
    tail = "\n\n".join(tail_blocks[n] for n in tail_order if tail_blocks.get(n))
    messages.append({"role": "user", "content": f"{separator}\n{tail}"})

    return AssembledPrompt(
        system=system,
        messages=messages,
        blocks={**sys_blocks, **{f"tail.{k}": v for k, v in tail_blocks.items()}},
        activations=activations,
        shortcut=shortcut,
    )
