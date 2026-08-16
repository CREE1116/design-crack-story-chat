#!/usr/bin/env python3
"""ComfyUI 흉내만 내는 테스트용 서버.

GPU 없이 batch.py의 큐잉·대기·다운로드 경로를 그대로 확인할 수 있다.
실제 그림은 안 나오고 단색 PNG가 저장된다.

  python mock_server.py &            8188 포트로 뜬다
  python batch.py --list-models
  python batch.py --check
  python batch.py --only ju-habin --situations normal --no-scenes
"""

from __future__ import annotations

import json
import struct
import sys
import zlib
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

CHECKPOINTS = ["illustriousXL_v01.safetensors", "ponyDiffusionV6XL.safetensors",
               "animagineXL_v31.safetensors"]
LORAS = ["webtoon_style.safetensors", "juhabin_v1.safetensors"]
SAMPLERS = ["euler", "euler_ancestral", "dpmpp_2m", "dpmpp_2m_sde", "ddim"]
SCHEDULERS = ["normal", "karras", "exponential", "sgm_uniform"]

JOBS: dict[str, dict] = {}


def png(w: int, h: int, rgb: tuple[int, int, int]) -> bytes:
    """의존성 없이 단색 PNG 한 장을 만든다."""
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6))
            + chunk(b"IEND", b""))


def enum_node(field: str, values: list[str], extra: dict | None = None) -> dict:
    node = {"input": {"required": {field: [values, {}]}}}
    if extra:
        node["input"]["required"].update({k: [v, {}] for k, v in extra.items()})
    return node


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):  # 조용히
        pass

    def _send(self, obj, code: int = 200) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        u = urlparse(self.path)
        if u.path == "/system_stats":
            return self._send({"system": {"comfyui_version": "mock"}})
        if u.path.startswith("/object_info/"):
            node = u.path.rsplit("/", 1)[1]
            table = {
                "CheckpointLoaderSimple": enum_node("ckpt_name", CHECKPOINTS),
                "LoraLoader": enum_node("lora_name", LORAS),
                "KSampler": enum_node("sampler_name", SAMPLERS, {"scheduler": SCHEDULERS}),
            }
            return self._send({node: table[node]} if node in table else {})
        if u.path.startswith("/history/"):
            pid = u.path.rsplit("/", 1)[1]
            job = JOBS.get(pid)
            if not job:
                return self._send({})
            return self._send({pid: {
                "status": {"status_str": "success", "completed": True},
                "outputs": {"7": {"images": [{"filename": f"{pid}.png",
                                              "subfolder": "hunter", "type": "output"}]}}}})
        if u.path == "/view":
            q = parse_qs(u.query)
            pid = q.get("filename", ["x.png"])[0].removesuffix(".png")
            job = JOBS.get(pid, {"w": 64, "h": 64, "seed": 0})
            s = job["seed"]
            body = png(max(8, job["w"] // 8), max(8, job["h"] // 8),
                       (s * 37 % 256, s * 91 % 256, s * 53 % 256))
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self._send({"error": "not found"}, 404)

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/prompt":
            return self._send({"error": "not found"}, 404)
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"] or 0)) or b"{}")
        g = payload.get("prompt", {})

        # 실제 서버처럼 그래프를 최소한만 검증한다.
        try:
            ckpt = g["1"]["inputs"]["ckpt_name"]
            latent = g["4"]["inputs"]
            ks = g["5"]["inputs"]
        except KeyError as exc:
            return self._send({"error": f"malformed graph: missing {exc}"}, 400)
        if ckpt not in CHECKPOINTS:
            return self._send({"error": f"unknown checkpoint {ckpt}"}, 400)
        for nid, node in g.items():
            if node.get("class_type") == "LoraLoader" and node["inputs"]["lora_name"] not in LORAS:
                return self._send({"error": f"unknown lora {node['inputs']['lora_name']}"}, 400)
        if ks["sampler_name"] not in SAMPLERS or ks["scheduler"] not in SCHEDULERS:
            return self._send({"error": "unknown sampler/scheduler"}, 400)

        pid = f"mock{len(JOBS):04d}"
        JOBS[pid] = {"w": latent["width"], "h": latent["height"], "seed": ks["seed"]}
        return self._send({"prompt_id": pid, "number": len(JOBS)})


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8188
    print(f"mock ComfyUI on 127.0.0.1:{port}", flush=True)
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
