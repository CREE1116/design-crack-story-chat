#!/usr/bin/env python3
"""High-Precision Character Appearance Composer, UC Generator, and Character Design Markdown Exporter."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Color keywords for linting
COLOR_KEYWORDS = {
    "white", "black", "grey", "gray", "dark grey", "charcoal", "slate grey",
    "silver", "red", "crimson", "scarlet", "ruby", "maroon", "burgundy",
    "blue", "navy", "navy blue", "dark blue", "light blue", "sky blue", "cyan", "teal", "azure",
    "green", "dark green", "olive", "emerald", "mint", "forest green", "sage",
    "yellow", "gold", "golden", "amber", "blonde", "platinum blonde",
    "brown", "dark brown", "light brown", "chestnut", "auburn", "tan", "beige", "khaki",
    "purple", "violet", "lavender", "indigo", "plum",
    "pink", "rose", "magenta", "orange", "bronze", "copper"
}

DEFAULT_BASE_UC = (
    "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, "
    "fewer digits, cropped, worst quality, low quality, normal quality, "
    "jpeg artifacts, signature, watermark, username, blurry, artist name"
)

# DB search paths
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
class CharacterVisualSpec:
    name: str = ""
    id: str = "01"
    role: str = ""
    gender: str = "1girl"  # 1girl, 1boy
    age_group: str = "young woman, 20s"
    
    # 1. 체형 및 신체 디테일 (Body Form & Physical Details)
    breasts: str = ""        # flat chest, small breasts, medium breasts, large breasts, huge breasts
    musculature: str = ""    # toned, abs, muscular, athletic build, soft body, slender
    body_silhouette: str = "" # slender, skinny, petite, curvy, tall, short, narrow waist, hourglass figure
    body_details: str = ""   # 신체 고유 세부 디테일 (예: thigh gap, thick thighs, wide hips, collarbone, long legs 등)
    
    # 2. 헤어 (Hair) 3요소 필수 결속
    hair_color: str = ""     # dark brown hair, silver hair, etc.
    hair_style: str = ""     # high ponytail, loose strands at nape, blunt bangs, etc.
    hair_length: str = ""    # short hair, medium hair, long hair, very long hair
    
    # 3. 안면, 두상 및 이목구비 (Face, Ears & Facial Features)
    face_shape: str = ""     # round face, sharp chin, pointed chin, defined jawline, chubby cheeks, oval face
    ears: str = ""           # human ears, pointed ears, cat ears, ear piercings
    eye_shape: str = ""      # sharp almond eyes, round gentle eyes, tsurime, tareme, sanpaku, half-closed eyes
    eye_color: str = ""      # dark brown eyes, amber eyes, heterochromia (...)
    eyebrows_lashes: str = "" # thick eyebrows, slender arched eyebrows, long eyelashes
    nose_mouth: str = ""     # straight nose bridge, small nose, thin lips, parted lips
    face_markings: str = ""  # mole under left eye, scar across bridge of nose, freckles on cheeks
    skin_tone: str = ""      # pale skin, fair skin, tanned skin, flushed cheeks
    
    # 4. 제어된 비대칭성 (Controlled Asymmetry)
    asymmetry: str = ""      # single silver hoop earring on left ear, single shoulder guard, etc.
    
    # 5. 의상 부위별 전 파츠 색상 결속 (Outfit by Region)
    outerwear: str = ""      # e.g. navy blue high-collar tactical vest
    top_inner: str = ""      # e.g. white button-up shirt, black compression shirt
    bottom: str = ""         # e.g. dark grey tactical cargo pants
    gloves: str = ""         # e.g. black fingerless leather gloves
    legwear: str = ""        # e.g. dark navy thighhighs, black sheer pantyhose
    footwear: str = ""       # e.g. dark brown combat boots, black leather loafers
    belt_acc: str = ""       # e.g. black leather belt with utility pouches
    
    # 6. 시그니처 소지품 / 모티프
    signature_items: str = "" # e.g. thin rimless glasses held in hand, teal bio-scanner
    
    # 7. 커스텀 제외 태그 (Custom Exclusions)
    custom_uc: list[str] = field(default_factory=list)

    def lint(self) -> list[str]:
        warnings = []
        
        # 1. 체형 검사
        if not self.breasts and self.gender in ("1girl", "female"):
            warnings.append("⚠️ [체형] 가슴 볼륨(breasts)이 지정되지 않았습니다. (예: small breasts, medium breasts, large breasts)")
        if not self.body_silhouette and not self.body_details:
            warnings.append("⚠️ [체형] 골격/실루엣 또는 신체 세부 디테일(body_details)이 지정되지 않았습니다. (예: slender, narrow waist, thigh gap, thick thighs 등)")
            
        # 2. 헤어 3요소 검사
        if not self.hair_color:
            warnings.append("⚠️ [헤어] 헤어 색상(hair_color)이 누락되었습니다. (예: dark brown hair, silver hair)")
        if not self.hair_style:
            warnings.append("⚠️ [헤어] 헤어 스타일(hair_style)이 누락되었습니다. (예: high ponytail, loose strands at nape, messy bangs)")
        if not self.hair_length:
            warnings.append("⚠️ [헤어] 헤어 기장(hair_length)이 누락되었습니다. (예: short hair, medium hair, long hair)")
            
        # 3. 안면/이목구비 검사
        if not self.eye_color:
            warnings.append("⚠️ [안면] 동공 색상(eye_color)이 지정되지 않았습니다. (예: dark brown eyes, amber eyes)")
        if not self.eye_shape:
            warnings.append("⚠️ [안면] 눈매 형태(eye_shape)가 지정되지 않았습니다. (예: sharp almond eyes, round gentle eyes, sanpaku)")
            
        # 4. 의상 색상 결속 검사
        outfit_parts = [
            ("아우터", self.outerwear),
            ("이너/상의", self.top_inner),
            ("하의", self.bottom),
            ("장갑", self.gloves),
            ("양말/스타킹", self.legwear),
            ("신발", self.footwear),
            ("벨트/소지품", self.belt_acc),
        ]
        for part_name, part_val in outfit_parts:
            if not part_val:
                continue
            has_color = any(c in part_val.lower() for c in COLOR_KEYWORDS)
            if not has_color:
                warnings.append(f"⚠️ [의상 색상 고립] '{part_name}'({part_val})에 명시적 색상 단어가 없습니다. (예: black, navy blue, white 등 결속 필요)")
                
        return warnings

    def compose_prompt(self, validator: TagValidator | None = None) -> str:
        tags = []
        
        # 1. 성별 및 연령
        if self.gender:
            tags.append(self.gender)
        if self.age_group:
            tags.append(self.age_group)
            
        # 2. 체형
        for part in [self.body_silhouette, self.musculature, self.breasts, self.body_details]:
            if part:
                tags.extend([t.strip() for t in part.split(",") if t.strip()])
                
        # 3. 헤어 (색상 + 스타일 + 기장 결합)
        for part in [self.hair_color, self.hair_style, self.hair_length]:
            if part:
                tags.extend([t.strip() for t in part.split(",") if t.strip()])
                
        # 4. 안면, 두상 및 이목구비
        for part in [self.face_shape, self.skin_tone, self.ears, self.eye_color, self.eye_shape, self.eyebrows_lashes, self.nose_mouth, self.face_markings]:
            if part:
                tags.extend([t.strip() for t in part.split(",") if t.strip()])
                
        # 5. 비대칭성
        if self.asymmetry:
            tags.extend([t.strip() for t in self.asymmetry.split(",") if t.strip()])
            
        # 6. 의상 파츠
        for part in [self.outerwear, self.top_inner, self.bottom, self.belt_acc, self.gloves, self.legwear, self.footwear]:
            if part:
                tags.extend([t.strip() for t in part.split(",") if t.strip()])
                
        # 7. 시그니처 소지품
        if self.signature_items:
            tags.extend([t.strip() for t in self.signature_items.split(",") if t.strip()])
            
        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for t in tags:
            norm = t.lower()
            if norm not in seen:
                seen.add(norm)
                deduped.append(t)
                
        return ", ".join(deduped)

    def compose_uc(self) -> str:
        """Generate Undesired Content (Negative Prompt) including quality guards and auto-derived character drift exclusions."""
        exclusions = []
        
        # 1. Base quality & anatomy guards
        exclusions.extend([t.strip() for t in DEFAULT_BASE_UC.split(",")])
        
        # 2. Auto-derived character drift exclusions
        # Breast drift
        if any(b in self.breasts.lower() for b in ("small breasts", "flat chest", "medium breasts")):
            exclusions.extend(["large breasts", "huge breasts", "gigantic breasts", "cleavage"])
        elif any(b in self.breasts.lower() for b in ("large breasts", "huge breasts")):
            exclusions.extend(["flat chest", "small breasts"])
            
        # Hair drift
        if "ponytail" in self.hair_style.lower():
            exclusions.extend(["short hair", "loose hair", "twintails", "twin braids"])
        if "short hair" in self.hair_length.lower():
            exclusions.extend(["long hair", "ponytail", "braid"])
            
        # Hair color drift
        if "dark brown" in self.hair_color.lower() or "black" in self.hair_color.lower():
            exclusions.extend(["blonde hair", "pink hair", "blue hair", "green hair", "multi-colored hair"])
            
        # Ear drift
        if "human" in self.ears.lower() or not self.ears:
            exclusions.extend(["animal ears", "cat ears", "dog ears", "fox ears", "pointy ears", "elf ears"])
        elif "pointy" in self.ears.lower() or "elf" in self.ears.lower():
            exclusions.extend(["human ears", "animal ears"])
            
        # Bottom drift (if pants, exclude skirt/dress)
        if any(p in self.bottom.lower() for p in ("pants", "cargo", "jeans", "trousers")):
            exclusions.extend(["skirt", "dress", "shorts"])
        elif "skirt" in self.bottom.lower() or "dress" in self.bottom.lower():
            exclusions.extend(["pants", "cargo pants"])
            
        # Asymmetry drift
        if "single" in self.asymmetry.lower() and "earring" in self.asymmetry.lower():
            exclusions.extend(["earrings", "pair of earrings"])
            
        # Custom exclusions
        if self.custom_uc:
            exclusions.extend(self.custom_uc)
            
        # Deduplicate
        seen = set()
        deduped = []
        for e in exclusions:
            norm = e.lower().strip()
            if norm and norm not in seen:
                seen.add(norm)
                deduped.append(e.strip())
                
        return ", ".join(deduped)


def generate_character_design_markdown(specs: list[CharacterVisualSpec], project_title: str = "크랙 스토리챗") -> str:
    """Generate official character-design.md specification document."""
    md = []
    md.append(f"# {project_title} 공식 캐릭터 비주얼 디자인 명세서 (Character Visual Design Specification)\n")
    md.append("본 문서는 AI 이미지 생성 시 모델, 체크포인트, 시드가 바뀌어도 캐릭터의 외형과 정체성이 100% 동일하게 재현되도록 정의된 **시각적 지문(Visual Fingerprint) 및 공식 프롬프트/UC 명세서**입니다.\n")
    md.append("---\n")
    
    # Roster table
    md.append("## 📋 캐릭터 비주얼 로스터 요약\n")
    md.append("| 번호 | 인물명 | 성별/나이 | 헤어 시그니처 | 핵심 의상 & 배색 | 체형/이목구비 지표 |")
    md.append("|:---:|---|---|---|---|---|")
    for s in specs:
        face_summary = f"{s.eye_shape}, {s.eye_color}"
        md.append(f"| `{s.id}` | **{s.name}** | {s.gender}/{s.age_group} | {s.hair_color}, {s.hair_style} | {s.outerwear or s.top_inner} | {s.body_silhouette}, {face_summary} |")
    md.append("\n---\n")
    
    # Detailed sections per character
    for s in specs:
        md.append(f"## [{s.id}] {s.name}")
        if s.role:
            md.append(f"> 역할: **{s.role}**\n")
            
        md.append("### 1. 시각적 지문 6대 앵커 (Visual Fingerprint)")
        md.append(f"- **👤 체형 & 실루엣**: `{s.body_silhouette}`, `{s.musculature}`, `{s.breasts}`, `{s.body_details}`")
        md.append(f"- **💇 헤어 3요소**: `{s.hair_color}` (색상) + `{s.hair_style}` (형태) + `{s.hair_length}` (기장)")
        md.append(f"- **👁️ 안면, 두상 & 이목구비**:")
        if s.face_shape: md.append(f"  - 얼굴형/턱선: `{s.face_shape}`")
        if s.skin_tone: md.append(f"  - 피부톤/혈색: `{s.skin_tone}`")
        if s.ears: md.append(f"  - 귀 형태: `{s.ears}`")
        if s.eye_shape: md.append(f"  - 눈매 각도: `{s.eye_shape}`")
        if s.eye_color: md.append(f"  - 동공 색상: `{s.eye_color}`")
        if s.eyebrows_lashes: md.append(f"  - 눈썹/속눈썹: `{s.eyebrows_lashes}`")
        if s.nose_mouth: md.append(f"  - 코/입: `{s.nose_mouth}`")
        if s.face_markings: md.append(f"  - 고유 표식(점/흉터): `{s.face_markings}`")
        md.append(f"- **⚖️ 제어된 비대칭성**: `{s.asymmetry}`")
        md.append(f"- **🎨 의상 전 파츠 색상 결속**:")
        if s.outerwear: md.append(f"  - 아우터/조끼: `{s.outerwear}`")
        if s.top_inner: md.append(f"  - 이너/상의: `{s.top_inner}`")
        if s.bottom: md.append(f"  - 하의: `{s.bottom}`")
        if s.gloves: md.append(f"  - 장갑: `{s.gloves}`")
        if s.legwear: md.append(f"  - 양말/스타킹: `{s.legwear}`")
        if s.footwear: md.append(f"  - 신발: `{s.footwear}`")
        if s.belt_acc: md.append(f"  - 벨트/액세서리: `{s.belt_acc}`")
        if s.signature_items:
            md.append(f"- **🎒 시그니처 소지품**: `{s.signature_items}`")
            
        prompt = s.compose_prompt()
        uc = s.compose_uc()
        
        md.append("\n### 2. 컴파일된 불변 베이스 프롬프트 (Prompt)")
        md.append("```text")
        md.append(prompt)
        md.append("```\n")
        
        md.append("### 3. 네거티브 프롬프트 (Undesired Content / UC)")
        md.append("```text")
        md.append(uc)
        md.append("```\n")
        
        md.append("### 4. 불변 유지(Do Not Vary) vs 변형 허용(Safe to Vary)")
        md.append("| 불변 고정 항목 (Do Not Vary) | 표정/상황별 변형 가능 항목 (Safe to Vary) |")
        md.append("|---|---|")
        md.append(f"| 헤어 색상/스타일 (`{s.hair_color}`, `{s.hair_style}`), 안면 표식 (`{s.face_markings}`), 의상 배색 (`{s.outerwear}`) | 표정 (smile, serious, combat focus), 시선 각도 (looking at viewer, looking away), 조명/날씨 |")
        md.append("\n---\n")
        
    return "\n".join(md)


@dataclass
class SceneVisualSpec:
    id: str = "scene/a01"
    name: str = ""
    role: str = ""
    category: str = "indoor"  # indoor, outdoor, combat, urban
    
    # 1. 풍경화형 단독 배경 (Pure Scenery / Landscape CG)
    scenery_architecture: str = ""  # hospital infirmary, modern high-tech medical clinic, interior
    scenery_lighting: str = ""      # volumetric pale blue fluorescent ceiling lighting, monitor glow
    scenery_atmosphere: str = ""    # sterile quiet atmosphere, clean reflections
    scenery_props: str = ""         # rows of empty medical beds with white sheets, glowing green vital monitors, IV drip stands
    scenery_camera: str = "wide angle, panoramic view"
    
    # 2. 인물 배치형 결속 배경 (Staged Character Environment)
    staged_environment: str = ""    # indoors, medical clinic infirmary
    staged_anchors: str = ""        # beside hospital bed, vital monitor glowing in background
    staged_lighting: str = ""       # soft rim lighting from overhead lamps, cool ambient backlight
    staged_depth: str = "depth of field, blurred background"

    def compose_scenery_prompt(self) -> str:
        parts = [
            "no humans",
            "scenery",
            self.scenery_architecture,
            self.scenery_props,
            self.scenery_lighting,
            self.scenery_atmosphere,
            self.scenery_camera,
        ]
        return ", ".join(p.strip() for p in parts if p.strip())

    def compose_scenery_uc(self) -> str:
        return "1girl, 1boy, humans, character, person, lowres, bad anatomy, text, error, blurry, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark"

    def compose_staged_prompt(self) -> str:
        parts = [
            self.staged_environment,
            self.staged_anchors,
            self.staged_lighting,
            self.staged_depth,
        ]
        return ", ".join(p.strip() for p in parts if p.strip())

    def compose_staged_uc(self) -> str:
        return "white background, simple background, flat background, solid color background"


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Run a demo test and print character-design.md output")
    parser.add_argument("--output", type=Path, help="Export output character design markdown file (e.g. build/assets/character-design.md)")
    parser.add_argument("--output-scenes", type=Path, help="Export output scene design markdown file (e.g. build/assets/scene-design.md)")
    args = parser.parse_args()

    # Sample character test data
    spec1 = CharacterVisualSpec(
        name="심가을 (Shim Gae-ul)",
        id="01",
        role="각성자 관리국 등록과 선임 주임",
        gender="1girl",
        age_group="young woman, 24yo",
        breasts="medium breasts",
        musculature="slender build",
        body_silhouette="slender, narrow waist",
        body_details="thigh gap, slim legs",
        hair_color="dark brown hair",
        hair_style="neat low ponytail, parted bangs",
        hair_length="medium hair",
        face_shape="oval face, soft cheeks",
        skin_tone="fair skin",
        ears="human ears",
        eye_shape="intelligent almond eyes",
        eye_color="warm brown eyes",
        eyebrows_lashes="neat slender eyebrows, long eyelashes",
        nose_mouth="small straight nose, gentle smile",
        face_markings="",
        asymmetry="thin silver rimless glasses",
        outerwear="navy blue administrative tailored blazer",
        top_inner="white collared blouse",
        bottom="charcoal pencil skirt",
        gloves="",
        legwear="black sheer pantyhose",
        footwear="black low-heel pumps",
        signature_items="digital tablet clipboard in hand"
    )
    
    spec2 = CharacterVisualSpec(
        name="하무진 (Ha Mu-jin)",
        id="02",
        role="발할라 길드 마스터 · 1급 각성자",
        gender="1boy",
        age_group="mature male, 35yo",
        breasts="",
        musculature="heavily muscular, broad shoulders, massive abs",
        body_silhouette="tall, towering build",
        body_details="thick legs, prominent collarbone",
        hair_color="black hair",
        hair_style="undercut, slicked back, short beard",
        hair_length="short hair",
        face_shape="defined angular jawline, strong square chin",
        skin_tone="tanned weathered skin",
        ears="human ears",
        eye_shape="sharp menacing gaze, deep-set eyes",
        eye_color="golden amber eyes",
        eyebrows_lashes="thick furrowed eyebrows",
        nose_mouth="straight prominent nose bridge, firm set mouth",
        face_markings="cross-shaped scar on right cheek",
        asymmetry="heavy steel pauldron on right shoulder only",
        outerwear="dark crimson sleeveless leather duster coat",
        top_inner="black torn combat tank top",
        bottom="charcoal combat pants with reinforced knee pads",
        gloves="dark brown fingerless reinforced brawler gloves",
        footwear="heavy black combat boots with steel plates",
        signature_items="glowing orange heavy greatsword slung on back"
    )

    # Sample scene test data
    scene1 = SceneVisualSpec(
        id="scene/a01",
        name="각성자 관리국 등록홀",
        role="헌터 등록 및 등급 측정 대기 로비",
        category="indoor",
        scenery_architecture="modern government administration hall, sleek glass and marble interior, wide lobby",
        scenery_lighting="bright cool white ceiling panel lighting, holographic terminal glow",
        scenery_atmosphere="formal clean atmosphere, bustling administrative area",
        scenery_props="reception desks, holographic status boards, rows of waiting chairs, security gates",
        scenery_camera="wide angle, panoramic interior view",
        staged_environment="indoors, administration hall lobby",
        staged_anchors="beside reception desk, holographic directory screen in background",
        staged_lighting="clean overhead lighting, subtle screen backlight",
        staged_depth="depth of field, blurred background"
    )

    scene2 = SceneVisualSpec(
        id="scene/a02",
        name="발할라 길드 훈련장",
        role="길드 지하 실전 대련 및 각성자 전투 평가장",
        category="combat",
        scenery_architecture="massive underground combat arena, reinforced steel barricades, scorched stone flooring",
        scenery_lighting="harsh overhead industrial floodlights, high contrast dramatic shadows",
        scenery_atmosphere="floating dust particles, smoky haze",
        scenery_props="holographic target projectors, heavy weapon racks, blast marks",
        scenery_camera="wide shot, grand scale, atmospheric perspective",
        staged_environment="indoors, combat training arena",
        staged_anchors="scorched stone floor, steel barricade in background",
        staged_lighting="dramatic harsh key lighting, floating sparks",
        staged_depth="depth of field, blurred background"
    )

    doc_char = generate_character_design_markdown([spec1, spec2], "『각성의 밤』")
    doc_scene = generate_scene_design_markdown([scene1, scene2], "『각성의 밤』")
    
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(doc_char, encoding="utf-8")
        print(f"✅ 캐릭터 비주얼 디자인 문서가 생성되었습니다: {args.output}")

    if args.output_scenes:
        args.output_scenes.parent.mkdir(parents=True, exist_ok=True)
        args.output_scenes.write_text(doc_scene, encoding="utf-8")
        print(f"✅ 배경 비주얼 디자인 문서가 생성되었습니다: {args.output_scenes}")

    if not args.output and not args.output_scenes:
        print(doc_char)
        print("\n" + "=" * 80 + "\n")
        print(doc_scene)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

