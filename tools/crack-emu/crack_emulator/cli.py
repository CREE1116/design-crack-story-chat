"""Agent-facing CLI. Every subcommand can emit a single JSON object on stdout.

Designed to be driven by an LLM agent during QA: no interactive prompts, no
partial output, and a process exit code that reflects the QA verdict
(0 = clean, 1 = contract violations found, 2 = harness error).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import qa
from .config import Config
from .engine import Engine
from .llm import make_client
from .models import Session
from .log import ActivationLog, report
from .parser import lint, load_project
from .sets import migrate, use
from .session import Store

EXIT_OK, EXIT_FINDINGS, EXIT_ERROR = 0, 1, 2


def _emit(obj, as_json: bool, human=None) -> None:
    if as_json:
        json.dump(obj, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    elif human:
        human(obj)


def _cfg(args) -> Config:
    cfg = Config.load(args.spec)
    overrides = {
        "fidelity": args.fidelity,
        "context.window_turns": args.window_turns,
        "keyword.scan_turns": args.scan_turns,
        "memory.recalled_selection": args.recall,
        "llm.provider": args.provider,
        "llm.model": args.model,
        "llm.base_url": args.base_url,
        "llm.temperature": args.temperature,
    }
    return cfg.override(overrides)


def _engine(args) -> Engine:
    cfg = _cfg(args)
    client = make_client(cfg, args.provider)
    return Engine(args.project, cfg, client, Store(args.store), variant=args.variant)


# ── commands ──────────────────────────────────────────────────────

def cmd_parse(args) -> int:
    p = load_project(args.project)
    out = {
        "name": p.name,
        "root": p.root,
        "variants": p.variants,
        "characters": [{"number": c.number, "name": c.name} for c in p.characters],
        "image_rule": {
            "base_url": p.image_rule.base_url,
            "situation_codes": p.image_rule.situation_codes,
            "restricted_codes": p.image_rule.restricted_codes,
        },
        "keyword_entries": {
            v: [{"title": e.title, "keywords": e.keywords, "chars": e.char_count}
                for e in p.entries(v)] for v in p.variants
        },
        "shortcuts": {
            v: [{"id": s.id, "name": s.name, "description": s.description}
                for s in p.shortcut_list(v)] for v in p.variants
        },
        "start_sets": [{"id": x.id, "title": x.title, "source": x.source,
                        "prologue_chars": len(x.prologue)} for x in p.start_sets],
        "prologue_chars": len(p.prologue),
        "opening_chars": len(p.opening_situation),
        "has_hud_example": bool(p.hud_example),
    }

    def human(o):
        print(f"{o['name']}  variants={','.join(o['variants'])}  "
              f"characters={len(o['characters'])}")
        for v in o["variants"]:
            print(f"  [{v}] entries={len(o['keyword_entries'][v])} "
                  f"shortcuts={len(o['shortcuts'][v])}")
    _emit(out, args.json, human)
    return EXIT_OK


def cmd_lint(args) -> int:
    p = load_project(args.project)
    findings = lint(p, max_entry_chars=args.max_entry_chars,
                    target_entry_chars=args.target_entry_chars)
    counts: dict[str, int] = {}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    out = {"project": p.name, "findings": findings, "counts": counts,
           "passed": counts.get("error", 0) == 0}

    def human(o):
        for f in o["findings"]:
            print(f"{f['severity']:6s} {f['rule']:26s} {f['message']}")
        print(f"-- {o['counts'] or 'clean'} | passed={o['passed']}")
    _emit(out, args.json, human)
    return EXIT_OK if out["passed"] else EXIT_FINDINGS


def cmd_health(args) -> int:
    cfg = _cfg(args)
    providers = [args.provider] if args.provider else list(cfg.get("providers", {}))
    out = {"fidelity": cfg.fidelity,
           "providers": [make_client(cfg, p).health() for p in providers]}

    def human(o):
        for h in o["providers"]:
            mark = "ok " if h["ok"] else "ERR"
            note = "" if h["ok"] else (h.get("missing_key") or h.get("error", ""))[:60]
            print(f"{mark} {h['provider']:11s} {h['model'][:44]:46s} {note}")
    _emit(out, args.json, human)
    return EXIT_OK


def cmd_spec(args) -> int:
    cfg = _cfg(args)
    _emit(cfg.data, True)
    return EXIT_OK


def cmd_start(args) -> int:
    eng = _engine(args)
    s = eng.start(args.session, persona_name=args.persona_name,
                  persona_body=args.persona or "", user_note=args.user_note or "",
                  goal=args.goal or "", seed_prologue=not args.no_prologue,
                  start_set=args.start_set)
    chosen = eng.project.start_set(s.start_set)
    out = {"session": s.id, "variant": s.variant, "turns": len(s.turns),
           "start_set": s.start_set,
           "prologue_chars": len(chosen.prologue) if chosen else 0,
           "opening_situation": chosen.opening_situation if chosen else ""}
    _emit(out, args.json,
          lambda o: print(f"started {o['session']} ({o['variant']}, "
                          f"set={o['start_set']}, {o['turns']} turns)"))
    return EXIT_OK


def cmd_turn(args) -> int:
    eng = _engine(args)
    store = eng.store
    if not store.exists(args.session):
        eng.start(args.session, persona_name=args.persona_name,
                  persona_body=args.persona or "", user_note=args.user_note or "",
                  goal=args.goal or "", start_set=args.start_set)
    session = eng.load(args.session)
    text = args.input if args.input is not None else sys.stdin.read()
    res = eng.turn(session, text, run_qa=not args.no_qa)
    out = res.to_dict()

    def human(o):
        print(o["reply"])
        print("\n--- activated:", ", ".join(a["title"] for a in o["activations"]) or "(none)")
        for f in o["findings"]:
            loc = f"L{f['line']}" if f["line"] else "-"
            print(f"{f['severity']:8s} {loc:5s} {f['rule']:26s} {f['message']}")
        print(f"--- qa: {o['qa']}")
    _emit(out, args.json, human)
    return EXIT_OK if res.qa["passed"] else EXIT_FINDINGS


def cmd_prompt(args) -> int:
    """Dump the assembled prompt without calling a model."""
    eng = _engine(args)
    session = eng.load(args.session) if eng.store.exists(args.session) else Session(
        id=args.session, project_root=eng.project.root, variant=eng.variant)
    p = eng.build_prompt(session, args.input or "")
    out = {"system": p.system, "messages": p.messages,
           "blocks": list(p.blocks), "char_count": p.char_count,
           "activations": [a.entry.title for a in p.activations],
           "shortcut": p.shortcut.id if p.shortcut else None}
    if args.json:
        _emit(out, True)
    else:
        print(p.system)
        for m in p.messages:
            print(f"\n===== {m['role']} =====\n{m['content']}")
    return EXIT_OK


def cmd_check(args) -> int:
    """Validate an existing response file against the contract. No model call."""
    p = load_project(args.project)
    text = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()
    session = Session(id="check", project_root=p.root, variant=args.variant,
                      persona_name=args.persona_name)
    findings = qa.check(text, p, session, user_input=args.input or "")
    out = {"findings": [f.to_dict() for f in findings], "qa": qa.summarize(findings)}

    def human(o):
        for f in o["findings"]:
            loc = f"L{f['line']}" if f["line"] else "-"
            print(f"{f['severity']:8s} {loc:5s} {f['rule']:26s} {f['message']}")
        print(f"-- {o['qa']}")
    _emit(out, args.json, human)
    return EXIT_OK if out["qa"]["passed"] else EXIT_FINDINGS


def cmd_replay(args) -> int:
    """Run a scenario file (one user input per line, # comments allowed)."""
    eng = _engine(args)
    lines = [ln.strip() for ln in Path(args.scenario).read_text(encoding="utf-8").splitlines()]
    inputs = [ln for ln in lines if ln and not ln.startswith("#")]

    if eng.store.exists(args.session) and args.fresh:
        eng.store.delete(args.session)
    if not eng.store.exists(args.session):
        eng.start(args.session, persona_name=args.persona_name,
                  persona_body=args.persona or "", goal=args.goal or "",
                  start_set=args.start_set)

    results, all_findings = [], []
    for text in inputs:
        session = eng.load(args.session)
        res = eng.turn(session, text, run_qa=True)
        results.append(res.to_dict())
        all_findings.extend(res.findings)
        if not args.json:
            print(f"\n===== turn {res.turn_index}: {text[:60]} =====")
            print(res.reply)
            for f in res.findings:
                print(f"  {f['severity']:8s} {f['rule']:26s} {f['message']}")

    by_rule: dict[str, int] = {}
    for f in all_findings:
        by_rule[f["rule"]] = by_rule.get(f["rule"], 0) + 1
    counts: dict[str, int] = {}
    for f in all_findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    passed = counts.get("critical", 0) == 0 and counts.get("error", 0) == 0
    out = {"session": args.session, "scenario": args.scenario, "turns": len(results),
           "counts": counts, "by_rule": by_rule, "passed": passed, "results": results}
    if args.json:
        _emit(out, True)
    else:
        print(f"\n===== summary: {len(results)} turns, {counts or 'clean'}, passed={passed}")
        for rule, n in sorted(by_rule.items(), key=lambda x: -x[1]):
            print(f"  {n:3d}  {rule}")
    return EXIT_OK if passed else EXIT_FINDINGS


def cmd_report(args) -> int:
    """Aggregate activation logs into keyword-book statistics."""
    p = load_project(args.project)
    store = Store(args.store)
    log = ActivationLog(args.logs or store.root.parent / "logs")
    sessions = args.sessions or None
    records = log.read_all(sessions)
    if not records:
        out = {"error": "no activation logs found", "log_dir": str(log.root),
               "sessions": log.sessions()}
        _emit(out, args.json, lambda o: print(
            f"no logs in {o['log_dir']} (known sessions: {o['sessions'] or 'none'})"))
        return EXIT_ERROR
    out = report(records, p, args.variant, always_on_ratio=args.always_ratio,
                 min_turns=args.min_turns)
    out["log_dir"] = str(log.root)
    out["sessions"] = sessions or log.sessions()

    def human(o):
        print(f"{o['turns']}턴 · 엔트리 {o['entries_fired']}/{o['entries_total']} 발동 · "
              f"턴당 평균 {o['avg_entries_per_turn']}개 / {o['avg_injected_chars']}자 주입")
        print(f"매칭 출처: {o['match_source']}")
        print("\n발동 횟수:")
        for title, n in o["fired"].items():
            bar = "█" * min(n, 30)
            print(f"  {n:4d} {bar:<30s} {title}")
        if o["dropped"]:
            print(f"\n슬롯 부족으로 드롭 ({o['turns_with_overflow']}/{o['turns']}턴):")
            for title, n in o["dropped"].items():
                print(f"  {n:4d}  {title}")
        if o["by_keyword"]:
            print("\n키워드별:")
            for kw, n in list(o["by_keyword"].items())[:15]:
                print(f"  {n:4d}  {kw}")
        if not o["coverage_conclusive"]:
            print(f"\n(턴 {o['turns']}개 — 미발동 판정에는 부족. --min-turns 참고)")
        if o["findings"]:
            print()
            for f in o["findings"]:
                print(f"{f['severity']:6s} {f['rule']:22s} {f['message']}")
    _emit(out, args.json, human)
    return EXIT_OK if not out["findings"] else EXIT_FINDINGS


def cmd_sets(args) -> int:
    """List selectable openings; optionally copy one into build/."""
    p = load_project(args.project)
    if args.migrate is not None:
        plan = migrate(args.project, apply=args.migrate == "apply")
        _emit(plan, args.json, lambda o: (
            print(f"{'적용' if o['applied'] else '계획'} · {o['root']}"),
            [print("  move:", m) for m in o["moves"]],
            [print("  meta:", m) for m in o["meta_created"]],
            print("  " + o["note"]) if o.get("note") else None))
        return EXIT_OK
    if args.use:
        result = use(p, args.use)
        _emit(result, args.json, lambda o: print(
            f"{o['set']} ({o['title']}) -> " + ", ".join(o["written"])))
        return EXIT_OK

    out = {"start_sets": [{"id": x.id, "title": x.title, "description": x.description,
                           "source": x.source, "default": x.is_default,
                           "order": x.order, "generated": x.generated,
                           "prologue_chars": len(x.prologue),
                           "opening_chars": len(x.opening_situation)}
                          for x in p.start_sets]}

    def human(o):
        for x in o["start_sets"]:
            mark = "*" if x["default"] else " "
            tag = " (생성물)" if x["generated"] else ""
            print(f" {mark} {x['id']:14s} {x['title']:26s} "
                  f"프롤로그 {x['prologue_chars']:5d}자  첫상황 {x['opening_chars']:4d}자  "
                  f"{x['source']}{tag}")
    _emit(out, args.json, human)
    return EXIT_OK


def cmd_serve(args) -> int:
    from .webui import serve
    serve(args.project, host=args.host, port=args.port, spec=args.spec,
          store=args.store, open_browser=not args.no_open, key_file=args.key_file)
    return EXIT_OK


def cmd_sessions(args) -> int:
    store = Store(args.store)
    log = ActivationLog(args.logs or store.root.parent / "logs")

    targets: list[str] = []
    if args.delete_all:
        targets = store.list()
    elif args.delete:
        targets = list(args.delete)

    if targets:
        removed = []
        for sid in targets:
            removed.append({"id": sid, "session": store.delete(sid),
                            "log": log.delete(sid)})
        out = {"store": str(store.root), "removed": removed,
               "sessions": store.list()}
        _emit(out, args.json, lambda o: [
            print(("deleted " if r["session"] else "not found ") + r["id"]
                  + (" (+log)" if r["log"] else ""))
            for r in o["removed"]])
        return EXIT_OK

    out = {"store": str(store.root), "sessions": store.list()}
    _emit(out, args.json, lambda o: print("\n".join(o["sessions"]) or "(none)"))
    return EXIT_OK


# ── argument parsing ──────────────────────────────────────────────

def _add_global_flags(ap: argparse.ArgumentParser) -> None:
    """Global flags are attached to the top parser and to every subcommand, so
    an agent can write them on either side of the subcommand name."""
    ap.add_argument("--json", action="store_true", help="emit a single JSON object")
    ap.add_argument("--spec", help="path to crack_spec.yaml")
    ap.add_argument("--project", help="path to a Crack build/ directory")
    ap.add_argument("--variant", help="safe | unsafe | default (default: safe)")
    ap.add_argument("--store", help="session store directory")
    ap.add_argument("--provider", help="ollama | openrouter | gemini | openai | echo")
    ap.add_argument("--model", help="override the provider's model id")
    ap.add_argument("--base-url", help="override the provider's base url")
    ap.add_argument("--temperature", type=float)
    ap.add_argument("--fidelity", choices=["crack", "extended"])
    ap.add_argument("--window-turns", type=int, help="context window, in turns")
    ap.add_argument("--scan-turns", type=int, help="keyword scan depth, in turns")
    ap.add_argument("--recall", choices=["recent", "lexical", "manual"])
    ap.add_argument("--persona-name", help="persona label (default: {{user}})")
    ap.add_argument("--persona")
    ap.add_argument("--user-note")
    ap.add_argument("--goal")
    ap.add_argument("--start-set", help="opening to start from (see `parse`)")


DEFAULTS = {"variant": "safe", "persona_name": "{{user}}"}


def build_parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(add_help=False)
    _add_global_flags(top)

    # The subcommand copy suppresses unset values so that a flag written before
    # the subcommand is not clobbered by the subparser's own default.
    common = argparse.ArgumentParser(add_help=False, argument_default=argparse.SUPPRESS)
    _add_global_flags(common)

    ap = argparse.ArgumentParser(
        prog="crack-emu", parents=[top],
        description="Crack story-chat emulator / QA harness")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name: str, help: str) -> argparse.ArgumentParser:
        return sub.add_parser(name, help=help, parents=[common])

    add("parse", "parse a build dir and dump its structure").set_defaults(fn=cmd_parse)

    p = add("lint", "static integrity check of the authored build")
    p.add_argument("--max-entry-chars", type=int, default=400)
    p.add_argument("--target-entry-chars", type=int, default=360)
    p.set_defaults(fn=cmd_lint)

    add("health", "check LLM provider reachability").set_defaults(fn=cmd_health)
    add("spec", "dump the effective spec").set_defaults(fn=cmd_spec)
    p = add("sessions", "list or delete stored sessions")
    p.add_argument("--delete", nargs="+", metavar="ID", help="delete these sessions")
    p.add_argument("--delete-all", action="store_true", help="delete every session")
    p.add_argument("--logs", help="log directory (default: <store>/../logs)")
    p.set_defaults(fn=cmd_sessions)

    p = add("start", "create a session seeded with the prologue")
    p.add_argument("session")
    p.add_argument("--no-prologue", action="store_true")
    p.set_defaults(fn=cmd_start)

    p = add("turn", "run one turn and validate the reply")
    p.add_argument("session")
    p.add_argument("--input", help="user input; reads stdin when omitted")
    p.add_argument("--no-qa", action="store_true")
    p.set_defaults(fn=cmd_turn)

    p = add("prompt", "dump the assembled prompt, no model call")
    p.add_argument("session")
    p.add_argument("--input", default="")
    p.set_defaults(fn=cmd_prompt)

    p = add("check", "validate a response file against the contract")
    p.add_argument("--file", help="response file; reads stdin when omitted")
    p.add_argument("--input", help="the user input that produced it (for echo checks)")
    p.set_defaults(fn=cmd_check)

    p = add("report", "aggregate activation logs into keyword-book statistics")
    p.add_argument("--sessions", nargs="*", help="limit to these session ids")
    p.add_argument("--logs", help="log directory (default: <store>/../logs)")
    p.add_argument("--always-ratio", type=float, default=0.9,
                   help="flag an entry firing on at least this share of turns")
    p.add_argument("--min-turns", type=int, default=10,
                   help="turns required before never-fired is treated as a finding")
    p.set_defaults(fn=cmd_report)

    p = add("sets", "list start sets, or copy one into build/")
    p.add_argument("--use", metavar="ID", help="copy this set's pair into build/")
    p.add_argument("--migrate", nargs="?", const="plan", choices=["plan", "apply"],
                   help="move departments/ to start-sets/ and scaffold meta.md")
    p.set_defaults(fn=cmd_sets)

    p = add("serve", "start the local web UI")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--no-open", action="store_true", help="do not open a browser")
    p.add_argument("--key-file", help="persist provider API keys here (mode 600). "
                                      "Keep it outside the repository.")
    p.set_defaults(fn=cmd_serve)

    p = add("replay", "run a scenario file end to end")
    p.add_argument("session")
    p.add_argument("scenario")
    p.add_argument("--fresh", action="store_true", help="delete the session first")
    p.set_defaults(fn=cmd_replay)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    for key, value in DEFAULTS.items():
        if getattr(args, key, None) is None:
            setattr(args, key, value)
    if args.cmd not in {"health", "spec", "sessions"} and not args.project:
        print("error: --project is required", file=sys.stderr)
        return EXIT_ERROR
    try:
        return args.fn(args)
    except Exception as e:
        if args.json:
            json.dump({"error": f"{type(e).__name__}: {e}"}, sys.stdout, ensure_ascii=False)
            sys.stdout.write("\n")
        else:
            print(f"error: {type(e).__name__}: {e}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
