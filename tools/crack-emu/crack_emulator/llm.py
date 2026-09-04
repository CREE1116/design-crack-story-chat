"""OpenAI-compatible chat client over urllib. No third-party dependency.

Works against Ollama (`http://localhost:11434/v1`), any OpenAI-compatible
gateway, or the OpenAI API itself — only `llm.base_url` and `llm.model` change.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

from .config import Config


class LLMError(RuntimeError):
    pass


class Client:
    def __init__(self, cfg: Config, provider: str | None = None,
                 api_key: str | None = None):
        self.provider = provider or cfg.get("llm.provider", "ollama")
        preset = cfg.get(f"providers.{self.provider}") or {}
        if not preset:
            raise LLMError(
                f"unknown provider '{self.provider}'. "
                f"available: {', '.join(cfg.get('providers', {}))}"
            )
        self.base_url = str(cfg.get("llm.base_url") or preset["base_url"]).rstrip("/")
        self.model = cfg.get("llm.model") or preset["model"]
        self.temperature = float(cfg.get("llm.temperature", 0.9))
        self.max_tokens = int(cfg.get("llm.max_tokens", 2048))
        self.timeout = int(cfg.get("llm.timeout", 300))
        key_env = preset.get("api_key_env")
        self.api_key_env = key_env
        # A key typed into the UI wins over the environment; it lives only in
        # this process's memory and is never written to disk or echoed back.
        self.api_key = api_key or (os.environ.get(key_env, "") if key_env else "")
        if key_env and not self.api_key:
            self.missing_key = key_env
        else:
            self.missing_key = None
        self.last_usage: dict = {}

    def _require_key(self) -> None:
        if self.api_key_env and not self.api_key:
            raise LLMError(
                f"{self.provider}: API 키가 없습니다. "
                f"웹 UI 의 'API 키' 칸에 넣고 '키 저장' 을 누르거나, "
                f"환경변수 {self.api_key_env} 를 설정한 뒤 서버를 다시 시작하세요.\n"
                f"(UI 에 저장한 키는 서버 프로세스 메모리에만 있어 서버를 끄면 사라집니다.)"
            )

    def complete(self, system: str, messages: list[dict], *, model: str | None = None,
                 temperature: float | None = None, max_tokens: int | None = None,
                 retries: int = 2) -> str:
        self._require_key()
        payload = {
            "model": model or self.model,
            "messages": [{"role": "system", "content": system}, *messages],
            "temperature": self.temperature if temperature is None else temperature,
            "max_tokens": self.max_tokens if max_tokens is None else max_tokens,
            "stream": False,
        }
        body_bytes = json.dumps(payload).encode("utf-8")

        def build_request() -> urllib.request.Request:
            # Built fresh per attempt: urlopen mutates the Request (and a
            # redirect replaces it outright), so a reused object can go out
            # without the Authorization header it was created with.
            return urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=body_bytes,
                headers={
                    "Content-Type": "application/json",
                    **({"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}),
                },
                method="POST",
            )

        last_err: Exception | None = None
        for attempt in range(retries + 1):
            try:
                with urllib.request.urlopen(build_request(), timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                self.last_usage = data.get("usage", {}) or {}
                return data["choices"][0]["message"]["content"] or ""
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", "replace")[:500]
                auth_failed = (e.code in (401, 403)
                               or "Authorization" in body
                               or "API key" in body
                               or "API_KEY_INVALID" in body)
                if auth_failed:
                    raise LLMError(
                        f"{self.provider}: 인증 실패. 키가 없거나 잘못되었습니다. "
                        f"UI 의 'API 키' 칸에 다시 넣고 '키 저장' 을 누르세요"
                        + (f" (또는 환경변수 {self.api_key_env})." if self.api_key_env else ".")
                        + "\n서버를 재시작하면 UI 에 저장한 키는 사라집니다."
                        + f"\n[진단] 이 요청에 키 첨부됨={bool(self.api_key)}"
                        + (f", 길이={len(self.api_key)}" if self.api_key else "")
                        + f", 시도={attempt + 1}/{retries + 1}"
                        + f"\n원문: {body[:200]}"
                    ) from e
                last_err = LLMError(f"HTTP {e.code} from {self.base_url}: {body}")
            except Exception as e:  # network, json, key errors
                last_err = LLMError(f"{type(e).__name__}: {e}")
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
        raise last_err  # type: ignore[misc]

    def health(self) -> dict:
        try:
            req = urllib.request.Request(f"{self.base_url}/models")
            if self.api_key:
                req.add_header("Authorization", f"Bearer {self.api_key}")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            names = [m.get("id") for m in data.get("data", [])]
            # Providers list ids with and without a "models/" prefix.
            bare = {n.split("/")[-1] for n in names if n}
            available = (self.model in names or self.model.split("/")[-1] in bare) \
                if names else None
            return {"ok": True, "provider": self.provider, "base_url": self.base_url,
                    "model": self.model, "models": names,
                    "model_available": available}
        except Exception as e:
            return {"ok": False, "provider": self.provider, "base_url": self.base_url,
                    "model": self.model, "missing_key": self.missing_key,
                    "error": f"{type(e).__name__}: {e}"}


class OllamaClient(Client):
    """Ollama through its native /api/chat.

    The OpenAI-compatible endpoint gives no way to raise the context window, so
    a 7,000-character system prompt fails against the 4,096-token default. The
    native endpoint takes `options.num_ctx`, which is the only way to make a
    full Crack prompt fit without rebuilding the model.
    """

    def __init__(self, cfg: Config, provider: str = "ollama",
                 api_key: str | None = None):
        super().__init__(cfg, provider, api_key)
        self.native_url = self.base_url[:-3].rstrip("/") if self.base_url.endswith("/v1") \
            else self.base_url
        self.num_ctx = int(cfg.get("llm.num_ctx", 16384))

    def _require_key(self) -> None:
        if self.api_key_env and not self.api_key:
            raise LLMError(
                f"{self.provider}: API 키가 없습니다. "
                f"웹 UI 의 'API 키' 칸에 넣고 '키 저장' 을 누르거나, "
                f"환경변수 {self.api_key_env} 를 설정한 뒤 서버를 다시 시작하세요.\n"
                f"(UI 에 저장한 키는 서버 프로세스 메모리에만 있어 서버를 끄면 사라집니다.)"
            )

    def complete(self, system: str, messages: list[dict], *, model: str | None = None,
                 temperature: float | None = None, max_tokens: int | None = None,
                 retries: int = 2) -> str:
        self._require_key()
        payload = {
            "model": model or self.model,
            "messages": [{"role": "system", "content": system}, *messages],
            "stream": False,
            "options": {
                "num_ctx": self.num_ctx,
                "temperature": self.temperature if temperature is None else temperature,
                "num_predict": self.max_tokens if max_tokens is None else max_tokens,
            },
        }
        body_bytes = json.dumps(payload).encode("utf-8")

        def build_request() -> urllib.request.Request:
            return urllib.request.Request(
                f"{self.native_url}/api/chat",
                data=body_bytes,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

        last_err: Exception | None = None
        for attempt in range(retries + 1):
            try:
                with urllib.request.urlopen(build_request(), timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                self.last_usage = {
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                }
                return (data.get("message") or {}).get("content", "") or ""
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", "replace")[:500]
                if "exceed_context_size" in body or "context size" in body:
                    raise LLMError(
                        f"프롬프트가 모델 컨텍스트를 초과했습니다. num_ctx={self.num_ctx} 로 "
                        f"요청했지만 거부됨. 이 모델이 지원하는 최대 컨텍스트를 확인하거나 "
                        f"(`ollama show {self.model}`), 더 큰 모델 또는 원격 프로바이더를 쓰세요.\n{body}"
                    ) from e
                last_err = LLMError(f"HTTP {e.code} from {self.native_url}: {body}")
            except Exception as e:
                last_err = LLMError(f"{type(e).__name__}: {e}")
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
        raise last_err  # type: ignore[misc]


class EchoClient(Client):
    """Offline stand-in: returns a canned reply so plumbing and QA rules can be
    exercised without a model. Selected with `--provider echo`."""

    def __init__(self, cfg: Config, canned: str = "", api_key: str | None = None):
        super().__init__(cfg, provider="echo")
        self.canned = canned or (
            "*라임 대리가 둥글레차를 내밀며 젤리 같은 어깨를 살짝 기울인다.*\n\n"
            '![라임](https://baal-corp.pages.dev/06/s02.webp)\n'
            '라임 | "천천히 해요. 제가 사수니까 지켜줄게요."\n\n'
            "```Info\n[⌛1] [8월 29일 금｜09:30｜본사 7층：상품기획팀｜☀️]\n━\n"
            "[신입]: 미상(♂)｜미상｜입사 1일째\n"
            "[실적]: 세계정복률 0.12% (+0.00%p)｜분기목표 +0.04%p｜수습 D-90｜사랑의 묘약 검토\n━\n"
            "[현장]: 라임(맞은편 자리)\n[관계]:\n  ▸ 라임·'사수'·동료·🙂\n━\n"
            "[목표]: 첫 출근 안착\n[상황]: \"둥글레차를 받는다\"｜🟢\n```"
        )

    def complete(self, system: str, messages: list[dict], **kw) -> str:  # type: ignore[override]
        self.last_usage = {"prompt_tokens": 0, "completion_tokens": 0}
        return self.canned

    def health(self) -> dict:
        return {"ok": True, "provider": "echo", "base_url": "echo://",
                "model": "echo", "models": ["echo"], "model_available": True}


class AgentClient(Client):
    """Client for agent/manual self-response mode.
    
    Instead of calling an external LLM API, the agent or user directly crafts
    the character/story response and submits it via turn(..., reply=...) or
    play_turn(reply=...).
    """

    def __init__(self, cfg: Config, api_key: str | None = None):
        super().__init__(cfg, provider="agent")
        self.model = "agent-injected"

    def complete(self, system: str, messages: list[dict], **kw) -> str:  # type: ignore[override]
        raise LLMError(
            "자가 응답 모드(agent)에서는 외부 API를 호출하지 않습니다. "
            "모델 또는 에이전트가 직접 생성한 응답 텍스트를 'reply' 파라미터로 전달해야 합니다. "
            "(예: CLI --reply '...' 또는 --reply-file '...')"
        )

    def health(self) -> dict:
        return {"ok": True, "provider": "agent", "base_url": "agent://",
                "model": "agent-injected", "models": ["agent-injected"],
                "model_available": True}


def make_client(cfg: Config, provider: str | None = None, canned: str = "",
                api_key: str | None = None) -> Client:
    provider = provider or cfg.get("llm.provider", "ollama")
    if provider == "echo":
        return EchoClient(cfg, canned)
    if provider in ("agent", "manual"):
        return AgentClient(cfg, api_key)
    if provider == "ollama":
        return OllamaClient(cfg, provider, api_key)
    return Client(cfg, provider, api_key)
