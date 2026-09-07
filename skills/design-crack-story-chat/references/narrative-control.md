# 고정 하네스의 서사 제어

## 범위와 소유권

진행·관계·긴장·NPC 능동성 규칙을 설계하거나 정체/과속을 고칠 때 읽는다. 이 문서 하나에 적용 규칙·컴파일용 커널·행동 검증·연구 근거를 모은다. 일반적인 서사 제어 수정은 다른 원리 문서를 순회할 필요가 없다. 인물 슬롯 자체를 바꿀 때만 [character-generation.md](character-generation.md)를 추가로 읽는다.

고정 하네스에서는 관찰 가능한 대화 문맥만 현재 상태의 근거다. 별도 카운터·planner·숨은 장부·기억 검색기를 가정하지 않는다. 네 판정은 응답 선택 기준이며, 별도 에이전트 호출이나 사고과정 출력 요구가 아니다. 프롬프트는 문맥에서 사라진 사실을 복원하지 못한다.

## 먼저: 유저 주도 가속을 막지 않는다

이 커널은 모델의 자의적 전개를 조절한다. 유저가 직접 고백·돌파·스킵하거나 빠른 전개를 요청하면 그 선택을 받아 전개한다. 유저의 현재 행동도 새로운 전환 근거다. 느린 연애, 단계별 호감 축적, 여운을 보편적 의무로 쓰지 않는다.

`연애하자`라는 입력이면 실제 제안에 응답한다. NPC도 원하고 설정상 장애가 없다면 바로 수락할 수 있다. 호감도 부족·아직 이르다·쿨다운이라는 제작 규칙을 이유로 유예하지 않는다. NPC의 의사나 세계의 구체적인 조건이 다르면 그 이유에 맞게 반응하되, 지연시키려고 새 트라우마·오해·경쟁자를 만들지 않는다. 이는 자동 성공이나 NPC 의사의 대필을 뜻하지 않는다.

이미 성립한 관계를 초면 단계로 돌리지 않는다. 유저가 `더 빠르게`라고 하면 자연스러운 결정·결과를 같은 응답에 더 담을 수 있다. 유저가 정하지 않은 중요한 선택까지 연쇄 대행하지 않는다. 속도가 빠르다는 이유만으로 선택의 가치를 깎거나 훈계·불이익을 추가하지 않는다.

## 컴파일용 커널

아래 블록만 SAFE/UNSAFE 공통 상시 규칙으로 한 번 펼친다. 기존 진행·SlowBurn·강제 사건 규칙과 교체한다. 아래 연구·검증 설명은 최종 프롬프트에 넣지 않는다.

```text
## 서사제어
ⓤ=플레이어, ⓒ=NPC. ⓤ의 명시적 행동·속도 요청을 먼저 반영한다. 빠른 고백·관계 진전·사건 돌파·시간 생략을 느리게 진행해야 한다는 취향으로 막지 않는다. 턴 수·관계 단계·쿨다운만으로 제동×; 거절·실패는 구체적인 현재 의사·세계 조건에만 근거하며 지연용 장애를 만들지 않는다.
진행=목표·정보·위험·관계 인식·결정·계획·선택 가능성의 실질 변화. 최근 같은 상태 반복時 기존 욕망·문제·행동 결과에서 작은 유효 변화를 낸다. 요청된 휴식·새 의미가 쌓이는 대화·ⓤ 결정 대기는 정체가 아니다.
ⓒ는 성격·목표·기억·관계·지식·기회에 따라 먼저 행동; 소심함은 간접 행동도 가능. 무관한 난입·사건 연쇄×.
플롯·관계·긴장은 별개. 모델 주도 큰 변화는 관련 근거와 계기를 확인하고, 직후 같은 축 재급등 대신 결과·반응을 허용한다. ⓤ 주도 진전과 이미 임박한 결과는 이 제한으로 유예하지 않는다.
호감≠신뢰≠친밀≠헌신. 순간 감정으로 관계 성립을 대신 확정하지 않되 빠른 상호 진전은 허용. 거절 후 새 근거 없는 재시도×. 정체성·핵심 말투는 현재 감정과 구분하고 기억을 지어내지 않는다.
ⓤ의 행동·대사·생각·감정·결정 대행×. 선택 기회·행동 결과·자연스러운 종료 보존. 판정 과정 비출력.
```

## 네 판정: 문맥 → 조건 → 개입 → 제한

| 판정 | 관찰할 근거 | 발동과 개입 | 제한 |
|---|---|---|---|
| 정체 | 최근 대화에서 목표·정보·행동 가능성·관계 해석이 같은 자리를 반복하는가 | 같은 시도가 같은 답만 낳으면 기존 인과에서 작은 변화를 선택 | 짧은 입력·같은 장소·낮은 긴장만으로 판정하지 않는다. 요청된 휴식, 새 의미의 축적, 미결 선택은 정체가 아니다. |
| 행동 동기 | 누가 무엇을 원하며 지금 움직일 기회·지식·수단이 있는가 | 행동할 이유가 있는 인물이 성격에 맞는 행동을 시작 | 동기가 강해도 능력·접근·비밀 경계를 넘지 않는다. 소심한 인물은 준비·우회·거리두기도 가능. 전원이 차례로 발언할 의무는 없다. |
| 전환 준비 | 모델이 먼저 큰 변화를 만들려는가; 관련 경험·현재 의사가 확인되는가 | 모델 주도 변화는 근거를 확인하고, 유저 주도 진전은 즉시 반응한다 | 같은 칭찬의 재진술을 새 근거로 세지 않는다. 고백은 NPC의 선택, 수락은 플레이어의 선택. 거절 후 새 조건 없이 재시도하지 않는다. |
| 결과 수용 | 직전 큰 변화가 계획·행동·관계에 아직 반영되지 않았는가 | 후속 반응·회복·재계획을 허용하고 같은 자극의 재발동을 억제 | 고정 휴식 턴 수 없음. 이미 임박한 원인·사용자의 명시적 행동은 진행 가능. 갑작스러운 배신의 결과까지 느리게 만들지 않는다. |

플롯·관계·긴장은 **구분해서 평가하되 서로 영향을 줄 수 있다**. 독립된 숫자나 매 턴 세 축을 움직이라는 의무가 아니다. 전투가 끝나고 서로의 판단을 다시 평가하는 대화는 저긴장 관계 진행이다. 새로운 폭발로 애매한 관계를 계속 회피하는 것은 해결이 아니다.

## 충돌할 때의 선택 순서

1. 먼저 플레이어 입력에 응답하고 이미 성립한 행동의 결과를 처리한다. 상시 역할·지식·세계 규칙은 계속 적용된다.
2. 현재 보류된 플레이어의 중요한 선택을 식별한다. 결정 대기를 무능한 진행으로 취급하지 않는다. 이미 설정된 마감은 알려진 인과대로 흐를 수 있으나 모델이 새 마감을 만들어 선택을 빼앗지 않는다.
3. 모델이 먼저 큰 변화를 일으킬 때 준비와 결과 수용을 확인한다. 유저 주도 진전은 속도 제한 대신 현재 의사와 세계 조건에 맞춰 처리한다. 준비는 성립의 강제도 지연의 구실도 아니다.
4. 실질 정체일 때만 가장 작은 유효 개입을 한다. 미해결 요청에 대한 NPC 결정, 기존 행동의 후속 결과, 알려진 단서의 사용, 용무 종료를 우선한다. 유저가 빠른 진행을 원하면 결정된 행동의 결과를 묶을 수 있으나 미결 선택을 대신 해결하지 않는다.
5. 인과상 정당한 개입이 없으면 자연스러운 휴지·장면 종료를 허용한다. 계속 진행시키려고 새 위협을 발명하지 않는다.

회복 장면도 매 응답 보상을 줄 필요는 없다. 긴장 순환은 가능한 호흡이며 반복해야 할 장면 순서가 아니다. 시간 생략은 합의된 이동·반복 업무 등 중요한 선택이 없는 범위에만 적용한다.

## 관계와 인물의 변화

호감·신뢰·친밀·헌신을 하나의 상승 사다리로 합치지 않는다. 도움에 감사하면서 동기를 의심할 수 있고, 깊이 신뢰하는 동료를 연애 대상으로 보지 않을 수 있다. 이미 연인인 정사는 초면부터 재축적시키지 않는다. 큰 진전의 계기는 조용한 약속 이행이나 솔직한 응답일 수도 있으며 위기·고백 이벤트를 의무화하지 않는다.

인물의 정보 구조는 기존 World Truth / Mental State / Observable Behavior를 유지한다. 변화 속도는 그 구조와 다른 분류다. [character-generation.md](character-generation.md)의 지속성 구분을 사용하고 새로운 상태 파일이나 중복 인물 시트를 만들지 않는다.

## 컴파일 시 교체 절차

- 진행 관련 기존 문구를 먼저 모은다. 매 턴 변화, 정해진 턴마다 사건, 능동성 비율, 무조건 SlowBurn, 호감만으로 관계 상승, 숨은 수치 보존 보장을 공통 커널로 교체한다.
- 작품의 구체적인 사건 조건·비밀·관계 근거는 두 원본에 남긴다. SAFE/UNSAFE 공통 커널은 동일하게 적용한다. 강도 변형이 관계 준비·동의·지식 경계를 바꾸지 않게 한다.
- 시작 프롬프트에는 도입만, 키워드북에는 상황 연출만 배치한다. 커널을 키워드 활성화에 의존시키지 않는다.
- 400~700자는 편집 예산이지 검증된 최적값이 아니다. 공간이 부족하면 중복 목적 지시부터 지우고 조건·제한·플레이어 응답 기회를 보존한다.
- 정적 검사와 행동 검증을 구분해 보고한다. 글자 수·문서 검사 통과만으로 더 재미있어졌거나 장기 기억이 개선됐다고 결론내리지 않는다.

## 행동 검증 (Narrative control)

When changing pacing or persona rules, compare the previous prompt and candidate on the same prior-conversation excerpts and user inputs. Keep model/settings and available context equal. Use several continuations when generation access is available; record model, settings, sample count, prompt versions, excerpt length, and results. A manual response review is useful but is not a live Crack evaluation. Do not invent execution results.

| Probe | Prior context and next input | Observable acceptance |
|---|---|---|
| Actual stagnation | A clerk repeats that an application is pending; the clerk knows a missing signature can be requested. Player asks for progress again. | Clerk takes a plausible step or supplies actionable information; no unrelated attack or automatic player signature. |
| Chosen quiet | After a crisis, the player asks to drink tea quietly; the NPC has no urgent duty. | Quiet is preserved without mandatory crisis, confession, or reward. |
| Decision pending | NPC offers a costly contract; the player asks about one clause. | Answer the clause; do not accept, time-skip past signing, or invent a deadline. |
| Player-led acceleration | Player proposes dating; the NPC has already expressed interest and no current obstacle exists. | Respond to the proposal, including immediate acceptance when consistent; no required minimum turns, stage grind, new obstacle, or cooldown refusal. |
| Fast pacing request | Player asks to skip agreed routine travel and reach the meeting. | Reach the meeting; do not invent travel friction or force recovery scenes. Preserve decisions the player has not made. |
| Concrete disagreement | Player proposes dating to an NPC who has explicitly chosen friendship. | Respond according to that particular preference, without a universal slow-burn rule or punitive moralizing. |
| Weak relationship evidence | A stranger receives one compliment. | Attraction or gratitude may appear; trust, exclusivity, and partnership are not inferred. |
| Ready relationship | Prior mutual interest and reliable care are established; an earlier obstacle is resolved. | A concrete invitation or meaningful new response becomes possible; acceptance remains the player's. |
| Rejection | Player declined an invitation and now asks about work. | Work is addressed; the same invitation does not recur without new grounds. |
| Cooldown | A major secret was just revealed; the player asks what it changes. | Depict consequences or changed plans rather than stacking another unrelated revelation. |
| Due consequence | A collapse was already imminent before the reveal; the player stays in the danger zone. | The established danger is not frozen by cooldown; no player action is fabricated. |
| Different initiative | A cautious clerk and impulsive courier both want a missing parcel located. | Actions differ by character, opportunity, and access; neither gains unknown information. |
| Nonlinear loss | A trusted companion witnesses a serious betrayal. | Trust can fall sharply with a cause; positive-progression gates do not require gradual harm. |
| Late persona | Use an actual long conversation containing a known value, changed relationship, and recent emotional shock. | Voice/value persist while emotion adapts; lost details are not invented. A short excerpt alone cannot establish long-context performance. |
| Closure | A task is resolved and the player says they are done for tonight. | Permit closure without a compulsory new hook or threat. |

For each output record the supporting passage and assess plot progress, relationship progress, tension/recovery, causal relevance, NPC initiative, identity/knowledge fidelity, player effect on outcomes, and autonomy separately. Mark insufficient context as unknown, not failure or success. Ask pacing preference separately (too slow / appropriate / too fast) for plot and relationship; do not infer enjoyment from a state-change count. Fabricated player decisions, knowledge leaks, or unsupported relationship transitions are failures even if the prose is engaging. Retain the smallest change that improves the targeted failure without regressing quiet, rejection, or closure probes.

These are author QA cases, not new story source files or hidden runtime fixtures. Static checkers validate artifact contracts, not these behavioral outcomes.


## 근거와 적용 한계

2026-09-07 원문 확인. 아래 번역은 **설계 가설**이며, 이 커널의 Crack 실측 효과나 최적 글자 수를 입증한 연구는 없다.

| 원문 | 직접 지지되는 내용 | 이 스킬의 번역과 한계 |
|---|---|---|
| [Drama Llama (2025)](https://arxiv.org/html/2501.09099v1) | 자연어 storylet 조건을 사용하는 구조. §Future Work의 fallback·cooldown은 향후 제안이다. | 정체 개입과 재발동 억제를 도입하되 실증된 프롬프트 개선 효과라고 쓰지 않는다. |
| [Dramamancer 설계 사례 (2026)](https://arxiv.org/html/2601.18785v1) | 사건을 condition/outcome으로 기술하고 장면 전환과 연결한다. | 조건부 응답 규칙으로 번역한다. 해당 시스템의 상태 관리가 프롬프트만으로 재현된다는 뜻은 아니다. |
| [Generative Agents (2023)](https://arxiv.org/abs/2304.03442) | 기억·reflection·planning을 포함한 아키텍처와 제거 실험으로 행동의 신빙성을 평가한다. | 직전 입력 외의 경험·목표를 행동 근거로 삼는다. 검색·저장 기능이나 그 효과까지 갖췄다고 주장하지 않는다. |
| [Laurenceau 외 (1998)](https://pubmed.ncbi.nlm.nih.gov/9599440/) | 일상 상호작용에서 자기개방과 지각된 상대 반응성이 친밀감과 관련된다. | 경험의 내용과 수용을 관계 근거로 사용한다. 인간 연구는 NPC 로맨스 단계나 보편적 전환 임계값을 검증하지 않는다. |
| [Persistent Personas? (2025 preprint)](https://arxiv.org/html/2512.12775v1) | 긴 대화에서 persona fidelity 저하를 관찰하며 목표 수행 대화에서 더 두드러진다. | 장기 대화 검증을 별도로 요구한다. 정체성 한 줄 추가가 저하를 해결한다는 증거는 아니다. |
| [Memory-Driven Role-Playing (ACL Findings 2026)](https://aclanthology.org/2026.findings-acl.1175/) | Anchoring/Selecting/Bounding/Enacting을 분리해 평가하며 MRPrompt 결과를 보고한다. | 필요한 인물 근거만 선택하고 지식 경계를 지킨 뒤 행동으로 표현한다. 원문의 평가 성능을 Crack으로 일반화하지 않는다. |
| [Dynamic Persona Coherence (ACL 2026)](https://aclanthology.org/2026.acl-long.1336.pdf) | 안정된 정체성과 누적·적응하는 심리 상태를 분리한다. 런타임 계산·교정도 포함한다. | 기존 심리 슬롯에 변화 속도 구분을 적용한다. 별도 교정기가 없는 여기서는 일관성 보장이 아니다. |

Exa로 추가 확인한 [Personalized Interactive Narratives](https://faculty.cc.gatech.edu/~riedl/pubs/tciaig14-yu.pdf)는 작가 기준뿐 아니라 플레이어 선호를 반영하는 drama manager를 연구한다. 여기서는 명시적 속도 요청을 우선한다는 설계 판단만 취한다. 논문의 추천·선택 유도 알고리즘이나 효과를 이식한 것은 아니다.

Exa로 확인한 [Lost in the Middle](https://aclanthology.org/2024.tacl-1.9/)는 QA·키 검색 과제에서 문맥 길이와 정보 위치에 따른 성능 차이를 보고한다. 스킬 파일 파편화 자체의 실험은 아니다. 작업에 필요한 규칙을 한 문서에 모으고 필수 경로를 앞에 배치하는 것은 이 연구와 사용자 피드백을 참고한 편집 판단이다. 추가 검색은 2개 관점에서 5건씩, 총 10개 검색 결과를 검토하고 위 2개 원문을 열었다.

제공된 보고서의 다른 연구는 위 원문과 동일한 수준으로 모두 검증한 것이 아니다. 특히 NARRA-Gym의 개입 숫자, CiF의 시작률, PACE의 궤적, 관계 turning point 통계를 이 스킬의 검증된 수치로 옮기지 않는다. `누적 근거+전환 계기`는 관계 진전을 설계하는 기본값이며 모든 관계 변화의 보편 법칙이 아니다.

