# Stable Diffusion 일괄 생성

`prompts.json`의 캐릭터 15명 × 상황 6종 + 장면·배경·범람체 각 6종 = **108장**을 조합해 생성하고, 결과를 `out/<인물>/<상황>.png`로 저장한다. 이 경로가 그대로 스토리챗의 `{IMG}/인물/상황.png` 에셋 구조다.

**A1111/Forge WebUI와 ComfyUI를 모두 지원한다.** `config.backend` 로 고르고, 프롬프트 데이터(`prompts.json`)는 양쪽이 공유한다. 백엔드를 바꿔도 캐릭터·상황·시드 정의는 그대로다.

GUI 대신 스크립트를 쓰는 이유는 조합 수와 파일명 때문이다. 108장을 손으로 돌릴 수 없고, 결과가 `out/<인물>/<상황>.png` 로 정확히 떨어져야 스토리챗의 `{IMG}/인물/상황.png` 에셋 경로와 맞는다.

## 준비 — A1111 WebUI (기본)

**WebUI를 `--api` 플래그와 함께 켜야 한다.** 없으면 연결이 안 된다.

```bash
./webui.sh --api                 # 리눅스·맥
```
윈도우는 `webui-user.bat` 의 `COMMANDLINE_ARGS` 에 `--api` 를 넣는다.

```json
"config": {
  "backend": "a1111",
  "server": "127.0.0.1:7860",
  "checkpoint": "illustriousXL_v01.safetensors",
  "quality_preset": "illustrious",
  "style_preset": "webtoon",
  "steps": 28, "cfg": 5.0,
  "sampler": "Euler a", "scheduler": "Automatic",
  "loras": [],
  "output_dir": "out"
}
```

- `checkpoint` 는 파일명 그대로 적으면 된다. WebUI 내부 표기는 `파일명.safetensors [해시]` 인데 스크립트가 알아서 맞춰 보낸다.
- 샘플러 이름이 ComfyUI와 다르다(`Euler a` vs `euler_ancestral`). `--list-models` 로 확인하는 게 확실하다.
- LoRA는 WebUI 문법대로 프롬프트에 `<lora:이름:강도>` 로 자동 삽입된다. 설정은 동일하게 `loras` 배열에 적으면 된다.

## ComfyUI로 쓰려면

```bash
python batch.py --backend comfy      # 이번 실행만
```
`config.backend` 를 `"comfy"` 로 바꾸면 기본값이 된다. 백엔드를 `--backend` 로 넘기면 샘플러·포트도 `backend_defaults` 값으로 같이 전환된다.

- `quality_preset` 은 `illustrious` / `pony` / `plain`. Pony 계열은 `score_9` 계열 태그가 없으면 품질이 크게 떨어져서 프리셋으로 분리해 뒀다.
- `style_preset` 은 `webtoon` / `anime` / `semireal`. 전체 화풍이 이걸로 갈린다.

## 실행

```bash
python batch.py --dry-run          # 서버 없이 조합·프롬프트만 확인
python batch.py                    # 전체 108장, 이미 있는 파일은 건너뜀
python batch.py --only ju-habin,shim-gaeul
python batch.py --situations normal,serious
python batch.py --scenes-only      # 장면 6종만
python batch.py --backgrounds-only # 배경판 6종만
python batch.py --monsters-only    # 범람체 6종만
python batch.py --dataset ju-habin # LoRA 학습셋
python batch.py --style semireal   # 그림체 전환
python batch.py --force            # 덮어쓰기
```

출력 구조

```
out/<인물>/<상황>.png     캐릭터 15 × 상황 6 = 90장
out/scene/<장면>.png      장면 6장 — 본문 맨 앞 삽화용
out/bg/<이름>.png         배경판 6장 — 글자가 얹히는 판, 저대비 와이드
out/mob/<유형>.png        범람체 6장
out/_dataset/<인물>/      LoRA 학습셋 (기본 24장)
```

한 장 실패해도 전체가 멈추지 않고, 마지막에 성공·실패 개수를 보고한다. 이미 있는 파일은 기본으로 건너뛰므로 중단 후 다시 돌리면 이어서 진행된다.

**먼저 `--dry-run`으로 확인하고, `--only`로 한 명만 뽑아 화풍을 맞춘 다음 전체를 돌리는 순서를 권한다.** 96장을 바로 돌려놓고 나중에 마음에 안 들면 전부 다시 뽑아야 한다.

## LoRA

전역 LoRA는 `config.loras`, 캐릭터 전용은 각 캐릭터의 `loras`에 넣는다. 둘 다 있으면 전역 → 캐릭터 순으로 체인된다.

```json
"config": { "loras": [{"name": "webtoon_style.safetensors", "model": 0.7, "clip": 0.7}] },
"characters": {
  "ju-habin": { "loras": [{"name": "juhabin_v1.safetensors", "model": 0.8, "clip": 0.8}] }
}
```

`model`/`clip`을 생략하면 1.0이다.

## 캐릭터 LoRA 워크플로

프롬프트만으로는 같은 얼굴이 계속 안 나온다. 결국 캐릭터당 LoRA를 뽑는 게 가장 빠르고, 스크립트가 그 과정을 지원한다.

```bash
# 1. 화풍 먼저 맞춘다
python batch.py --only ju-habin --situations normal
#    마음에 들 때까지 --style / --checkpoint / --force 로 반복

# 2. 학습셋을 뽑는다 (기본 24장)
python batch.py --dataset ju-habin
python batch.py --dataset ju-habin --count 40      # 더 필요하면

# 3. out/_dataset/ju-habin/ 에서 잘 나온 15~25장을 고른다
#    얼굴이 흔들린 것, 손이 망가진 것은 버린다

# 4. 고른 걸로 LoRA를 학습시킨다 (kohya_ss 등, 이 스크립트 밖)

# 5. prompts.json 에 등록
#    "ju-habin": { "loras": [{"name": "juhabin_v1.safetensors", "model": 0.8}] }

# 6. 그 캐릭터의 6상황을 다시 뽑는다
python batch.py --only ju-habin --force
```

학습셋은 캐릭터 베이스 태그를 **고정한 채** 각도·표정·조명·프레이밍만 흔든다(`dataset_variations` 12종을 순환). 시드도 장마다 다르다. 얼굴은 같고 구도만 다른 세트가 나와야 LoRA가 인물을 배우지 특정 포즈를 배우지 않는다.

변주 목록이 마음에 안 들면 `prompts.json`의 `dataset_variations` 를 직접 고친다. 장수가 변주 수보다 많으면 순환하면서 시드만 달라진다.

## 시드

캐릭터마다 고정 시드를 두고 상황별로 인덱스만 더한다(`110001 + 상황 순번`). 같은 인물이 상황만 바뀔 때 얼굴이 덜 흔들리고, 특정 조합만 다시 뽑아도 이전과 같은 그림이 나온다. 시드를 바꾸고 싶으면 `characters.<슬러그>.seed`를 고친다.

## 해상도

상황별로 구도가 달라서 해상도도 다르게 잡았다. `combat`은 전신이라 세로로 길고, `soft`는 버스트라 정사각, 장면은 가로다. 대사창 옆에 붙일 때 크기가 튀는 게 싫으면 생성 후 눈높이 기준으로 리사이즈하거나, `situations.*.size`를 전부 같은 값으로 통일하면 된다.

## 자산 확인과 검증

이름을 손으로 맞출 필요 없이 서버에서 직접 읽어온다.

```bash
python batch.py --list-models    # 설치된 체크포인트·LoRA·샘플러·스케줄러 전부
python batch.py --check          # 지금 설정으로 돌릴 수 있는지만 검사
```

`--check`는 이번 실행에 필요한 체크포인트와 LoRA가 서버에 실제로 있는지, 샘플러·스케줄러 이름이 맞는지 확인하고, 틀렸으면 **가까운 이름을 제안**한다. 오타 하나로 96장을 날리는 걸 막는 단계이므로 본 실행 전에 한 번 돌리는 게 좋다. 본 실행도 시작 전에 같은 검사를 자동으로 하고, 문제가 있으면 아무것도 생성하지 않고 멈춘다.

## 일회성 덮어쓰기

`prompts.json`을 고치지 않고 이번 실행에만 다른 값을 쓸 수 있다.

```bash
python batch.py --checkpoint ponyDiffusionV6XL.safetensors --preset pony
python batch.py --lora webtoon_style.safetensors:0.7 --lora juhabin_v1.safetensors:0.8:0.9
python batch.py --steps 32 --cfg 6.0 --sampler dpmpp_2m --scheduler karras
python batch.py --server 192.168.0.10:8188 --out /mnt/assets
```

`--lora`는 `이름[:model[:clip]]` 형식이고 여러 번 쓸 수 있다. `clip`을 생략하면 `model`과 같은 값이 된다.

캐릭터별로 다른 체크포인트를 쓰려면 `characters.<슬러그>.checkpoint`를 넣으면 된다. 없으면 전역 설정을 쓴다.

## 검증 상태

백엔드마다 모의 서버가 있다. GPU 없이 전 경로를 확인할 수 있고, 없는 체크포인트·LoRA·샘플러를 쓰면 실제 서버처럼 404/400을 돌려준다.

```bash
python mock_a1111.py &     # 7860 — A1111 경로
python mock_server.py &    # 8188 — ComfyUI 경로

python batch.py --list-models
python batch.py --check
python batch.py --only ju-habin --situations normal --no-scenes --no-monsters --no-backgrounds
```

두 모의 서버로 확인한 것: 자산 목록 읽기, 오타 시 유사 이름 제안, LoRA 전달(A1111은 `<lora:>` 프롬프트 문법, ComfyUI는 노드 체인), 생성→저장, 경로·해상도, 학습셋·배경판·범람체 모드, 재실행 시 건너뛰기, dry-run이 파일을 만들지 않는 것, 서버 꺼졌을 때 오류 메시지, `--backend` 전환.

**진짜 WebUI로는 테스트하지 못했다.** 모의 서버는 응답 형태를 재현한 것이지 실물이 아니다. 처음에는 `--only ju-habin --situations normal` 로 한 장만 돌려 보길 권한다. 실패하면 `--list-models` 로 이름 체계부터 확인하는 게 빠르다.

## 배포 — `deploy.py`

생성한 이미지를 전용 깃헙 저장소에 올리고 jsDelivr CDN 주소를 만들어 준다. 통합 프롬프트의 `{IMG}`에 넣을 기준 주소를 마지막에 출력한다.

```bash
python deploy.py --check                              검사만
python deploy.py --dry-run --repo 계정/이미지저장소     계획만 출력
python deploy.py --repo 계정/이미지저장소 --create      저장소 만들고 배포
python deploy.py --tag v2                             태그를 찍어 캐시 지연 없이 배포
python deploy.py --verify                             배포 후 주소가 열리는지 확인
```

저장소를 매번 적기 싫으면 `prompts.json`의 `deploy.repo`에 넣어두면 된다.

### 올리기 전에 검사한다

프롬프트는 축의 **닫힌 목록**을 싣고 모델은 그 안에서만 슬러그를 조합한다. 파일 이름이 한 글자라도 다르면 그 조합은 영원히 깨진 링크이고, 플레이 중에는 그냥 이미지가 안 뜨는 것으로만 보여서 원인을 찾기 어렵다. 그래서 업로드 전에 막는다.

- **목록에 없는 슬러그의 파일 → 중단.** 오타이거나 축 목록이 낡았다.
- **목록에 있는데 없는 파일 → 통과.** 부분 커버리지는 정상 상태다. 프롬프트가 "조합이 없으면 그 자리만 생략"을 이미 규정한다.
- 과도하게 큰 파일 → 경고 또는 중단.

```
## 커버리지  (out)
  인물        12/90  ← 78장 없음
  scene      6/6

## 목록에 없는 파일 1개 — 슬러그 오타이거나 축 목록이 낡았다
  X scene/hq-loby.png
```

### 폴더 구조

`batch.py`의 출력 구조를 그대로 쓴다. 직접 그린 이미지를 올릴 때도 이 구조를 지키면 된다.

```
out/<인물>/<상황>.png      out/ju-habin/combat.png
out/scene/<장면>.png       out/scene/hq-lobby.png
out/bg/<배경>.png          out/bg/city-night.png
out/mob/<위협>.png         out/mob/swarm.png
```

### 캐시

jsDelivr는 브랜치 주소를 최대 12시간 캐시한다. 이미지를 갈아끼운 뒤 즉시 반영하려면 `--tag v2`처럼 새 태그를 쓴다. 태그 주소는 불변이라 영구 캐시되고 지연이 없다.

jsDelivr는 **공개 저장소만** 서빙한다. 비공개로 두려면 다른 호스팅이 필요하다.
