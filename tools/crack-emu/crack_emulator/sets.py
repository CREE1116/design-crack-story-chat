"""Materialise and migrate start sets.

`build/prologue.md` and `build/start-prompt.md` are what Crack uploads, so they
have to exist; but keeping them as the only copy means the build cannot say
which opening it holds. Sets live in `start-sets/<id>/` and one of them is
copied into `build/` on demand.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from .models import Project, StartSet

CANONICAL_DIR = "start-sets"
LEGACY_DIR = "departments"

META_TEMPLATE = """# {title}
{description}

- order: {order}
- default: {default}
"""


def project_root(build_dir: str | Path) -> Path:
    p = Path(build_dir).expanduser().resolve()
    return p.parent if p.name == "build" else p


def use(project: Project, set_id: str) -> dict:
    """Copy one set's pair into build/. Returns what changed."""
    root = project_root(project.root)
    build = Path(project.root)
    chosen: StartSet | None = next(
        (x for x in project.start_sets if x.id == set_id and not x.generated), None)
    if chosen is None:
        available = [x.id for x in project.start_sets if not x.generated]
        raise ValueError(f"unknown start set '{set_id}'. available: {available}")

    src = root / chosen.source
    written = []
    for name in ("prologue.md", "start-prompt.md"):
        s = src / name
        if not s.is_file():
            continue
        shutil.copy2(s, build / name)
        written.append(str((build / name).relative_to(root)))
    return {"set": chosen.id, "title": chosen.title, "source": chosen.source,
            "written": written}


def migrate(build_dir: str | Path, *, apply: bool = False) -> dict:
    """Move a legacy `departments/` tree to `start-sets/` and scaffold meta.md."""
    root = project_root(build_dir)
    legacy, canonical = root / LEGACY_DIR, root / CANONICAL_DIR
    plan: dict = {"root": str(root), "moves": [], "meta_created": [], "applied": apply}

    source = legacy if legacy.is_dir() else canonical
    if not source.is_dir():
        plan["note"] = f"{LEGACY_DIR}/ 도 {CANONICAL_DIR}/ 도 없습니다"
        return plan

    if source is legacy:
        plan["moves"].append(f"{LEGACY_DIR}/ -> {CANONICAL_DIR}/")
        if apply:
            if canonical.exists():
                raise FileExistsError(f"{canonical} already exists; merge by hand")
            legacy.rename(canonical)
        source = canonical if apply else legacy

    folders = sorted(p for p in source.iterdir() if p.is_dir())
    for i, folder in enumerate(folders):
        meta = folder / "meta.md"
        if meta.exists():
            continue
        title = re.sub(r"^\d+[_-]", "", folder.name)
        plan["meta_created"].append(str(meta.relative_to(root)) if apply
                                    else f"{CANONICAL_DIR}/{folder.name}/meta.md")
        if apply:
            meta.write_text(
                META_TEMPLATE.format(title=title, description="",
                                     order=i, default="true" if i == 0 else "false"),
                encoding="utf-8")
    return plan
