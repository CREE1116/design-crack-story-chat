"""Session persistence. One JSON file per session under the store root."""
from __future__ import annotations

import json
from pathlib import Path

from .models import Session

DEFAULT_STORE = Path(".crack-emu/sessions")


class Store:
    def __init__(self, root: str | Path | None = None):
        self.root = Path(root or DEFAULT_STORE).expanduser()

    def path(self, session_id: str) -> Path:
        return self.root / f"{session_id}.json"

    def exists(self, session_id: str) -> bool:
        return self.path(session_id).exists()

    def load(self, session_id: str) -> Session:
        return Session.from_dict(json.loads(self.path(session_id).read_text(encoding="utf-8")))

    def save(self, session: Session) -> Path:
        p = self.path(session.id)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(session.to_dict(), ensure_ascii=False, indent=2),
                     encoding="utf-8")
        return p

    def list(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted(p.stem for p in self.root.glob("*.json"))

    def delete(self, session_id: str) -> bool:
        p = self.path(session_id)
        if p.exists():
            p.unlink()
            return True
        return False
