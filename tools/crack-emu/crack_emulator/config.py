"""Load the fidelity spec and apply overrides."""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

DEFAULT_SPEC = Path(__file__).resolve().parent.parent / "spec" / "crack_spec.yaml"


class Config:
    def __init__(self, data: dict[str, Any]):
        self.data = data

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Config":
        p = Path(path) if path else DEFAULT_SPEC
        return cls(yaml.safe_load(p.read_text(encoding="utf-8")))

    def get(self, dotted: str, default: Any = None) -> Any:
        cur: Any = self.data
        for part in dotted.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return default
            cur = cur[part]
        return cur

    def set(self, dotted: str, value: Any) -> None:
        parts = dotted.split(".")
        cur = self.data
        for part in parts[:-1]:
            cur = cur.setdefault(part, {})
        cur[parts[-1]] = value

    def override(self, pairs: dict[str, Any]) -> "Config":
        out = Config(copy.deepcopy(self.data))
        for k, v in pairs.items():
            if v is not None:
                out.set(k, v)
        return out

    @property
    def fidelity(self) -> str:
        return self.get("fidelity", "crack")

    def extension_enabled(self, name: str) -> bool:
        """Extensions are force-disabled in crack fidelity mode."""
        if self.fidelity == "crack":
            return False
        return bool(self.get(f"extension.{name}", False))
