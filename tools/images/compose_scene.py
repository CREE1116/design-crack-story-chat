#!/usr/bin/env python3
"""High-Precision Scene & Environment Prompt Composer, UC Generator, and Scene Design Markdown Exporter.

Complies with design-crack-story-chat scene-design-guide:
1. 🖼️ Pure Scenery CG (풍경화형 단독 배경): 5대 앵커 (no humans 락, 공간/건축, 조명/시간, 대기/날씨, 소품/랜드마크, 카메라)
2. 👥 Staged Character Environment (인물 결속형 배경): 4대 앵커 (환경 바인딩, 지지대/가구, 인물 조명, 심도)
3. Exporters for official build/assets/scene-design.md, NovelAI preset-backgrounds.json, and prompts.json
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Default Scenery Undesired Content (Negative Prompt) - Completely filters out characters/humans/anatomy
DEFAULT_SCENERY_UC = (
    "1girl, 1boy, 2girls, multiple girls, 2boys, multiple boys, female, male, person, "
    "human, people, character, face, eyes, mouth, nose, hair, body, head, hands, fingers, "
    "limbs, legs, feet, breasts, cleavage, skin, clothing, clothes, dress, suit, shirt, pants, "
    "skirt, shoes, bad anatomy, deformed, text, watermark, signature, artist name, lowres, "
    "worst quality, blurry, diptych, triptych, multi-panel, split screen, comic, character sheet"
)

# Default In-Scene Staged Undesired Content - Prevents flat backgrounds & retains depth
DEFAULT_STAGED_UC = (
    "white background, simple background, flat background, solid color background"
)

# Words that indicate character presence accidentally leaking into scenery prompts
HUMAN_LEAK_KEYWORDS = {
    "1girl", "1boy", "girl", "boy", "woman", "man", "person", "human", "character",
    "female", "male", "face", "eyes", "hair", "smile", "looking", "standing",
    "sitting", "walking", "holding", "hand", "hands", "breasts", "body", "dress", "suit"
}

# DB search paths for Danbooru tag validation
SEARCH_PATHS = [
    Path(__file__).resolve().parent / "data" / "wiki.sqlite3",
    Path("/Users/leejongmin/crack/novel-ai-image-skill/skills/novel-ai-image-skill/data/wiki.sqlite3"),
    Path.home() / "crack" / "novel-ai-image-skill" / "skills" / "novel-ai-image-skill" / "data" / "wiki.sqlite3",
]


def find_database() -> Path | None:
    for p in SEARCH_PATHS:
        if p.is_file():
            return p
    return None


class TagValidator:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or find_database()
        self.conn = None
        if self.db_path and self.db_path.is_file():
            try:
                self.conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
                self.conn.row_factory = sqlite3.Row
            except Exception:
                self.conn = None

    def is_exact_tag(self, tag: str) -> bool:
        if not self.conn:
            return True
        norm = " ".join(tag.casefold().replace("_", " ").replace("-", " ").split())
        row = self.conn.execute("SELECT 1 FROM pages WHERE tag_norm = ? LIMIT 1", (norm,)).fetchone()
        return row is not None


@dataclass
class SceneVisualSpec:
    id: str = "scene/a01"
    name: str = ""
    role: str = ""
    category: str = "indoor"  # indoor, outdoor, combat, urban, office, fantasy, dungeon

    # 1. 풍경화형 단독 배경 5대 앵커 (Pure Scenery CG)
    no_humans_lock: bool = True
    scenery_architecture: str = ""  # 공간 스케일 & 건축 (e.g. grand corporate lobby, glass entrance doors)
    scenery_props: str = ""         # 랜드마크 & 환경 소품 (e.g. speed gate turnstiles, reception desk)
    scenery_lighting: str = ""      # 시간대 & 조명 효과 (e.g. volumetric lighting, architectural lighting)
    scenery_atmosphere: str = ""    # 대기 & 날씨 연출 (e.g. sterile quiet atmosphere, light dust particles)
    scenery_camera: str = "wide angle, panoramic view"  # 카메라 화각 & 앵글 (e.g. wide angle, panoramic view, establishing shot)
    quality_prefix: str = "masterpiece, best quality, ultra-detailed, anime visual novel background"
    custom_scenery_prompt: str = ""
    custom_scenery_uc: list[str] = field(default_factory=list)

    # 2. 인물 배치형 결속 배경 4대 앵커 (Staged Character Environment)
    staged_environment: str = ""    # 공간 환경 바인딩 (e.g. indoors, corporate building lobby)
    staged_anchors: str = ""        # 인물 지지대 & 가구 (e.g. beside speed gate, reception desk in background)
    staged_lighting: str = ""       # 인물 지향 조명 (e.g. soft architectural lighting, subtle rim lighting)
    staged_depth: str = "depth of field, blurred background"  # 피사계 심도 (e.g. depth of field, blurred background)
    custom_staged_uc: list[str] = field(default_factory=list)

    def lint(self) -> list[str]:
        warnings = []

        # 1. 인물 누출 검사 (Pure Scenery 에 인물 태그 혼입 방지)
        scenery_full = f"{self.scenery_architecture}, {self.scenery_props}, {self.scenery_lighting}, {self.scenery_atmosphere}, {self.custom_scenery_prompt}".lower()
        words = set(re.findall(r"\b[a-z0-9_-]+\b", scenery_full))
        leaked = words.intersection(HUMAN_LEAK_KEYWORDS)
        if leaked:
            warnings.append(f"⚠️ [인물 누출] 순수 배경 프롬프트에 인물/인체 관련 단어가 감지되었습니다: {', '.join(sorted(leaked))}")

        # 2. 풍경화 5대 앵커 누락 검사
        if not self.scenery_architecture:
            warnings.append("⚠️ [5대 앵커] 공간 스케일 & 건축(scenery_architecture)이 지정되지 않았습니다.")
        if not self.scenery_lighting:
            warnings.append("⚠️ [5대 앵커] 조명/시간대(scenery_lighting)가 지정되지 않았습니다. (예: volumetric lighting, soft ambient light)")
        if not self.scenery_props:
            warnings.append("⚠️ [5대 앵커] 랜드마크 소품(scenery_props)이 지정되지 않았습니다.")

        # 3. 결속용 배경 앵커 검사
        if not self.staged_environment:
            warnings.append("ℹ️ [인물 결속] staged_environment 가 비어 있어 풍경화 기반으로 자동 유도됩니다.")

        return warnings

    def compose_scenery_prompt(self, include_quality: bool = True) -> str:
        parts = []
        if include_quality and self.quality_prefix:
            parts.append(self.quality_prefix)
        if self.no_humans_lock:
            parts.extend(["no humans", "scenery"])

        for comp in [
            self.scenery_architecture,
            self.scenery_props,
            self.scenery_lighting,
            self.scenery_atmosphere,
            self.scenery_camera,
            self.custom_scenery_prompt,
        ]:
            if comp:
                parts.extend([t.strip() for t in comp.split(",") if t.strip()])

        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for p in parts:
            norm = p.lower().strip()
            if norm and norm not in seen:
                seen.add(norm)
                deduped.append(p.strip())

        return ", ".join(deduped)

    def compose_scenery_uc(self) -> str:
        exclusions = [t.strip() for t in DEFAULT_SCENERY_UC.split(",")]
        if self.custom_scenery_uc:
            exclusions.extend(self.custom_scenery_uc)

        seen = set()
        deduped = []
        for e in exclusions:
            norm = e.lower().strip()
            if norm and norm not in seen:
                seen.add(norm)
                deduped.append(e.strip())

        return ", ".join(deduped)

    def compose_staged_prompt(self) -> str:
        parts = []
        env = self.staged_environment or f"indoors, {self.scenery_architecture}"
        for comp in [
            env,
            self.staged_anchors,
            self.staged_lighting,
            self.staged_depth,
        ]:
            if comp:
                parts.extend([t.strip() for t in comp.split(",") if t.strip()])

        seen = set()
        deduped = []
        for p in parts:
            norm = p.lower().strip()
            if norm and norm not in seen:
                seen.add(norm)
                deduped.append(p.strip())

        return ", ".join(deduped)

    def compose_staged_uc(self) -> str:
        exclusions = [t.strip() for t in DEFAULT_STAGED_UC.split(",")]
        if self.custom_staged_uc:
            exclusions.extend(self.custom_staged_uc)

        seen = set()
        deduped = []
        for e in exclusions:
            norm = e.lower().strip()
            if norm and norm not in seen:
                seen.add(norm)
                deduped.append(e.strip())

        return ", ".join(deduped)


def generate_scene_design_markdown(scenes: list[SceneVisualSpec], project_title: str = "크랙 스토리챗") -> str:
    """Generate official scene-design.md specification document."""
    md = []
    md.append(f"# {project_title} 공식 배경 및 환경 디자인 명세서 (Scene & Environment Specification)\n")
    md.append("본 문서는 스토리챗에 사용되는 **① 풍경화형 단독 배경(Pure Scenery CG)**과 **② 인물 결속용 배경(Staged Environment)**의 프롬프트 및 UC 명세서입니다.\n")
    md.append("---\n")

    # Roster table
    md.append("## 📋 씬 및 장소 로스터 요약\n")
    md.append("| ID | 장소명 | 분류 | 핵심 공간/건축 테마 | 주요 시그니처 소품 |")
    md.append("|:---:|---|---|---|---|")
    for sc in scenes:
        md.append(f"| `{sc.id}` | **{sc.name}** | {sc.category} | {sc.scenery_architecture} | {sc.scenery_props} |")
    md.append("\n---\n")

    # Detailed sections per scene
    for sc in scenes:
        md.append(f"## [{sc.id}] {sc.name}")
        if sc.role:
            md.append(f"> 용도: **{sc.role}**\n")

        md.append("### 1. 🖼️ 풍경화형 단독 배경 (Pure Scenery CG)")
        md.append("무대 전체를 조망하고 공간의 깊이와 분위기를 전달하는 단독 씬 프롬프트입니다.\n")
        md.append("```text")
        md.append(f"[Prompt]\n{sc.compose_scenery_prompt()}\n")
        md.append(f"[UC (네거티브)]\n{sc.compose_scenery_uc()}")
        md.append("```\n")

        md.append("### 2. 👥 인물 배치형 결속 배경 (Staged Character Environment)")
        md.append("캐릭터 포트레이트 및 상황 CG 생성 시 인물 베이스 태그 뒤에 결합되는 환경 프롬프트입니다.\n")
        md.append("```text")
        md.append(f"[Prompt 환경 결속부]\n{sc.compose_staged_prompt()}\n")
        md.append(f"[UC 환경 방어부]\n{sc.compose_staged_uc()}")
        md.append("```")
        md.append("\n---\n")

    return "\n".join(md)


def export_preset_backgrounds_json(
    scenes: list[SceneVisualSpec],
    output_path: Path | None = None,
    name: str = "공식 배경 일러스트 생성 프리셋",
    description: str = "고품질 순수 배경 일러스트 일괄 생성 프리셋 (No humans)"
) -> str:
    """Export NovelAI/WebUI batch preset JSON format (preset-backgrounds.json)."""
    poses = []
    for sc in scenes:
        prompt = sc.compose_scenery_prompt(include_quality=True)
        uc = sc.compose_scenery_uc()
        poses.append({
            "name": sc.name or sc.id,
            "female_directive": prompt,
            "female_extra": "",
            "female_uc": uc,
            "male_directive": prompt,
            "male_extra": "",
            "male_uc": uc,
            "strip_clothing": True,
            "strip_hand_identity": True
        })

    data = {
        "name": name,
        "version": "1.0",
        "description": f"{description} (총 {len(scenes)}종)",
        "poses": poses
    }

    json_text = json.dumps(data, ensure_ascii=False, indent=2)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_text, encoding="utf-8")
        print(f"✅ NovelAI 일괄 생성 프리셋 JSON이 생성되었습니다: {output_path}")
    return json_text


def export_standard_json(scenes: list[SceneVisualSpec], output_path: Path | None = None) -> str:
    """Export standard list JSON: [{"id": "...", "name": "...", "prompt": "...", "uc": "..."}]."""
    data = []
    for sc in scenes:
        data.append({
            "id": sc.id,
            "name": sc.name,
            "category": sc.category,
            "scenery_prompt": sc.compose_scenery_prompt(include_quality=False),
            "scenery_uc": sc.compose_scenery_uc(),
            "staged_prompt": sc.compose_staged_prompt(),
            "staged_uc": sc.compose_staged_uc(),
        })
    json_text = json.dumps(data, ensure_ascii=False, indent=2)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_text, encoding="utf-8")
        print(f"✅ 표준 씬 프롬프트 JSON이 생성되었습니다: {output_path}")
    return json_text


def export_prompts_json_patch(
    scenes: list[SceneVisualSpec],
    output_path: Path,
    base_prompts_json_path: Path | None = None
) -> None:
    """Merge or generate scenes & backgrounds blocks into prompts.json."""
    data: dict[str, Any] = {}
    if base_prompts_json_path and base_prompts_json_path.exists():
        try:
            data = json.loads(base_prompts_json_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}

    scenes_dict = data.setdefault("scenes", {})
    backgrounds_dict = data.setdefault("backgrounds", {})

    seed_base = 220000
    for idx, sc in enumerate(scenes):
        slug = re.sub(r"[^a-zA-Z0-9_-]", "", sc.id.replace("scene/", "").replace("bg", "")).strip() or f"scene-{idx+1:02d}"
        entry = {
            "ko": sc.name,
            "size": [1216, 832],
            "tags": sc.compose_scenery_prompt(include_quality=False).replace("no humans, scenery, ", "").replace("no humans, scenery", "").strip(", "),
            "seed": seed_base + idx
        }
        scenes_dict[slug] = entry

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ prompts.json 에 씬 설정이 반영되었습니다: {output_path}")


def parse_story_md(story_path: Path) -> list[SceneVisualSpec]:
    """Intelligently discover locations and world scenes from story.md."""
    if not story_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {story_path}", file=sys.stderr)
        return []

    text = story_path.read_text(encoding="utf-8")
    specs: list[SceneVisualSpec] = []

    # 1. Standard crack format: #### `loc.xxx` — 장소명 (or #### `장소-xxx` — 장소명)
    loc_sections = re.findall(
        r"^####\s+`?(?:loc\.|장소-|loc-)?([a-zA-Z0-9_-]+)`?\s*—\s*([^\n]+)\n([\s\S]*?)(?=\n#{2,4}\s|\Z)",
        text,
        re.MULTILINE
    )

    for slug, raw_name, body in loc_sections:
        name = raw_name.strip()
        # Extract function/role
        m_func = re.search(r"^[\s*-]+(?:기능|Function)[^\n:]*[:—\-]\s*([^\n]+)", body, re.MULTILINE | re.IGNORECASE)
        role = m_func.group(1).strip() if m_func else ""

        # Extract sensory anchors / props
        m_sens = re.search(r"^[\s*-]+(?:감각\s*앵커|sensory\s*anchors?)[^\n:]*[:—\-]\s*([^\n]+)", body, re.MULTILINE | re.IGNORECASE)
        sensory = m_sens.group(1).strip() if m_sens else ""

        desc_full = f"{role} {sensory}".strip()
        spec_id = f"scene/{slug}" if not slug.startswith("scene/") else slug
        category = "outdoor" if any(w in name for w in ("거리", "길", "광장", "야외", "옥상", "게이트", "공원")) else "indoor"

        specs.append(SceneVisualSpec(
            id=spec_id,
            name=name,
            role=role or "스토리챗 주요 공간 무대",
            category=category,
            scenery_architecture=f"{name}, modern architecture interior" if category == "indoor" else f"{name}, exterior landscape",
            scenery_props=sensory or "empty and quiet atmosphere",
            scenery_lighting="volumetric architectural lighting",
            scenery_atmosphere="atmospheric perspective",
            scenery_camera="wide angle, panoramic view",
            staged_environment=f"indoors, {name}" if category == "indoor" else f"outdoors, {name}",
            staged_anchors=sensory[:60] if sensory else "in background",
            staged_lighting="soft ambient lighting",
            staged_depth="depth of field, blurred background"
        ))

    if specs:
        return specs

    # 2. Fallback: Search for bullet definitions of places if no #### headings found
    generic_places = re.findall(
        r"^[\s*-]+\*\*([가-힣a-zA-Z0-9\s()·_-]+(?:실|홀|룸|방|거리|길|빌딩|사옥|게이트|던전|경기장|라운지|광장|연구실|센터|본부|기숙사)[가-힣a-zA-Z0-9\s()·_-]*)\*\*[:—\-]\s*(.+)$",
        text,
        re.MULTILINE
    )
    for idx, (gname, gdesc) in enumerate(generic_places):
        name = gname.strip()
        category = "outdoor" if any(w in name for w in ("거리", "길", "광장", "야외", "옥상")) else "indoor"
        specs.append(SceneVisualSpec(
            id=f"scene/a{idx+1:02d}",
            name=name,
            role=gdesc[:60].strip() if gdesc else "주요 공간",
            category=category,
            scenery_architecture=f"{name}, interior" if category == "indoor" else f"{name}, exterior landscape",
            scenery_props="empty environment",
            scenery_lighting="volumetric architectural lighting",
            scenery_atmosphere="atmospheric perspective",
            scenery_camera="wide angle, panoramic view",
            staged_environment=f"indoors, {name}" if category == "indoor" else f"outdoors, {name}",
            staged_anchors="in background",
            staged_lighting="soft ambient lighting",
            staged_depth="depth of field, blurred background"
        ))

    return specs


def parse_markdown_table(table_path: Path) -> list[SceneVisualSpec]:
    """Parse scenes from markdown asset tables (e.g. 에셋_배치표.md)."""
    if not table_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {table_path}", file=sys.stderr)
        return []

    text = table_path.read_text(encoding="utf-8")
    specs: list[SceneVisualSpec] = []

    # Match rows like: | **bg01** | 마왕성 로비 (결계 게이트) | `bg01_...png` |
    # or | `scene/a01` | **각성자 관리국 등록홀** | indoor | ... |
    rows = re.findall(r"^\|\s*`?\*?\*?([a-zA-Z0-9_/.-]+)\*?\*?`?\s*\|\s*`?\*?\*?([^|]+?)\*?\*?`?\s*\|\s*([^|\n]+)", text, re.MULTILINE)
    for cid, cname, col3 in rows:
        cid_clean = cid.strip("*` ").lower()
        name_clean = cname.strip("*` ")
        if cid_clean in ("코드", "id", "번호", "---", ":---:", ":---"):
            continue
        if not any(cid_clean.startswith(prefix) for prefix in ("bg", "scene", "a", "s")) and not any(ch in name_clean for ch in ("실", "홀", "룸", "방", "거리", "길", "사옥", "게이트", "던전", "라운지", "광장", "연구실", "본부")):
            continue

        category = "outdoor" if any(w in name_clean for w in ("거리", "길", "광장", "야외", "옥상", "포장마차", "공원")) else "indoor"
        specs.append(SceneVisualSpec(
            id=f"scene/{cid_clean}" if not cid_clean.startswith("scene/") else cid_clean,
            name=name_clean,
            role=f"{name_clean} 배경",
            category=category,
            scenery_architecture=f"{name_clean}, interior" if category == "indoor" else f"{name_clean}, exterior landscape",
            scenery_props="empty environment",
            scenery_lighting="volumetric architectural lighting",
            scenery_atmosphere="atmospheric perspective",
            scenery_camera="wide angle, panoramic view",
            staged_environment=f"indoors, {name_clean}" if category == "indoor" else f"outdoors, {name_clean}",
            staged_anchors="in background",
            staged_lighting="soft ambient lighting",
            staged_depth="depth of field, blurred background"
        ))

    return specs


def parse_json_config(json_path: Path) -> list[SceneVisualSpec]:
    """Parse scenes from an existing preset-backgrounds.json or prompts.json."""
    if not json_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {json_path}", file=sys.stderr)
        return []

    data = json.loads(json_path.read_text(encoding="utf-8"))
    specs: list[SceneVisualSpec] = []

    # Format 1: preset-backgrounds.json with 'poses'
    if "poses" in data and isinstance(data["poses"], list):
        for idx, item in enumerate(data["poses"]):
            name = item.get("name", f"배경_{idx+1}")
            directive = item.get("female_directive", "")
            tags = [t.strip() for t in directive.split(",") if t.strip()]
            # Strip quality & no humans
            clean_tags = [t for t in tags if t not in ("masterpiece", "best quality", "ultra-detailed", "anime visual novel background", "no humans", "scenery")]
            specs.append(SceneVisualSpec(
                id=f"scene/a{idx+1:02d}",
                name=name,
                role="스토리 주요 배경",
                category="indoor" if "indoors" in directive.lower() else "outdoor",
                scenery_architecture=", ".join(clean_tags[:4]) if clean_tags else name,
                scenery_props=", ".join(clean_tags[4:8]) if len(clean_tags) > 4 else "clean empty space",
                scenery_lighting=", ".join(clean_tags[8:10]) if len(clean_tags) > 8 else "ambient lighting",
                scenery_atmosphere="atmospheric haze",
                scenery_camera="wide angle, panoramic view"
            ))
        return specs

    # Format 2: prompts.json with 'scenes'
    if "scenes" in data and isinstance(data["scenes"], dict):
        for idx, (slug, item) in enumerate(data["scenes"].items()):
            name = item.get("ko", slug)
            tags_str = item.get("tags", "")
            specs.append(SceneVisualSpec(
                id=f"scene/{slug}",
                name=name,
                role=f"{name} 배경",
                category="indoor" if "interior" in tags_str.lower() or "room" in tags_str.lower() else "outdoor",
                scenery_architecture=tags_str,
                scenery_props="empty environment",
                scenery_lighting="soft architectural light",
                scenery_atmosphere="atmospheric perspective",
                scenery_camera="wide angle, panoramic view"
            ))
        return specs

    # Format 3: List of scene specs
    if isinstance(data, list):
        for idx, item in enumerate(data):
            specs.append(SceneVisualSpec(
                id=item.get("id", f"scene/a{idx+1:02d}"),
                name=item.get("name", f"배경 {idx+1}"),
                role=item.get("role", ""),
                category=item.get("category", "indoor"),
                scenery_architecture=item.get("architecture", item.get("scenery_architecture", "")),
                scenery_props=item.get("props", item.get("scenery_props", "")),
                scenery_lighting=item.get("lighting", item.get("scenery_lighting", "")),
                scenery_atmosphere=item.get("atmosphere", item.get("scenery_atmosphere", "")),
                scenery_camera=item.get("camera", item.get("scenery_camera", "wide angle, panoramic view")),
                staged_environment=item.get("staged_environment", ""),
                staged_anchors=item.get("staged_anchors", ""),
                staged_lighting=item.get("staged_lighting", ""),
                staged_depth=item.get("staged_depth", "depth of field, blurred background"),
            ))
        return specs

    return specs


def get_demo_scenes() -> list[SceneVisualSpec]:
    """Built-in demo scene specifications for verification & testing."""
    return [
        SceneVisualSpec(
            id="scene/a01",
            name="마왕성 로비 (결계 게이트)",
            role="사옥 1층 로비 및 방문자 보안 결계 게이트 통과 구역",
            category="indoor",
            scenery_architecture="grand corporate building lobby, glass entrance doors, polished marble floor reflecting lights",
            scenery_props="speed gate turnstiles, reception desk, faint blue magical runes glowing on security barrier",
            scenery_lighting="volumetric ceiling architectural lighting, subtle neon edge glow",
            scenery_atmosphere="sterile quiet corporate atmosphere, modern corporate headquarters",
            scenery_camera="wide angle, panoramic view",
            staged_environment="indoors, grand corporate building lobby",
            staged_anchors="beside speed gate turnstile, reception desk in background",
            staged_lighting="overhead cool white light, subtle blue rune backlight",
            staged_depth="depth of field, blurred background"
        ),
        SceneVisualSpec(
            id="scene/a02",
            name="마도개발팀 연금 랩실",
            role="릴리스 책임연구원의 연금술 합성 및 마도 시제품 내구성 검증실",
            category="indoor",
            scenery_architecture="high-tech magic R&D laboratory, brass pipeline conduits, chemical laboratory workbenches",
            scenery_props="glass alembics and retorts, bubbling flasks with glowing purple liquids, arcane circuit boards",
            scenery_lighting="dim ambient purple lighting, volumetric glow from magical reaction tubes",
            scenery_atmosphere="light chemical vapor haze, floating faint magical embers",
            scenery_camera="wide shot, intricate perspective",
            staged_environment="indoors, magic R&D laboratory",
            staged_anchors="leaning against chemical workbench, glowing purple alembic in background",
            staged_lighting="dramatic purple rim lighting from flask, soft desk lamp glow",
            staged_depth="depth of field, blurred background"
        ),
        SceneVisualSpec(
            id="scene/a03",
            name="사옥 옥상 헬리패드 정원",
            role="고위 임원 접견 및 퇴근 후 야경 조망 구역",
            category="outdoor",
            scenery_architecture="corporate skyscraper rooftop terrace, circular helipad markings on concrete deck, safety glass railing",
            scenery_props="rooftop landscaping bushes, windsock pole, perimeter warning beacon lights",
            scenery_lighting="stunning panoramic city night view, glowing skyscrapers, starry night sky, volumetric floodlights",
            scenery_atmosphere="clear night breeze, soft city haze on horizon",
            scenery_camera="wide panoramic establishing shot, high angle",
            staged_environment="outdoors, skyscraper rooftop terrace at night",
            staged_anchors="standing beside safety glass railing, distant city skyline bokeh in background",
            staged_lighting="cool moonlight key lighting, warm city bokeh rim lighting",
            staged_depth="depth of field, blurred background, beautiful night bokeh"
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Run demo compilation and print scene-design.md output")
    parser.add_argument("--parse-story", type=Path, help="Parse location and scene candidates from story.md")
    parser.add_argument("--parse-json", type=Path, help="Parse scene specs from preset-backgrounds.json or config JSON")
    parser.add_argument("--output-md", type=Path, help="Export official scene design markdown (e.g. build/assets/scene-design.md)")
    parser.add_argument("--output-preset", type=Path, help="Export NovelAI/WebUI batch preset JSON (e.g. build/assets/preset-backgrounds.json)")
    parser.add_argument("--output-json", type=Path, help="Export standard JSON list of scene prompts")
    parser.add_argument("--output-prompts-json", type=Path, help="Patch or update scenes into prompts.json")
    parser.add_argument("--title", type=str, default="크랙 스토리챗", help="Project title for markdown export")

    # Single-scene builder arguments
    parser.add_argument("--name", type=str, help="Scene name (e.g. '마왕성 로비')")
    parser.add_argument("--id", type=str, default="scene/a01", help="Scene ID (e.g. 'scene/a01')")
    parser.add_argument("--role", type=str, default="", help="Scene role or usage description")
    parser.add_argument("--category", type=str, default="indoor", help="Category: indoor, outdoor, combat, etc.")
    parser.add_argument("--arch", type=str, default="", help="Architecture/Scale tags")
    parser.add_argument("--props", type=str, default="", help="Landmark props tags")
    parser.add_argument("--lighting", type=str, default="", help="Lighting tags")
    parser.add_argument("--atmo", type=str, default="", help="Atmosphere tags")
    parser.add_argument("--camera", type=str, default="wide angle, panoramic view", help="Camera tags")

    args = parser.parse_args()

    scenes: list[SceneVisualSpec] = []

    if args.demo:
        scenes = get_demo_scenes()
    elif args.parse_story:
        scenes = parse_story_md(args.parse_story)
        print(f"📖 {args.parse_story} 에서 장소 {len(scenes)}곳을 발견했습니다.")
    elif args.parse_json:
        scenes = parse_json_config(args.parse_json)
        print(f"📄 {args.parse_json} 에서 씬 {len(scenes)}개를 로드했습니다.")
    elif args.name:
        scenes = [SceneVisualSpec(
            id=args.id,
            name=args.name,
            role=args.role,
            category=args.category,
            scenery_architecture=args.arch or f"{args.name} interior",
            scenery_props=args.props or "clean space",
            scenery_lighting=args.lighting or "ambient lighting",
            scenery_atmosphere=args.atmo or "atmospheric perspective",
            scenery_camera=args.camera,
            staged_environment=f"indoors, {args.name}" if args.category == "indoor" else f"outdoors, {args.name}",
            staged_anchors="in background",
            staged_lighting="soft ambient lighting",
            staged_depth="depth of field, blurred background"
        )]
    else:
        # Default fallback to demo
        scenes = get_demo_scenes()

    # Lint check for all scenes
    has_lint_warnings = False
    for sc in scenes:
        warnings = sc.lint()
        if warnings:
            has_lint_warnings = True
            print(f"[{sc.id}] {sc.name}:")
            for w in warnings:
                print(f"  {w}")

    # Output exports
    md_content = generate_scene_design_markdown(scenes, args.title)

    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(md_content, encoding="utf-8")
        print(f"✅ 배경 및 환경 디자인 명세서가 생성되었습니다: {args.output_md}")

    if args.output_preset:
        export_preset_backgrounds_json(scenes, args.output_preset, name=f"{args.title} 배경 일러스트 프리셋")

    if args.output_json:
        export_standard_json(scenes, args.output_json)

    if args.output_prompts_json:
        export_prompts_json_patch(scenes, args.output_prompts_json)

    # If no output flags specified, print markdown to stdout
    if not (args.output_md or args.output_preset or args.output_json or args.output_prompts_json):
        print(md_content)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
