"""MCP server over stdio. No SDK dependency — the protocol is JSON-RPC 2.0.

Exposes the harness as tools so an agent can play a Crack build itself and read
back what broke. The point is the loop: `play_turn` returns the reply together
with the contract violations, the keyword-book entries that fired, and the ones
that lost their slot, so the agent sees the consequence of its own input in the
same call.

    crack-emu mcp --project <build> [--store DIR] [--provider NAME]

Everything is the same engine the CLI and the web UI use. A second
implementation of the rules would drift, and then no result could be trusted.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Any, Callable

from . import memory, qa
from .config import Config
from .engine import Engine
from .llm import make_client
from .log import ActivationLog, report
from .models import Session
from .parser import lint, load_project
from .session import Store
from .sets import use as use_start_set

PROTOCOL_VERSION = "2024-11-05"


class Server:
    def __init__(self, project: str, store: str | None, spec: str | None,
                 provider: str | None, variant: str, key_file: str | None):
        self.project_root = project
        self.spec = spec
        self.provider = provider
        self.variant = variant
        self.store = Store(store)
        self.log = ActivationLog(self.store.root.parent / "logs")
        self.cfg = Config.load(spec)
        self.project = load_project(project)
        self.keys: dict[str, str] = {}
        self.key_file = Path(key_file).expanduser() if key_file else None
        if self.key_file and self.key_file.is_file():
            try:
                self.keys = json.loads(self.key_file.read_text(encoding="utf-8"))
            except Exception:
                self.keys = {}

    # ── engine ────────────────────────────────────────────────────
    def _engine(self, overrides: dict | None = None, variant: str | None = None) -> Engine:
        cfg = self.cfg.override(overrides or {})
        provider = (overrides or {}).get("llm.provider") or self.provider \
            or cfg.get("llm.provider")
        client = make_client(cfg, provider, api_key=self.keys.get(provider))
        return Engine(self.project_root, cfg, client, self.store,
                      variant=variant or self.variant, log=self.log)

    @staticmethod
    def _overrides(args: dict) -> dict:
        out = {
            "llm.provider": args.get("provider"),
            "llm.model": args.get("model"),
            "context.window_turns": args.get("window_turns"),
            "keyword.scan_turns": args.get("scan_turns"),
            "memory.recalled_selection": args.get("recall"),
            "fidelity": args.get("fidelity"),
        }
        return {k: v for k, v in out.items() if v not in (None, "")}

    # ── tools ─────────────────────────────────────────────────────
    def tool_describe_project(self, a: dict) -> dict:
        p = self.project
        c = p.contract
        return {
            "name": p.name,
            "root": p.root,
            "variants": p.variants,
            "characters": [{"number": ch.number, "name": ch.name} for ch in p.characters],
            "start_sets": [{"id": x.id, "title": x.title, "description": x.description,
                            "default": x.is_default, "source": x.source}
                           for x in p.start_sets],
            "shortcuts": {v: [{"name": s.name, "description": s.description}
                              for s in p.shortcut_list(v)] for v in p.variants},
            "keyword_entries": {v: [{"title": e.title, "keywords": e.keywords,
                                     "chars": e.char_count} for e in p.entries(v)]
                                for v in p.variants},
            "contract": {
                "dialogue_separators": c.dialogue_separators,
                "narration_wrapper": c.narration_wrapper,
                "hud_fence": c.hud_fence,
                "hud_fields": c.hud_fields,
                "hud_required": c.hud_required,
                "image_id_kind": c.image_id_kind,
                "situation_codes": c.situation_codes,
                "restricted_codes": c.restricted_codes,
                "length_min": c.length_min, "length_max": c.length_max,
                "length_unit": c.length_unit,
                "evidence": c.detected,
                "note": "규칙은 이 빌드의 프롬프트에서 유도했습니다. "
                        "값이 없는 항목의 규칙은 실행되지 않습니다.",
            },
        }

    def tool_lint_build(self, a: dict) -> dict:
        findings = lint(self.project)
        counts: dict[str, int] = {}
        for f in findings:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1
        return {"findings": findings, "counts": counts,
                "passed": counts.get("error", 0) == 0}

    def tool_start_session(self, a: dict) -> dict:
        eng = self._engine(self._overrides(a), a.get("variant"))
        sid = a["session"]
        if self.store.exists(sid) and a.get("overwrite"):
            self.store.delete(sid)
            self.log.delete(sid)
        if not self.store.exists(sid):
            eng.start(sid,
                      persona_name=a.get("persona_name") or "{{user}}",
                      persona_body=a.get("persona_body") or "",
                      user_note=a.get("user_note") or "",
                      goal=a.get("goal") or "",
                      start_set=a.get("start_set"))
        s = self.store.load(sid)
        chosen = self.project.start_set(s.start_set)
        return {"session": s.id, "variant": s.variant, "start_set": s.start_set,
                "turns": len(s.turns),
                "prologue": s.turns[0].content if s.turns else "",
                "opening_situation": chosen.opening_situation if chosen else ""}

    def tool_play_turn(self, a: dict) -> dict:
        eng = self._engine(self._overrides(a), a.get("variant"))
        sid = a["session"]
        if not self.store.exists(sid):
            raise ValueError(f"session '{sid}' not started; call start_session first")
        s = eng.load(sid)
        for field in ("persona_name", "persona_body", "user_note", "goal"):
            if a.get(field) is not None:
                setattr(s, field, a[field])
        res = eng.turn(s, a["input"])
        d = res.to_dict()
        d["note"] = ("findings 는 이 빌드의 출력 계약 위반입니다. "
                     "dropped 는 3슬롯을 넘겨 주입되지 못한 키워드북 항목입니다.")
        return d

    def tool_inspect_prompt(self, a: dict) -> dict:
        eng = self._engine(self._overrides(a), a.get("variant"))
        sid = a["session"]
        s = eng.load(sid) if self.store.exists(sid) else Session(
            id=sid, project_root=self.project.root, variant=eng.variant)
        p = eng.build_prompt(s, a.get("input") or "")
        window = int(eng.cfg.get("context.window_turns", 20))
        return {"system": p.system, "messages": p.messages, "char_count": p.char_count,
                "activated": [x.entry.title for x in p.activations],
                "dropped": [x.entry.title for x in p.dropped],
                "live_turns": len(memory.live_turns(s, window)),
                "evicted_turns": len(memory.evicted_turns(s, window))}

    def tool_check_response(self, a: dict) -> dict:
        s = self.store.load(a["session"]) if a.get("session") and \
            self.store.exists(a["session"]) else Session(
                id="adhoc", project_root=self.project.root, variant=self.variant)
        findings = qa.check(a["text"], self.project, s, user_input=a.get("input") or "")
        return {"findings": [f.to_dict() for f in findings],
                "qa": qa.summarize(findings)}

    def tool_get_session(self, a: dict) -> dict:
        s = self.store.load(a["session"])
        return {"session": s.id, "variant": s.variant, "start_set": s.start_set,
                "persona_name": s.persona_name, "persona_body": s.persona_body,
                "user_note": s.user_note, "goal": s.goal,
                "summaries": s.summaries, "relations": s.relations,
                "turns": [{"index": t.index, "role": t.role, "content": t.content}
                          for t in s.turns]}

    def tool_list_sessions(self, a: dict) -> dict:
        return {"store": str(self.store.root), "sessions": self.store.list()}

    def tool_delete_session(self, a: dict) -> dict:
        sid = a["session"]
        return {"session": sid, "removed": self.store.delete(sid),
                "log_removed": self.log.delete(sid)}

    def tool_get_memory(self, a: dict) -> dict:
        cfg = self.cfg.override(self._overrides(a))
        s = self.store.load(a["session"])
        window = int(cfg.get("context.window_turns", 20))
        return memory.snapshot(self.project.root, s, cfg, window, a.get("input") or "")

    def tool_set_memory(self, a: dict) -> dict:
        s = self.store.load(a["session"])
        if "summaries" in a:
            s.summaries = [x for x in a["summaries"] if x.strip()]
        if "relations" in a:
            s.relations = [x for x in a["relations"] if x.strip()]
        if "recalled" in a:
            s.recalled = [x for x in a["recalled"] if x.strip()]
        self.store.save(s)
        return self.tool_get_memory(a)

    def tool_activation_report(self, a: dict) -> dict:
        sessions = a.get("sessions")
        records = self.log.read_all(sessions)
        if not records:
            return {"error": "no activation logs yet", "sessions": self.log.sessions()}
        out = report(records, self.project, a.get("variant") or self.variant,
                     min_turns=int(a.get("min_turns", 10)))
        out["sessions"] = sessions or self.log.sessions()
        return out

    def tool_use_start_set(self, a: dict) -> dict:
        result = use_start_set(self.project, a["start_set"])
        self.project = load_project(self.project_root)
        return result

    TOOLS: dict[str, dict[str, Any]] = {}

    # ── JSON-RPC ──────────────────────────────────────────────────
    def handle(self, req: dict) -> dict | None:
        method, rid = req.get("method"), req.get("id")
        if method == "initialize":
            return self._ok(rid, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "crack-emu", "version": "0.1.0"},
                "instructions": (
                    f"'{self.project.name}' 빌드를 직접 플레이하며 결함을 찾는 도구입니다. "
                    "start_session 으로 시작하고 play_turn 으로 진행하세요. "
                    "play_turn 응답의 findings 는 이 빌드가 자기 프롬프트에 써놓은 "
                    "출력 계약의 위반이고, dropped 는 3슬롯을 넘겨 주입되지 못한 "
                    "키워드북 항목입니다. 여러 턴을 돌린 뒤 activation_report 를 "
                    "부르면 한 턴만 봐서는 보이지 않는 문제가 나옵니다."),
            })
        if method in ("notifications/initialized", "initialized"):
            return None
        if method == "ping":
            return self._ok(rid, {})
        if method == "tools/list":
            return self._ok(rid, {"tools": list(TOOL_SCHEMAS.values())})
        if method == "tools/call":
            params = req.get("params") or {}
            name = params.get("name")
            args = params.get("arguments") or {}
            fn: Callable | None = getattr(self, f"tool_{name}", None)
            if fn is None:
                return self._err(rid, -32601, f"unknown tool: {name}")
            try:
                result = fn(args)
                return self._ok(rid, {
                    "content": [{"type": "text",
                                 "text": json.dumps(result, ensure_ascii=False, indent=2)}],
                    "isError": False,
                })
            except Exception as e:
                return self._ok(rid, {
                    "content": [{"type": "text",
                                 "text": f"{type(e).__name__}: {e}"}],
                    "isError": True,
                })
        if rid is None:
            return None
        return self._err(rid, -32601, f"unknown method: {method}")

    @staticmethod
    def _ok(rid, result) -> dict:
        return {"jsonrpc": "2.0", "id": rid, "result": result}

    @staticmethod
    def _err(rid, code, message) -> dict:
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}

    def run(self) -> int:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
            except json.JSONDecodeError:
                continue
            try:
                resp = self.handle(req)
            except Exception:
                traceback.print_exc(file=sys.stderr)
                resp = self._err(req.get("id"), -32603, "internal error")
            if resp is not None:
                sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                sys.stdout.flush()
        return 0


def _s(desc: str, **props) -> dict:
    required = [k for k, v in props.items() if v.pop("_required", False)]
    return {"description": desc,
            "inputSchema": {"type": "object", "properties": props,
                            "required": required}}


_SESSION = {"type": "string", "description": "세션 id", "_required": True}
_MODEL = {"type": "string", "description": "모델 id (생략 시 기본값)"}
_PROVIDER = {"type": "string", "description": "ollama | openrouter | gemini | openai | echo"}

TOOL_SCHEMAS = {
    "describe_project": {"name": "describe_project", **_s(
        "빌드 구조와 이 빌드에서 유도한 출력 계약을 반환합니다. 먼저 부르세요.")},
    "lint_build": {"name": "lint_build", **_s(
        "모델 호출 없이 빌드 자체를 검사합니다(항목 한도, 키워드 오발동, 슬롯 배치).")},
    "list_start_sets": {"name": "list_start_sets", **_s("선택 가능한 시작 세트 목록.")},
    "use_start_set": {"name": "use_start_set", **_s(
        "고른 시작 세트를 build/ 에 반영합니다.",
        start_set={"type": "string", "description": "세트 id", "_required": True})},
    "start_session": {"name": "start_session", **_s(
        "플레이 세션을 만들고 프롤로그를 첫 턴으로 넣습니다.",
        session=_SESSION,
        start_set={"type": "string", "description": "시작 세트 id"},
        variant={"type": "string", "description": "safe | unsafe | default"},
        persona_name={"type": "string"}, persona_body={"type": "string"},
        user_note={"type": "string", "description": "매 턴 최하단에 주입되는 지침"},
        goal={"type": "string"},
        overwrite={"type": "boolean", "description": "기존 세션을 지우고 새로 시작"})},
    "play_turn": {"name": "play_turn", **_s(
        "한 턴을 진행하고 응답·계약 위반·발동/드롭된 키워드북 항목을 함께 반환합니다.",
        session=_SESSION,
        input={"type": "string", "description": "플레이어 입력", "_required": True},
        provider=_PROVIDER, model=_MODEL,
        variant={"type": "string"},
        window_turns={"type": "integer", "description": "컨텍스트 창(턴)"},
        scan_turns={"type": "integer", "description": "키워드 스캔 깊이(턴)"})},
    "inspect_prompt": {"name": "inspect_prompt", **_s(
        "모델 호출 없이, 이 입력이면 실제로 무엇이 전송되는지 보여줍니다.",
        session=_SESSION, input={"type": "string"},
        window_turns={"type": "integer"}, scan_turns={"type": "integer"})},
    "check_response": {"name": "check_response", **_s(
        "임의의 응답 텍스트를 이 빌드의 출력 계약에 대조합니다.",
        text={"type": "string", "_required": True},
        input={"type": "string", "description": "그 응답을 만든 플레이어 입력"},
        session={"type": "string"})},
    "get_session": {"name": "get_session", **_s("세션 전체 기록.", session=_SESSION)},
    "list_sessions": {"name": "list_sessions", **_s("저장된 세션 목록.")},
    "delete_session": {"name": "delete_session", **_s(
        "세션과 발동 로그를 삭제합니다.", session=_SESSION)},
    "get_memory": {"name": "get_memory", **_s(
        "요약메모리·관계도·장기기억 슬롯의 내용과 밀려난 턴을 봅니다.",
        session=_SESSION, window_turns={"type": "integer"},
        recall={"type": "string", "description": "recent | lexical | manual"})},
    "set_memory": {"name": "set_memory", **_s(
        "메모리 슬롯을 직접 씁니다.",
        session=_SESSION,
        summaries={"type": "array", "items": {"type": "string"}},
        relations={"type": "array", "items": {"type": "string"}},
        recalled={"type": "array", "items": {"type": "string"}})},
    "activation_report": {"name": "activation_report", **_s(
        "여러 턴의 발동 로그를 모아 슬롯 초과·미발동·상시발동 항목을 집계합니다. "
        "한 턴만 봐서는 보이지 않는 문제가 여기서 나옵니다.",
        sessions={"type": "array", "items": {"type": "string"}},
        variant={"type": "string"},
        min_turns={"type": "integer", "description": "미발동 판정에 필요한 최소 턴 수"})},
}


def _tool_list_start_sets(self, a: dict) -> dict:
    return {"start_sets": [
        {"id": x.id, "title": x.title, "description": x.description,
         "default": x.is_default, "generated": x.generated, "source": x.source,
         "prologue_chars": len(x.prologue), "opening_chars": len(x.opening_situation)}
        for x in self.project.start_sets]}


Server.tool_list_start_sets = _tool_list_start_sets


def main(project: str, store: str | None = None, spec: str | None = None,
         provider: str | None = None, variant: str = "safe",
         key_file: str | None = None) -> int:
    return Server(project, store, spec, provider, variant, key_file).run()
