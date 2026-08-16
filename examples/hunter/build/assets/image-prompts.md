# 이미지 생성 프롬프트 — 헌터 스토리챗

단보루 태그 방식(Illustrious / NoobAI / Pony 계열 기준). ComfyUI는 프론트엔드라 문법은 체크포인트가 정하므로, 자연어 모델을 쓸 경우 맨 아래 변환 노트를 참고.

에셋 경로 `{IMG}/인물/상황.png`와 `{IMG}/scene/장면.png`에 정확히 대응한다. 파일명은 이 문서의 슬러그를 그대로 쓴다.

## 조립 방식

```
[품질 프리픽스] + [캐릭터 베이스] + [상황 모디파이어] + [공통 서픽스]
```

캐릭터 베이스는 절대 바꾸지 않는다. 상황마다 바뀌는 건 표정·자세·구도·조명뿐이다. 베이스를 흔들면 같은 인물로 안 보인다.

시드는 캐릭터별로 고정해두고 상황만 바꿔 돌리면 동일성이 크게 올라간다. 얼굴이 계속 흔들리면 캐릭터별 LoRA를 하나 뽑아 쓰는 게 결국 빠르다.

### 공통 그림체

96장이 한 작품처럼 보이게 만드는 건 캐릭터 태그가 아니라 이 블록이다. 모든 이미지에 똑같이 들어가고, 여기만 갈아끼우면 전체 화풍이 한 번에 바뀐다. `prompts.json`의 `config.style_preset` 으로 고른다.

**webtoon (기본)** — 한국 웹툰체
```
korean webtoon style, clean lineart, cel shading with soft gradients,
muted desaturated palette with one accent color, modern urban fantasy,
cinematic lighting, detailed face, detailed eyes, sharp focus
```
네거티브 추가: `sketch, unfinished, rough lines`

**anime** — 애니메이션풍
```
anime screencap style, crisp cel shading, vivid but controlled colors,
modern urban fantasy, dramatic key lighting, detailed face, detailed eyes
```
네거티브 추가: `realistic, 3d render`

**semireal** — 반실사
```
semi realistic illustration, painterly rendering, subtle skin texture,
muted cinematic color grading, modern urban fantasy, volumetric lighting,
detailed face, detailed eyes
```
네거티브 추가: `flat colors, cel shading, cartoon`

`muted desaturated palette with one accent color` 가 webtoon 프리셋의 핵심이다. 채도를 눌러 두면 대사창 옆에 반복 노출돼도 눈이 안 피로하고, 액센트 하나만 살아서 인물 구분이 쉬워진다.

### 품질 프리픽스

```
masterpiece, best quality, amazing quality, very aesthetic, absurdres, highly detailed
```

Pony 계열이면 맨 앞에 `score_9, score_8_up, score_7_up,` 를 붙인다. 없으면 품질이 크게 떨어진다.

### 공통 서픽스

```
solo, looking at viewer, simple background, dark grey background, subtle vignette
```

배경을 단색으로 고정하는 이유는 대사창 옆에 반복 노출되기 때문이다. 배경이 매번 달라지면 시선이 그쪽으로 끌린다. 장면 이미지만 배경을 살린다.

### 공통 네거티브

```
worst quality, low quality, normal quality, lowres, jpeg artifacts, blurry,
bad anatomy, bad hands, missing fingers, extra digits, fewer digits, extra limbs,
watermark, signature, artist name, text, speech bubble, logo,
multiple views, multiple girls, multiple boys, 2girls, 2boys,
child, loli, shota,
western comic style, 3d, photorealistic
```

`multiple views` 계열을 빼면 시트 형태로 여러 컷이 한 장에 나오는 경우가 잦다.

## 상황 모디파이어 6종

구도를 상황별로 다르게 잡는 선택이라, 같은 인물이라도 화면 안 크기가 달라진다. 대사창 옆에 붙일 때는 출력 후 동일 비율로 크롭하거나, 세로 기준선(눈높이)을 맞춰 리사이즈하면 튀는 느낌이 줄어든다.

### `normal` — 평상

```
upper body, relaxed posture, calm expression, neutral gaze, soft even lighting,
standing naturally, arms relaxed
```

### `serious` — 경계·진지

```
upper body, slight low angle, narrowed eyes, tense jaw, serious expression,
alert posture, head slightly turned, hard directional lighting, cool color grading
```

### `combat` — 전투

```
full body, dynamic action pose, mid-motion, foreshortening, intense expression,
gritted teeth, hair and clothes in motion, motion blur accents,
dramatic rim lighting, high contrast, debris in air
```

### `hurt` — 부상·소진

```
medium close-up, low angle from below eye level, leaning against wall or kneeling,
labored breathing, sweat, dirt smudges, torn clothing, pained expression,
half-lidded eyes, dim desaturated lighting
```

### `soft` — 신뢰·이완

```
bust shot, close framing, gentle expression, slight smile, softened eyes,
relaxed shoulders, warm soft lighting, shallow depth of field, warm color grading
```

### `guard` — 적대·거리두기

```
upper body, slightly turned away, cold stare, closed-off body language,
arms crossed or hands in pockets, chin lowered, harsh side lighting,
deep shadows, desaturated cool tones
```

## 캐릭터 베이스 15종

머리색·눈색은 원본에 없던 값이라 이번에 확정했다. 바꾸고 싶으면 이 문서와 `characters.md`를 같이 고친다.

### `shim-gaeul` — 심가을 (44, 여, 협회 부협회장)

**식별 포인트** — 목에 건 계측 단말. 늘 켜져 있어 걸을 때마다 흔들리며 미약하게 빛난다.

```
1girl, mature female, 40s, glowing measurement device on neck strap, short
black hair with grey streaks, dark brown eyes, tired eyes with dark circles,
sharp alert gaze, old scars on hands and wrists, dark grey field jacket,
association badge, measuring terminal hanging from neck, practical utilitarian
clothing, no makeup, weathered competent look
```

### `ju-habin` — 주하빈 (24, 여, 협회 필드 의무관)

**식별 포인트** — 손끝과 손목이 늘 물기에 젖은 듯 반들거린다. 표면장력 조작의 흔적이다.

```
1girl, young woman, early 20s, wet glistening fingertips and wrists, dark
brown hair in high ponytail, loose strands at nape, brown eyes, small slender
build, white and light blue medical field vest, multiple equipment pouches,
short trimmed nails, faint wet sheen on fingertips, kind eyes, medic
```

### `no-younghoon` — 노영훈 (52, 남, 협회장)

**식별 포인트** — 단말기 대신 늘 손에 든 종이 문서 뭉치. 말은 흩어져도 기록은 남는다는 신념.

```
1boy, mature male, 50s, holding thick stack of paper documents, short greying
hair, dark eyes, upright posture, navy formal suit, tie fastened to the
collar, association pin on left lapel, minimal facial expression, composed
bureaucrat
```

### `ban-hosik` — 반호식 (39, 남, 발할라 길드장 S급)

**식별 포인트** — 드러난 팔뚝과 목덜미를 덮은 겹친 흉터. 받아 저장한 타격이 몸에 남긴 이력이다.

```
1boy, huge muscular male, 30s, dense overlapping old scars on bare forearms
and neck, very broad shoulders, buzz cut black hair, dark brown eyes, deep set
eyes, crooked nose bridge from old fracture, layered old scars on forearms and
neck, rolled up sleeves, plain training gi top, martial artist, imposing quiet
presence
```

### `kang-yeojin` — 강여진 (33, 여, 발할라 부길장 A급)

**식별 포인트** — 손목과 발목에 늘 감긴 테이핑. 가속 반동에 관절이 먼저 나간다.

```
1girl, athletic female, 30s, athletic tape wrapped around wrists and ankles,
very short black hair above nape, sharp dark eyes, thin scar across left
eyebrow, flat unreadable expression, black functional combat suit, no
decoration, lean toned build
```

### `do-jaehyeon` — 도재현 (27, 남, 발할라 길드원 B급)

**식별 포인트** — 안경과 늘 짊어진 긴 봉. 명부에서 안경을 쓴 유일한 인물이다.

```
1boy, tall slender male, 20s, thin round glasses, carrying long staff on back,
messy dark brown hair, brown eyes, thin framed glasses, long fingers, awkward
calluses on hands, athletic tracksuit, holding a long metal staff, thoughtful
reserved expression
```

### `yun-seola` — 윤설아 (38, 여, 아발론 길드장 S급)

**식별 포인트** — 오른쪽 눈만 홍채가 옅다. 간파를 오래 써서 색소가 빠졌다.

```
1girl, elegant female, 30s, heterochromia with pale washed-out right iris,
long black hair in low ponytail, dark eyes, impeccably neat, tailored
monochrome suit, muted colors, thin glasses held in hand, calm measured
expression, observant gaze
```

### `cha-gyeongyun` — 차경윤 (33, 여, 아발론 부길장 A급)

**식별 포인트** — 왼 손목에 겹쳐 찬 단말기 두 개. 논문과 필드를 동시에 굴리는 사람의 장비다.

```
1girl, sharp-eyed female, 30s, two stacked smart terminals on left wrist, grey
eyes, sharp narrow eyes, visible fatigue, dress shirt with sleeves rolled up,
no tie, two wrist terminals stacked on one arm, restless impatient bearing,
workaholic
```

### `seo-dain` — 서다인 (23, 여, 아발론 길드원 B급)

**식별 포인트** — 손등을 덮는 소매와 늘 품에 안은 두꺼운 노트. 여백까지 빼곡하다.

```
1girl, petite young woman, early 20s, oversized sleeves covering hands,
clutching thick notebook, light brown hair, blunt bangs covering eyebrows,
brown eyes, hunched posture, oversized sweater with sleeves covering hands,
holding a densely filled notebook, ink stains on fingers, timid nervous
expression
```

### `ha-mujin` — 하무진 (37, 남, 에덴 길드장 S급)

**식별 포인트** — 감정이 올라오면 세로로 좁아지는 동공, 목덜미를 따라 난 짧은 줄무늬 털.

```
1boy, tall broad male, 30s, vertical slit pupils, short striped fur along
nape, long dark hair tied loosely, pale amber eyes, thick short nails, loose
simple clothing, animal ears, tiger beastman, silent predatory stillness
```

### `jin-seori` — 진서리 (28, 여, 에덴 부길장 A급)

**식별 포인트** — 살짝 뾰족한 귀와 웃을 때 보이는 송곳니. 늑대형 수인화의 상시 흔적.

```
1girl, lithe female, late 20s, slightly pointed ears, visible canine fangs,
silver grey hair tucked behind ears, yellow eyes, slightly pointed wolf ears,
visible canine teeth, neat fitted jacket over practical clothes, alert tilted
head, wolf beastman
```

### `cha-noeul` — 차노을 (20, 여, 에덴 길드원 B급)

**식별 포인트** — 감정에 따라 색이 번졌다 가라앉는 머리카락. 불안정 수인화가 겉으로 새는 자리다.

```
1girl, petite teenager-looking woman, 20s, hair colour bleeding between
shades, small slight build, light brown hair with uneven fading streaks, amber
eyes, oversized hoodie covering arms, short fur patches at fingertips and
nape, unstable transformation, anxious darting eyes, beastman
```

### `baek-haram` — 백하람 (34, 여, 바벨 길드장 S급)

**식별 포인트** — 움직임 끝에 한 겹 늦게 따라붙는 잔상. 주변 시간이 미세하게 어긋나 있다.

```
1girl, thin languid female, 30s, doubled afterimage outline, motion echo,
messy long black hair grown out, dark grey half-lidded eyes, drowsy detached
expression, thin long coat unsuited to the season, bare wrists, no watch,
understated ominous presence
```

### `no-ganghyeon` — 노강현 (31, 남, 바벨 부길장 A급)

**식별 포인트** — 목에 겹쳐 건 대여섯 개의 출입증·명찰. 창구를 혼자 다 맡은 사람의 표식.

```
1boy, ordinary-looking male, 30s, six overlapping ID badges on neck lanyards,
neat black hair, dark eyes, plain unremarkable clothing, shoulder bag, mild
pleasant expression, quick observant eyes, calm mediator bearing
```

### `myeong-seogyeong` — 명서경 (26, 여, 바벨 길드원 B급)

**식별 포인트** — 열 손가락 마디마다 낀 얇은 금속 밴드. 등가교환의 접촉 매개다.

```
1girl, guarded female, 20s, thin metal bands on every finger joint, dark eyes,
layered monochrome clothing, rough worn hands, short cut nails, fiddling with
a coin between fingers, flat expression, eyes that do not smile, appraising
sidelong glance
```

## 배경판 6종

채팅 배경으로 까는 용도라 장면 이미지와 요구사항이 다르다. **중앙이 비고 저대비여야** 위에 얹히는 텍스트가 읽힌다. 초점 대상을 두지 않고 가로로 길게(1536×640) 뽑는다. 경로는 `{IMG}/bg/<이름>.png`.

서픽스
```
no humans, empty establishing shot, wide angle, background plate,
low contrast, muted desaturated tones, uncluttered composition,
negative space in the center, soft depth of field, no focal subject
```
네거티브 추가: `1girl, 1boy, person, human, face, portrait, text, busy composition, high contrast, harsh highlights`

### `bg/city-day` — 서울 주간
```
seoul cityscape by day, mid rise buildings, overcast sky,
a faint dimensional rift visible far in the distance, hazy atmospheric depth
```

### `bg/city-night` — 서울 야경
```
seoul cityscape at night, scattered window lights, wet asphalt reflections,
distant rift glow on the horizon, deep blue tones
```

### `bg/hq-wide` — 협회 본부
```
wide interior of a modern government building atrium, high ceiling,
glass partitions, empty corridor, cold institutional lighting
```

### `bg/gate-far` — 게이트 원경
```
dimensional rift seen from far outside a cordon, floodlights and barriers
in the mid ground, empty sealed street, overcast dusk
```

### `bg/dungeon` — 던전 내부
```
interior of an otherworldly dungeon, irregular stone and crystalline growth,
faint ambient mana glow from the walls, long empty corridor receding into darkness
```

### `bg/aftermath` — 범람 후
```
damaged city street after an incident, overturned barriers, scattered debris,
thin smoke, emergency lights in the distance, grey overcast
```

`bg/dungeon` 은 공략 아크가 시작되면 필요한데 지금까지 게이트 내부 그림이 하나도 없었다. 헌터의 본업이 공략인데 정작 그 안을 보여줄 게 없던 상태다.

배경판과 장면 이미지는 용도가 갈린다. 장면(`scene/`)은 본문 맨 앞에 붙여 "여기가 어디인지" 보여주는 삽화고, 배경판(`bg/`)은 글자가 위에 얹히는 판이다. 같은 장소라도 따로 뽑는 게 맞다.

## 장면 6종

장면은 인물 없이 배경만 뽑는다. 네거티브에 `1girl, 1boy, person, human` 을 추가하고, 공통 서픽스의 `solo, looking at viewer, simple background` 는 뺀다.

### `scene/hq-lobby` — 협회 본부 등록층

```
no humans, modern government building interior, wide registration floor,
numbered ticket display board, queue barriers, reception counters,
fluorescent lighting, pale institutional color palette,
glass partition wall in background, worn but clean, near future korea
```

### `scene/hq-exterior` — 본부 외부

```
no humans, modern korean city street, large government building facade,
seoul gangnam district, morning light, spring, subway exit in foreground,
wide establishing shot, overcast sky with breaks of sun
```

### `scene/measure-room` — 측정실

```
no humans, small clinical measurement room, large cylindrical scanning apparatus,
cables and monitors, calibration markings on floor, cold blue instrument glow,
sterile white walls, single chair at center
```

### `scene/guild-booths` — 길드 상담 부스

```
no humans, four consultation booths in a row behind glass,
dark red booth, navy blue booth, deep green booth, one unpainted plain booth,
corporate recruitment atmosphere, banner stands, indirect lighting,
shallow depth of field
```

### `scene/gate-site` — 게이트 통제선

```
no humans, dimensional rift hovering above ground, cordon tape and barriers,
measuring equipment on tripods, warning lights, urban street sealed off,
faint distortion around the rift, tense quiet atmosphere, overcast
```

### `scene/overflow` — 범람 현장

```
no humans, dimensional rift violently unstable, cracks spreading in air,
overturned barriers, emergency lights, smoke and dust, debris,
red warning glow, chaotic aftermath, damaged street, dramatic high contrast
```

## 범람체 6종

인물 없이 뽑는다. 네거티브에 `1girl, 1boy, person, human face, cute, chibi` 를 추가하고 서픽스는 `no humans, creature concept art, dark urban background, dramatic rim lighting` 을 쓴다. 경로는 `{IMG}/mob/<유형>.png`.

### `mob/swarm` — 군체
```
swarm of small dark creatures, dozens of them, low crouching bodies, glowing pale eyes,
spilling through a narrow gap, chitinous limbs, faint mana glow, motion blur, overwhelming numbers
```

### `mob/beast` — 수형
```
large quadruped monster, beast form, lean muscular body, elongated skull, no visible eyes,
charging forward, foreshortening, dark hide with faint glowing seams
```

### `mob/shell` — 갑각
```
heavily armored monster, thick segmented carapace, slow hulking posture, plated shoulders,
narrow joint gaps glowing faintly, imposing bulk
```

### `mob/drift` — 부유
```
floating airborne creature, hovering above the ground, trailing membranes, no legs,
faint gravitational distortion beneath it, drifting silently, backlit
```

### `mob/mimic` — 의태
```
humanoid silhouette that is subtly wrong, proportions slightly off, blank featureless face
partially formed, standing still among ordinary objects, unsettling stillness, uncanny
```

### `mob/core` — 핵
```
massive core entity, dense concentration of mana given form, multiple asymmetric limbs,
glowing central mass, reality distorting around it, overwhelming scale, apex threat
```

의태는 "사람인데 뭔가 어긋난" 인상이 핵심이라 얼굴을 완성하지 않는 쪽이 낫다. 완성된 얼굴이 나오면 그냥 사람으로 읽혀서 유형의 의미가 사라진다.

## 모델별 조정

**Illustrious / NoobAI** — 위 태그를 그대로 쓴다. 품질 태그는 `masterpiece, best quality` 정도면 충분하고 과하게 쌓으면 오히려 뭉갠다.

**Pony V6** — 공통 프리픽스 맨 앞에 `score_9, score_8_up, score_7_up,` 필수. 없으면 품질이 크게 떨어진다.

**SDXL / Flux** — 태그를 자연어 문장으로 풀어야 한다. 예:

```
A tired woman in her forties with short black hair streaked with grey and dark
circles under her sharp eyes, wearing a dark grey field jacket with a measuring
terminal hanging from her neck, old scars visible on her hands. Upper body shot,
tense alert posture, hard directional lighting, cool tones, plain dark background.
Korean webtoon illustration style.
```

Flux는 네거티브 프롬프트를 쓰지 않으므로 원하지 않는 요소는 긍정 프롬프트에서 아예 언급하지 않는 쪽으로 처리한다.

## 남은 결정

- 머리색·눈색은 전부 이번에 새로 정한 값이다. 원본 `characters.md`에는 색 지정이 없었다.
- 하무진·진서리·차노을의 수인 표현 강도. 지금은 귀와 눈동자 정도의 약한 표현인데, 더 짐승에 가깝게 갈지는 화풍 취향 문제다.
- 90개 조합을 다 만들 필요는 없다. `normal`·`serious`만 먼저 뽑아도 대부분의 장면이 커버되고, 프롬프트 규칙이 없는 조합은 이미지 없이 출력하도록 이미 되어 있다.
