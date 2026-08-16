#!/usr/bin/env python3
"""A1111 WebUI 흉내만 내는 테스트용 서버.

GPU 없이 batch.py의 A1111 경로를 그대로 확인할 수 있다.

  python mock_a1111.py &          7860 포트
  python batch.py --list-models
  python batch.py --check
  python batch.py --only ju-habin --situations normal --no-scenes --no-monsters --no-backgrounds
"""

from __future__ import annotations

import base64
import json
import struct
import sys
import zlib
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

CHECKPOINTS = ["illustriousXL_v01.safetensors [a1b2c3]",
               "ponyDiffusionV6XL.safetensors [d4e5f6]",
               "animagineXL_v31.safetensors [7g8h9i]"]
LORAS = ["webtoon_style", "juhabin_v1"]
SAMPLERS = ["Euler a", "Euler", "DPM++ 2M", "DPM++ 2M SDE", "DDIM"]
SCHEDULERS = ["Automatic", "Karras", "Exponential", "SGM Uniform"]


def png(w: int, h: int, rgb: tuple[int, int, int]) -> bytes:
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6))
            + chunk(b"IEND", b""))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_a):
        pass

    def _send(self, obj, code: int = 200) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        table = {
            "/sdapi/v1/options": {"sd_model_checkpoint": CHECKPOINTS[0]},
            "/sdapi/v1/sd-models": [{"title": c, "model_name": c.split(".")[0]} for c in CHECKPOINTS],
            "/sdapi/v1/loras": [{"name": n, "alias": n} for n in LORAS],
            "/sdapi/v1/samplers": [{"name": s} for s in SAMPLERS],
            "/sdapi/v1/schedulers": [{"label": s, "name": s.lower()} for s in SCHEDULERS],
        }
        if path in table:
            return self._send(table[path])
        self._send({"detail": "Not Found"}, 404)

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/sdapi/v1/txt2img":
            return self._send({"detail": "Not Found"}, 404)
        p = json.loads(self.rfile.read(int(self.headers["Content-Length"] or 0)) or b"{}")

        # 실제 서버처럼 최소 검증
        ckpt = (p.get("override_settings") or {}).get("sd_model_checkpoint")
        if ckpt and ckpt not in CHECKPOINTS:
            return self._send({"detail": f"model not found: {ckpt}"}, 404)
        if p.get("sampler_name") not in SAMPLERS:
            return self._send({"detail": f"sampler not found: {p.get('sampler_name')}"}, 404)
        for tag in [t for t in p.get("prompt", "").split("<lora:")[1:]]:
            name = tag.split(":")[0]
            if name not in LORAS:
                return self._send({"detail": f"lora not found: {name}"}, 404)

        s = int(p.get("seed", 0))
        img = png(max(8, int(p.get("width", 512)) // 8),
                  max(8, int(p.get("height", 512)) // 8),
                  (s * 37 % 256, s * 91 % 256, s * 53 % 256))
        return self._send({"images": [base64.b64encode(img).decode()],
                           "parameters": p, "info": json.dumps({"seed": s})})


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 7860
    print(f"mock A1111 WebUI on 127.0.0.1:{port}", flush=True)
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
