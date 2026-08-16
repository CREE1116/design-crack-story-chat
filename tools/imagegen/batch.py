#!/usr/bin/env python3
"""헌터 스토리챗 이미지 일괄 생성 — Stable Diffusion 일괄 드라이버.

A1111/Forge WebUI와 ComfyUI를 모두 지원한다 (config.backend).

prompts.json의 캐릭터 × 상황을 전부 조합해 ComfyUI에 큐잉하고,
결과를 `out/<인물>/<상황>.png` 로 저장한다. 이 경로가 곧 스토리챗의
`{IMG}/인물/상황.png` 에셋 경로다.

  python batch.py --list-models          서버에 설치된 체크포인트·LoRA·샘플러 목록
  python batch.py --dry-run              조합과 프롬프트만 출력, 서버 불필요
  python batch.py --check                설정이 서버 자산과 맞는지만 검사
  python batch.py                        전부 생성 (이미 있는 파일은 건너뜀)
  python batch.py --only ju-habin --situations normal
  python batch.py --checkpoint other.safetensors --lora style.safetensors:0.7:0.7
"""

from __future__ import annotations

import argparse
import base64
import difflib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent


# ── 설정 ────────────────────────────────────────────────────────────────────

def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"설정 파일이 없습니다: {path}")
    except json.JSONDecodeError as exc:
        sys.exit(f"prompts.json 파싱 실패 ({exc.lineno}행): {exc.msg}")


def parse_lora(spec: str) -> dict:
    """`이름[:model[:clip]]` → {'name','model','clip'}"""
    parts = spec.split(":")
    name = parts[0]
    try:
        m = float(parts[1]) if len(parts) > 1 and parts[1] else 1.0
        c = float(parts[2]) if len(parts) > 2 and parts[2] else m
    except ValueError:
        sys.exit(f"--lora 강도는 숫자여야 합니다: {spec}")
    return {"name": name, "model": m, "clip": c}


def build_prompt(d: dict, kind: str, key: str, situation: str | None) -> tuple[str, str, list[int], int]:
    cfg, common = d["config"], d["common"]
    preset_name = cfg["quality_preset"]
    if preset_name not in d["quality_presets"]:
        sys.exit(f"모르는 quality_preset: {preset_name} (가능: {', '.join(d['quality_presets'])})")
    preset = d["quality_presets"][preset_name]
    style_name = cfg.get("style_preset")
    if style_name and style_name not in d.get("style_presets", {}):
        sys.exit(f"모르는 style_preset: {style_name} (가능: {', '.join(d.get('style_presets', {}))})")
    style = d.get("style_presets", {}).get(style_name, {})
    style_tags = style.get("tags") or common.get("style", "")
    neg = common["negative"]
    for extra in (preset.get("negative_extra"), style.get("negative_extra")):
        if extra:
            neg = f"{extra}, {neg}"

    BUCKET = {"scene": ("scenes", "scene_suffix", "scene_negative_extra"),
              "monster": ("monsters", "monster_suffix", "monster_negative_extra"),
              "background": ("backgrounds", "background_suffix", "background_negative_extra")}
    if kind in BUCKET:
        bucket, sfx, nx = BUCKET[kind]
        s = d[bucket][key]
        pos = ", ".join([preset["prefix"], style_tags, s["tags"], common[sfx]])
        return pos, f"{common[nx]}, {neg}", s["size"], s["seed"]

    c = d["characters"][key]
    if kind == "dataset":
        pool = d["dataset_variations"]
        n = int(situation)
        var = pool[n % len(pool)]
        # 학습셋은 같은 변주라도 시드를 계속 흔들어야 다양성이 생긴다.
        pos = ", ".join([preset["prefix"], style_tags, c["tags"], var, common["character_suffix"]])
        return pos, neg, [896, 1152], c["seed"] + 9000 + n

    sit = d["situations"][situation]
    pos = ", ".join([preset["prefix"], style_tags, c["tags"], sit["tags"], common["character_suffix"]])
    # 캐릭터 고정 시드 + 상황 오프셋 → 상황만 바뀔 때 얼굴이 덜 흔들린다.
    seed = c["seed"] + list(d["situations"]).index(situation)
    return pos, neg, sit["size"], seed


def resolve_assets(d: dict, kind: str, key: str) -> tuple[str, list[dict]]:
    """이 작업에 쓸 (체크포인트, LoRA 체인)."""
    cfg = d["config"]
    ckpt = cfg["checkpoint"]
    loras = list(cfg.get("loras", []))
    if kind in ("char", "dataset"):
        c = d["characters"][key]
        ckpt = c.get("checkpoint", ckpt)          # 캐릭터별 체크포인트 override
        loras += c.get("loras", [])
    return ckpt, loras


# ── ComfyUI 그래프 ───────────────────────────────────────────────────────────

def build_graph(d: dict, ckpt: str, pos: str, neg: str,
                size: list[int], seed: int, loras: list[dict]) -> dict:
    cfg = d["config"]
    g: dict = {"1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt}}}
    model_src, clip_src = ["1", 0], ["1", 1]
    for i, lora in enumerate(loras, start=1):
        nid = f"lora{i}"
        g[nid] = {"class_type": "LoraLoader", "inputs": {
            "lora_name": lora["name"],
            "strength_model": float(lora.get("model", 1.0)),
            "strength_clip": float(lora.get("clip", lora.get("model", 1.0))),
            "model": model_src, "clip": clip_src}}
        model_src, clip_src = [nid, 0], [nid, 1]

    g["2"] = {"class_type": "CLIPTextEncode", "inputs": {"text": pos, "clip": clip_src}}
    g["3"] = {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": clip_src}}
    g["4"] = {"class_type": "EmptyLatentImage",
              "inputs": {"width": size[0], "height": size[1], "batch_size": 1}}
    g["5"] = {"class_type": "KSampler", "inputs": {
        "seed": seed, "steps": cfg["steps"], "cfg": cfg["cfg"],
        "sampler_name": cfg["sampler"], "scheduler": cfg["scheduler"], "denoise": 1.0,
        "model": model_src, "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["4", 0]}}
    g["6"] = {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}}
    g["7"] = {"class_type": "SaveImage", "inputs": {"filename_prefix": "hunter/tmp", "images": ["6", 0]}}
    return g


# ── API ─────────────────────────────────────────────────────────────────────

class Comfy:
    name = "comfy"

    def __init__(self, server: str):
        self.base = server if server.startswith("http") else f"http://{server}"
        self.client_id = str(uuid.uuid4())

    def _get(self, path: str) -> dict:
        with urllib.request.urlopen(f"{self.base}{path}", timeout=30) as r:
            return json.loads(r.read())

    def _post(self, path: str, payload: dict) -> dict:
        req = urllib.request.Request(f"{self.base}{path}", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:500]
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc

    def ping(self) -> None:
        try:
            self._get("/system_stats")
        except (urllib.error.URLError, OSError) as exc:
            sys.exit(f"ComfyUI에 연결할 수 없습니다 ({self.base}): {exc}\n"
                     f"서버를 켜고 prompts.json의 config.server를 확인하세요.")

    def _enum(self, node: str, field: str) -> list[str]:
        """/object_info 에서 그 노드 입력의 선택지 목록을 뽑는다."""
        try:
            info = self._get(f"/object_info/{node}")
        except Exception:
            return []
        try:
            spec = info[node]["input"]["required"][field][0]
            return list(spec) if isinstance(spec, list) else []
        except (KeyError, TypeError, IndexError):
            return []

    def checkpoints(self) -> list[str]:
        return self._enum("CheckpointLoaderSimple", "ckpt_name")

    def loras(self) -> list[str]:
        return self._enum("LoraLoader", "lora_name")

    def samplers(self) -> list[str]:
        return self._enum("KSampler", "sampler_name")

    def schedulers(self) -> list[str]:
        return self._enum("KSampler", "scheduler")

    def queue(self, graph: dict) -> str:
        res = self._post("/prompt", {"prompt": graph, "client_id": self.client_id})
        if "prompt_id" not in res:
            raise RuntimeError(f"서버가 prompt_id를 주지 않았습니다: {str(res)[:300]}")
        return res["prompt_id"]

    def wait(self, pid: str, timeout: int) -> dict:
        deadline = time.time() + timeout
        while time.time() < deadline:
            hist = self._get(f"/history/{pid}")
            entry = hist.get(pid)
            if entry:
                status = entry.get("status", {})
                if status.get("status_str") == "error" or status.get("completed") is False:
                    msgs = status.get("messages") or []
                    raise RuntimeError(f"서버 측 실행 오류: {str(msgs)[:300]}")
                return entry
            time.sleep(1.0)
        raise TimeoutError(f"{timeout}초 안에 완료되지 않았습니다 (prompt_id={pid})")

    def fetch(self, img: dict) -> bytes:
        q = urllib.parse.urlencode({"filename": img["filename"],
                                    "subfolder": img.get("subfolder", ""),
                                    "type": img.get("type", "output")})
        with urllib.request.urlopen(f"{self.base}/view?{q}", timeout=120) as r:
            return r.read()

    def generate(self, d, ckpt, pos, neg, size, seed, loras, timeout) -> bytes:
        pid = self.queue(build_graph(d, ckpt, pos, neg, size, seed, loras))
        hist = self.wait(pid, timeout)
        images = [i for o in hist.get("outputs", {}).values() for i in o.get("images", [])]
        if not images:
            raise RuntimeError("서버가 이미지를 반환하지 않았습니다")
        return self.fetch(images[0])


class A1111:
    """AUTOMATIC1111 / Forge WebUI. 실행 시 `--api` 플래그가 필요하다."""

    name = "a1111"

    def __init__(self, server: str):
        self.base = server if server.startswith("http") else f"http://{server}"
        self._ckpt_map: dict[str, str] | None = None

    def _get(self, path: str):
        with urllib.request.urlopen(f"{self.base}{path}", timeout=30) as r:
            return json.loads(r.read())

    def _post(self, path: str, payload: dict, timeout: int):
        req = urllib.request.Request(f"{self.base}{path}", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"HTTP {exc.code}: {exc.read().decode(errors='replace')[:400]}") from exc

    def ping(self) -> None:
        try:
            self._get("/sdapi/v1/options")
        except (urllib.error.URLError, OSError) as exc:
            sys.exit(f"WebUI에 연결할 수 없습니다 ({self.base}): {exc}\n"
                     f"WebUI를 --api 플래그와 함께 켜고 config.server를 확인하세요.\n"
                     f"  예: ./webui.sh --api      (윈도우면 webui-user.bat 의 COMMANDLINE_ARGS 에 --api)")

    def _names(self, path: str, *keys: str) -> list[str]:
        try:
            data = self._get(path)
        except Exception:
            return []
        out = []
        for item in data if isinstance(data, list) else []:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                for k in keys:
                    if item.get(k):
                        out.append(item[k]); break
        return out

    def checkpoints(self) -> list[str]:
        # WebUI는 `파일명.safetensors [해시]` 형태의 title을 쓴다. 파일명만 적어도
        # 통과하도록 두 표기를 모두 유효한 이름으로 내놓는다.
        try:
            data = self._get("/sdapi/v1/sd-models")
        except Exception:
            return []
        out: list[str] = []
        for m in data if isinstance(data, list) else []:
            for k in ("title", "model_name"):
                if m.get(k):
                    out.append(m[k])
            title = m.get("title", "")
            if " [" in title:
                out.append(title.split(" [")[0])
        return list(dict.fromkeys(out))

    def loras(self) -> list[str]:
        return self._names("/sdapi/v1/loras", "name", "alias")

    def samplers(self) -> list[str]:
        return self._names("/sdapi/v1/samplers", "name")

    def schedulers(self) -> list[str]:
        return self._names("/sdapi/v1/schedulers", "label", "name")

    def _resolve_ckpt(self, name: str) -> str:
        """설정에 적힌 이름을 서버가 쓰는 정식 title 로 바꾼다.

        WebUI의 title 은 `파일명.safetensors [해시]` 형태라 설정에 파일명만
        적으면 일부 서버가 못 찾는다. 여기서 미리 맞춰 보낸다.
        """
        if self._ckpt_map is None:
            self._ckpt_map = {}
            try:
                for m in self._get("/sdapi/v1/sd-models") or []:
                    title = m.get("title")
                    if not title:
                        continue
                    for key in (title, m.get("model_name"), title.split(" [")[0]):
                        if key:
                            self._ckpt_map.setdefault(key, title)
            except Exception:
                pass
        return self._ckpt_map.get(name, name)

    def generate(self, d, ckpt, pos, neg, size, seed, loras, timeout) -> bytes:
        cfg = d["config"]
        ckpt = self._resolve_ckpt(ckpt)
        # WebUI는 LoRA를 노드가 아니라 프롬프트 문법으로 받는다.
        tags = "".join(f" <lora:{Path(l['name']).stem}:{l.get('model', 1.0)}>" for l in loras)
        payload = {
            "prompt": pos + tags, "negative_prompt": neg,
            "steps": cfg["steps"], "cfg_scale": cfg["cfg"],
            "width": size[0], "height": size[1],
            "sampler_name": cfg["sampler"], "scheduler": cfg["scheduler"],
            "seed": seed, "batch_size": 1, "n_iter": 1,
            "override_settings": {"sd_model_checkpoint": ckpt},
            "override_settings_restore_afterwards": True,
        }
        res = self._post("/sdapi/v1/txt2img", payload, timeout)
        if not res.get("images"):
            raise RuntimeError(f"서버가 이미지를 반환하지 않았습니다: {str(res)[:300]}")
        return base64.b64decode(res["images"][0].split(",", 1)[-1])


def make_backend(cfg: dict):
    kind = cfg.get("backend", "comfy")
    if kind not in ("a1111", "comfy"):
        sys.exit(f"모르는 backend: {kind} (가능: a1111, comfy)")
    return (A1111 if kind == "a1111" else Comfy)(cfg["server"])


# ── 자산 검증 ────────────────────────────────────────────────────────────────

def near(name: str, pool: list[str]) -> str:
    hit = difflib.get_close_matches(name, pool, n=3, cutoff=0.4)
    if hit:
        return "  가까운 이름: " + ", ".join(hit)
    return "  (--list-models 로 설치된 목록을 확인하세요)"


def verify(api: Comfy, d: dict, jobs: list) -> list[str]:
    """설정이 서버 자산과 맞는지 확인하고 문제 목록을 돌려준다."""
    errs: list[str] = []
    ckpts, loras = api.checkpoints(), api.loras()
    samplers, scheds = api.samplers(), api.schedulers()

    need_ckpt, need_lora = set(), set()
    for kind, key, _situ, _p in jobs:
        c, ls = resolve_assets(d, kind, key)
        need_ckpt.add(c)
        need_lora.update(l["name"] for l in ls)

    if ckpts:
        for c in sorted(need_ckpt):
            if c not in ckpts:
                errs.append(f"체크포인트 없음: {c}\n{near(c, ckpts)}")
    if loras:
        for l in sorted(need_lora):
            if l not in loras:
                errs.append(f"LoRA 없음: {l}\n{near(l, loras)}")
    if samplers and d["config"]["sampler"] not in samplers:
        errs.append(f"샘플러 없음: {d['config']['sampler']}\n{near(d['config']['sampler'], samplers)}")
    if scheds and d["config"]["scheduler"] not in scheds:
        errs.append(f"스케줄러 없음: {d['config']['scheduler']}\n{near(d['config']['scheduler'], scheds)}")
    return errs


def show_models(api: Comfy) -> int:
    def block(title: str, items: list[str]) -> None:
        print(f"\n{title} ({len(items)}개)")
        if not items:
            print("  (목록을 읽지 못했습니다)")
        for i in items:
            print(f"  {i}")
    block("체크포인트", api.checkpoints())
    block("LoRA", api.loras())
    block("샘플러", api.samplers())
    block("스케줄러", api.schedulers())
    print("\n이 이름을 prompts.json의 config.checkpoint / config.loras 에 그대로 넣으세요.")
    return 0


# ── 메인 ────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="헌터 스토리챗 이미지 일괄 생성")
    ap.add_argument("--config", default=str(HERE / "prompts.json"))
    ap.add_argument("--list-models", action="store_true", help="서버에 설치된 자산 목록만 출력")
    ap.add_argument("--check", action="store_true", help="설정이 서버 자산과 맞는지만 검사")
    ap.add_argument("--dry-run", action="store_true", help="서버 없이 조합만 확인")
    ap.add_argument("--only", help="캐릭터 슬러그 쉼표 구분")
    ap.add_argument("--situations", help="상황 슬러그 쉼표 구분")
    ap.add_argument("--scenes-only", action="store_true")
    ap.add_argument("--no-scenes", action="store_true")
    ap.add_argument("--monsters-only", action="store_true")
    ap.add_argument("--no-monsters", action="store_true")
    ap.add_argument("--backgrounds-only", action="store_true")
    ap.add_argument("--no-backgrounds", action="store_true")
    ap.add_argument("--style", help="style_preset 덮어쓰기")
    ap.add_argument("--dataset", help="LoRA 학습셋을 뽑을 캐릭터 슬러그")
    ap.add_argument("--count", type=int, help="학습셋 장수 (기본 config.dataset_count)")
    ap.add_argument("--force", action="store_true", help="기존 파일 덮어쓰기")
    ap.add_argument("--server", help="config.server 무시하고 이 주소 사용")
    ap.add_argument("--backend", choices=["a1111", "comfy"], help="이번 실행에 쓸 백엔드")
    ap.add_argument("--checkpoint", help="이번 실행에만 쓸 체크포인트")
    ap.add_argument("--lora", action="append", default=[],
                    help="추가 LoRA. `이름[:model[:clip]]`. 여러 번 쓸 수 있음")
    ap.add_argument("--preset", help="quality_preset 덮어쓰기")
    ap.add_argument("--steps", type=int)
    ap.add_argument("--cfg", type=float)
    ap.add_argument("--sampler")
    ap.add_argument("--scheduler")
    ap.add_argument("--out", help="출력 디렉터리")
    ap.add_argument("--timeout", type=int, default=600, help="장당 대기 상한(초)")
    a = ap.parse_args()

    d = load(Path(a.config))
    cfg = d["config"]
    for key, val in (("checkpoint", a.checkpoint), ("quality_preset", a.preset),
                     ("steps", a.steps), ("cfg", a.cfg),
                     ("sampler", a.sampler), ("scheduler", a.scheduler),
                     ("server", a.server), ("output_dir", a.out), ("style_preset", a.style),
                     ("backend", a.backend)):
        if val is not None:
            cfg[key] = val
    # 백엔드를 바꾸면 샘플러 이름 체계도 달라진다. 명시 지정이 없으면 기본값으로 맞춘다.
    if a.backend:
        for k, v in cfg.get("backend_defaults", {}).get(a.backend, {}).items():
            if getattr(a, k if k != "server" else "server", None) is None:
                cfg[k] = v
    cfg["loras"] = list(cfg.get("loras", [])) + [parse_lora(s) for s in a.lora]

    if a.list_models:
        api = make_backend(cfg); api.ping()
        return show_models(api)

    out = Path(cfg.get("output_dir", "out"))
    if not out.is_absolute():
        out = (HERE / out).resolve()

    chars, situs = list(d["characters"]), list(d["situations"])
    if a.only:
        chars = [c.strip() for c in a.only.split(",")]
        if bad := [c for c in chars if c not in d["characters"]]:
            sys.exit(f"모르는 캐릭터 슬러그: {', '.join(bad)}\n가능: {', '.join(d['characters'])}")
    if a.situations:
        situs = [s.strip() for s in a.situations.split(",")]
        if bad := [s for s in situs if s not in d["situations"]]:
            sys.exit(f"모르는 상황 슬러그: {', '.join(bad)}\n가능: {', '.join(d['situations'])}")

    if a.dataset:
        if a.dataset not in d["characters"]:
            sys.exit(f"모르는 캐릭터 슬러그: {a.dataset}\n가능: {', '.join(d['characters'])}")
        n = a.count or cfg.get("dataset_count", 24)
        jobs = [("dataset", a.dataset, str(i), out / "_dataset" / a.dataset / f"{i:03d}.png")
                for i in range(n)]
        if not a.force:
            skip = sum(1 for j in jobs if j[3].exists())
            jobs = [j for j in jobs if not j[3].exists()]
            if skip:
                print(f"이미 있어서 건너뜀: {skip}개")
        if not jobs:
            print("생성할 게 없습니다.")
            return 0
        return run(d, cfg, jobs, out, a)

    only = [f for f in ("scenes", "monsters", "backgrounds")
            if getattr(a, f"{f}_only")]
    if len(only) > 1:
        sys.exit(f"--*-only 옵션은 하나만 씁니다: {', '.join('--'+o+'-only' for o in only)}")
    pick = only[0] if only else None
    jobs: list[tuple[str, str, str | None, Path]] = []
    if pick is None:
        jobs += [("char", c, s, out / c / f"{s}.png") for c in chars for s in situs]
    for bucket, kind, sub in (("scenes", "scene", "scene"),
                              ("monsters", "monster", "mob"),
                              ("backgrounds", "background", "bg")):
        if getattr(a, f"no_{bucket}") or (pick and pick != bucket):
            continue
        jobs += [(kind, k, None, out / sub / f"{k}.png") for k in d.get(bucket, {})]

    if not a.force:
        n_skip = sum(1 for j in jobs if j[3].exists())
        jobs = [j for j in jobs if not j[3].exists()]
        if n_skip:
            print(f"이미 있어서 건너뜀: {n_skip}개 (--force 로 덮어쓰기)")
    if not jobs:
        print("생성할 게 없습니다.")
        return 0

    return run(d, cfg, jobs, out, a)


def label_of(kind: str, key: str, situ: str | None) -> str:
    if kind == "dataset":
        return f"{key} #{situ}"
    return f"{key}/{situ}" if situ is not None else f"{kind}/{key}"


def run(d: dict, cfg: dict, jobs: list, out: Path, a) -> int:
    if a.dry_run:
        print(f"작업 {len(jobs)}개\n")
        for kind, key, situ, path in jobs:
            pos, neg, size, seed = build_prompt(d, kind, key, situ)
            ckpt, loras = resolve_assets(d, kind, key)
            lr = "".join(f" +{l['name']}@{l.get('model',1.0)}" for l in loras)
            print(f"── {label_of(kind,key,situ)}  {size[0]}x{size[1]}  seed={seed}  [{ckpt}{lr}]")
            print(f"   → {path}")
            print(f"   +{pos[:140]}{'…' if len(pos) > 140 else ''}\n")
        print("dry-run 이므로 아무것도 생성하지 않았습니다.")
        return 0

    api = make_backend(cfg)
    api.ping()
    errs = verify(api, d, jobs)
    if errs:
        print("설정과 서버 자산이 맞지 않습니다.\n", file=sys.stderr)
        for e in errs:
            print(f"  · {e}", file=sys.stderr)
        return 2
    if a.check:
        print(f"이상 없음 — 작업 {len(jobs)}개를 생성할 수 있습니다.")
        return 0

    print(f"작업 {len(jobs)}개\n")
    ok = fail = 0
    for n, (kind, key, situ, path) in enumerate(jobs, 1):
        label = label_of(kind, key, situ)
        try:
            pos, neg, size, seed = build_prompt(d, kind, key, situ)
            ckpt, loras = resolve_assets(d, kind, key)
            data = api.generate(d, ckpt, pos, neg, size, seed, loras, a.timeout)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            ok += 1
            print(f"[{n}/{len(jobs)}] {label} → {path}")
        except Exception as exc:  # noqa: BLE001
            fail += 1
            print(f"[{n}/{len(jobs)}] {label} 실패: {exc}", file=sys.stderr)

    print(f"\n완료 {ok}개, 실패 {fail}개 · 출력 {out}")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
