# 이 저장소에서 작업할 때

크랙 스토리챗 설계 스킬과, 그 스킬로 만든 예제 작품, 이미지 제작 도구가 들어 있다.

## 무엇을 고치는 곳인가

| 하려는 일 | 고칠 곳 |
|---|---|
| 스킬 규칙을 바꾼다 | `skills/design-crack-story-chat/references/*.md` |
| 스킬 워크플로를 바꾼다 | `skills/design-crack-story-chat/SKILL.md` |
| 검사 규칙을 바꾼다 | `skills/design-crack-story-chat/scripts/*.py` |
| 예제 작품의 설정을 바꾼다 | `examples/hunter/story.md` · `characters.md` |
| 이미지 정리·배포 도구를 바꾼다 | `tools/images/deploy.py` |

## 절대 직접 고치지 않는 것

`examples/hunter/build/` 아래 전부. 두 원본에서 매번 다시 생성되는 산출물이다. 직접 고치면 두 번째 원본이 되고, 다음 컴파일에 사라진다. `build/assets/`의 파생물(요약 코멘트·이미지 프롬프트)도 마찬가지다.

원본을 고쳤으면 재컴파일하고 기준을 갱신한다.

```bash
python3 skills/design-crack-story-chat/scripts/check_freshness.py examples/hunter          # 뭐가 바뀌었나
# … 재컴파일 …
python3 skills/design-crack-story-chat/scripts/check_freshness.py examples/hunter --stamp  # 기준 갱신
```

## 무엇이든 고친 뒤에

```bash
./scripts/validate.sh examples/hunter
```

통과하지 않으면 커밋하지 않는다. CI가 푸시마다 같은 검사에 더해 음성 대조까지 돌린다.

## 검사기를 손볼 때

**통과했다고 보고하는 검사기를 믿기 전에 실패해야 마땅한 입력을 먹여본다.** 모든 것을 조용히 통과시키는 검사기는 없는 것보다 나쁘다 — 탐색을 끝내버리기 때문이다. 이 저장소의 검사기는 전부 CI에 음성 대조가 붙어 있고, 새로 만드는 검사기도 같은 대우를 받아야 한다.

## 스킬 규칙을 쓸 때

- 근거를 함께 적는다. "이렇게 하라"만 있는 규칙은 다음 사람이 지운다.
- 실측한 숫자가 있으면 숫자를 적는다. 인상으로 쓰지 않는다.
- 이미 있는 규칙과 충돌하면 둘 중 하나를 고친다. 두 규칙을 나란히 두지 않는다.
- 플랫폼 동작을 추측해서 규칙으로 만들지 않는다. 확인되지 않았으면 그렇게 표시한다.

## 문서 언어

문서와 주석은 한국어, 코드 식별자와 파일 이름은 ASCII. 스킬 레퍼런스는 파일마다 언어가 다른데(일부 영어, 일부 한국어) 기존 파일의 언어를 따른다.

## 예제 작품을 건드릴 때

`examples/hunter/`는 장식이 아니라 CI가 검증하는 실물이다. 여기를 깨면 빌드가 깨진다. 인물을 추가하면 이미지 프롬프트 명부도 같이 늘려야 `check_image_assets.py`가 통과한다.
