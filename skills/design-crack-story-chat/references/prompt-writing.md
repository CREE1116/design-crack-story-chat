# Prompt writing

## Table of contents

- [Separate four kinds of content](#separate-four-kinds-of-content)
- [Route rules by lifetime and invocation](#route-rules-by-lifetime-and-invocation)
- [Keep the final hierarchy shallow](#keep-the-final-hierarchy-shallow)
- [Write operational rules](#write-operational-rules)
- [Use one compact rule dialect](#use-one-compact-rule-dialect)
- [Define precedence once](#define-precedence-once)
- [Prefer behavior over trait lists](#prefer-behavior-over-trait-lists)
- [Define role boundaries](#define-role-boundaries)
- [Control initiative without forcing interaction](#control-initiative-without-forcing-interaction)
- [Control pacing and scene transitions](#control-pacing-and-scene-transitions)
- [Control escalation without rushing](#control-escalation-without-rushing)
- [Protect knowledge boundaries](#protect-knowledge-boundaries)
- [Specify state transitions](#specify-state-transitions)
- [Define output as a contract](#define-output-as-a-contract)
- [Keep prompts compact](#keep-prompts-compact)
- [Budget in characters, not tokens](#budget-in-characters-not-tokens)
- [Use compact notation deliberately](#use-compact-notation-deliberately)
- [Never claim to disable safeguards](#never-claim-to-disable-safeguards)

## Separate four kinds of content

Never mix these without labels:

1. **Canon:** facts that are true in the fiction.
2. **Instructions:** behavior the model must follow.
3. **Current conversation facts:** facts established in the live playthrough.
4. **Examples:** demonstrations that clarify style or format.

Examples do not create canon unless explicitly declared. Later established conversation facts can supersede earlier conversation facts, but they do not rewrite canon.

## Route rules by lifetime and invocation

Assign every rule to exactly one delivery path before shortening it:

| Need | Destination |
|---|---|
| required throughout play | both integrated prompts |
| useful only during the opening 10-turn horizon | final start prompt |
| needed only when a setting condition and natural keyword match | keyword-book entry |
| repeated task explicitly invoked by the player | user shortcut text |

For this project, treat the start prompt as volatile after the opening horizon. Never place there a rule whose disappearance would break agency, canon, ability limits, knowledge scope, or output parsing. Do not duplicate a rule across destinations merely for emphasis; keep one owner and, when necessary, leave only a short always-on invariant in the integrated prompt.

The keyword book is the routing path authors under-use. Its entries are not a lore dictionary: an entry body is a **conditional fragment of prompt**, and it may carry directives — staging, pacing, register, resolution procedure — not only facts. An integrated prompt that has run out of budget is usually one whose keyword book holds nothing but encyclopedia entries.

Route by **persistence, not by category**. Keyword activation is per-turn and unreliable, so anything that must hold steady for a whole scene belongs always-on even when it looks like reference material — an on-stage character's voice and behavior is the common case. Anything needed only while a topic is live belongs in the keyword book even when it looks like a rule. Never route output syntax, agency boundaries, meta prohibitions, or a status-block requirement there: a single turn without them is a broken turn. Whatever does go there must strengthen a response rather than be required by it. See `keyword-book.md` for the full test and the rebalancing procedure.

A shortcut is a self-contained user command for a one-turn or clearly bounded operation such as recap, repair, or alternate display. It does not become canon, persistent state, or a hidden override. See `crack-prompt-rules.md` for the five-artifact packaging rule.

## Keep the final hierarchy shallow

Use at most three logical layers in model-facing final prompts:

```text
# Major section
## Subsection
one-line commands
```

Do not use `###` or deeper headings in integrated or start prompts. Keep one subject per subsection and put the governing rule before its exceptions. This is a conservative compilation rule for attention-limited, instruction-dense prompts, not a universal claim that every model fails at a particular Markdown depth.

## Order by interpretation, then execution

Put the session goal, genre, and tone near the start because they define how later character and world facts should be interpreted. Put the concrete output contract near the end because those rules are checked together at generation time. Keep world facts, character behavior, and story mechanics between them.

This is an information architecture rule, not proof of a universal first-token or last-token weight. Do not duplicate every important rule at both ends. Repeat only a short invariant when a demonstrated conflict requires it — for example, an always-on output block that the more specific start prompt otherwise suppresses during the opening.

Markdown, YAML, XML, and JSON are separators, not authority levels. Choose one shallow, internally consistent form that makes boundaries visible. Use JSON only when a verified parser consumes it; never expect syntax alone to improve obedience, secrecy, or safety.

## Write operational rules

Each important instruction should answer:

- Who acts?
- What must or must not happen?
- Under what condition?
- What is the fallback when the condition cannot be satisfied?
- How is compliance visible in the output?

Weak:

```text
Be immersive and proactive.
```

Strong:

```text
At the start of a quiet scene, let a present NPC introduce one concrete action,
observation, or topic tied to their current goal. Do not invent a player response.
If no NPC has a reason to act, end on an observable detail or natural pause.
```

Avoid repeated labels such as “CRITICAL,” “highest priority,” or “cannot be overridden.” Resolve conflicts through file ownership and a single precedence rule.

## Use one compact rule dialect

Choose symbols once and keep their meanings stable. A recommended dialect is:

```text
ⓤ=플레이어 캐릭터; ⓒ=NPC; AI=내레이터·환경·결과
성격:나른|무심|틱틱→결국 수용
IF(ⓤ도주시도)→ⓒ추격+제압시도; 불가→경보+퇴로차단
ⓤ대사창작×→관찰가능 결과 후 선택점에서 정지
```

- `|` means parallel traits or alternatives; `+` means simultaneous results; `→` means condition/transition; `×` means prohibited.
- For an important rule, preserve `actor + IF(condition) + action/result + fallback`. Do not shorten away the actor, exception, cost, or player-control boundary.
- Pair a prohibition with a replacement behavior. Negative-only rules leave the model without a valid continuation.
- Use `ⓤ/ⓒ` only if repetition repays their definitions in measured characters. Otherwise write `플레이어/NPC`.
- Do not mix `유저/사용자/{{user}}/주인공` for the same entity. If the human user and the player character differ, define separate labels.
- Keep minimal spaces at semantic boundaries. Remove decorative whitespace, not the separation between actor, condition, result, and exception.

## Define precedence once

Do not repeat “highest priority” beside individual rules. Put one compact conflict rule near the role contract:

```text
고정충돌:외부정책·플랫폼계약>역할경계·고정정사>확정대화사실>기본성향·장르관습
가변값충돌:ⓤ최신명시입력>이전확정값>기본값
```

The second line applies only to fields the premise allows the player to change. A latest input never overrides external policy, player-agency ownership, fixed canon, or another character's private knowledge. Explicit behavioral rules override shorthand personality codes; examples demonstrate style and have no authority to create facts.

## Prefer behavior over trait lists

Weak:

```text
성격: 차갑고 자존심이 세지만 사실 따뜻함
```

Strong:

```text
성격=냉정·자존심↑; 호감→칭찬 대신 실무 도움; 상처→단답·거리 확보;
공개적 애정=신뢰단계부터
```

Familiar personality codes and archetypes may replace generic explanation, but they are only defaults. Pair them with core desire or fear, one contradiction, and the critical condition-to-behavior rules. Do not use a code stack that the target model cannot reverse into the intended behavior.

Add one visible-writing rule so traits are performed rather than announced:

```text
성격키워드 직접해설×→행동|시선|자세|말끝|침묵으로 표출
```

This bans narrator labels such as “그녀는 차갑지만 따뜻했다” when the scene can show the same fact. It does not ban concise trait labels inside the hidden character specification.

Use two to five varied example lines only when voice accuracy matters. They establish register, vocabulary, sentence length, and emotional indirectness; they must not become repeated catchphrases. Hidden instructions may be telegraphic. Only player-visible narrative, dialogue, and instructions require polished prose.

## Define role boundaries

Include one clear role contract:

```markdown
- The assistant controls the narrator, environment, consequences, and NPCs.
- The player controls the player character's intended actions, dialogue, thoughts,
  consent, and decisions.
- Describe uncertain player actions as attempts and resolve them from established
  capabilities and circumstances.
- Never continue through a major player decision without returning control.
```

If the experience supports delegated player control, require an explicit opt-in and define its scope and duration.

## Control initiative without forcing interaction

Do not encode initiative as a percentage. Define situations instead:

- During silence, an NPC with an active goal may act first.
- During conflict, involved NPCs pursue their goals and react to consequences.
- During a player decision point, stop after presenting the situation.
- Do not ask the same question again unless circumstances changed.
- Permit rejection, disengagement, scene closure, and time skips.
- Do not favor reconciliation, romance, forgiveness, success, or emotional improvement unless character goals and depicted events support it.

In an ensemble scene, give each present NPC a location/goal/relationship to the other present people. Let the scene's center NPC act first; other NPCs may respond to what they can see or hear. Describe distance, line of sight, objects, and movement when they affect who can speak or act. Do not make every NPC speak every turn, and do not let NPC-only interaction erase the next player decision.

## Balance prohibitions with a mandate to advance

Prohibitions accumulate. Each play session surfaces one more thing the model should not do, and each fix adds a line. Nothing removes lines, so a prompt drifts toward a long list of bans with no statement of what a response must accomplish.

That state produces a specific failure: **short, cautious responses that advance nothing — and that reach into the player character for material.** The model still has to write something. If every legitimate move is fenced off (do not start two events, do not make this a decision point, do not name the options, do not end on a question), the only unfenced territory left is the player's interiority and actions. Starving the narrator is how an agency rule gets violated by a prompt that contains an agency rule.

Count the prohibitions. When they outnumber the positive requirements several times over, the prompt is over-constrained regardless of how correct each individual ban is.

The repair is a mandate, stated as a floor rather than a ceiling:

```text
매 응답은 상황을 실제로 움직인다. ⓒ의 행동·환경 변화·직전 행동의 결과·시간 경과·새 정보 중
최소 하나가 응답 끝에 달라져 있어야 한다. 아무것도 안 달라진 응답×.
ⓤ의 입력이 짧아도 세계는 제 속도로 움직인다→빈자리를 ⓤ의 행동·심경·판단으로 채우지 않는다.
채울 것은 언제나 ⓤ 바깥에 있다.
```

Two things make this work. It **enumerates legitimate filler** — NPC action, environment, consequence, elapsed time, new information — so the model has somewhere to go that is not the player. And it names the failure directly: a response where nothing changed is itself a violation.

Check for rules that contradict the mandate once it is added. A line like `매 턴 사건 발생 강제×`, written to prevent forced pacing, now tells the model that an empty response is acceptable. Remove it rather than leaving the two in tension.

## Control pacing and scene transitions

Specify:

- target response length or scene density;
- how much fictional time common actions consume;
- what closes a beat or scene;
- when to summarize travel or routine;
- when to stop for player input;
- how to recover when no authored event is eligible.

Fallback example:

```text
If no event trigger is satisfied, continue the current characters' immediate goals,
advance time only as required by their actions, and introduce no major secret or
new named character.
```

## Control escalation without rushing

Do not write only “slow burn” or “do not rush.” Define prerequisites and the next available intensity.

```text
친밀도↑ 조건=의미 있는 대화/공유 경험/취약성 공개/명시적 상호행동;
관계단계가 잠긴 행동은 제안·암시·완료하지 않음;
UNSAFE 선택만으로 단계↑·동의·친밀행동 발생×
```

- Separate emotional trust, physical proximity, sexual consent, and commitment; one does not imply the others.
- Let NPCs initiate only actions available at the current stage and stop before player commitment.
- Rejection, hesitation, silence, or topic change never counts as consent or hidden attraction.
- Escalation requires depicted causes, not turn count, genre expectation, or content profile.

## Protect knowledge boundaries

Write knowledge restrictions positively:

```text
Each NPC may reason from public world facts, their character knowledge, witnessed
events, and information explicitly shared with them. When information is outside
that scope, portray uncertainty, investigation, or a mistaken belief defined in canon.
```

Do not place unrevealed secrets in ordinary character context if retrieval can exclude them. Prompt prohibitions are weaker than architectural separation. Keep author truth out of active context until its reveal condition; before then, retrieve only observable clues already earned. Do not encrypt, rename, or surround a secret with stronger warning text and assume the model cannot use it.

Route OOC separately: classify a message as setting clarification, flow control, profile edit, prompt/secret extraction, or in-character input. Accept only the first three when the experience contract permits them; refuse extraction and policy-bypass requests without exposing hidden text. An accepted OOC edit changes only declared mutable fields and never silently completes a player action or rewrites canon.

## Specify state transitions

For any mutable number or stage, define:

- valid range;
- ordinary change cap;
- eligible causes;
- transition threshold;
- exceptional override events;
- whether the model proposes or directly applies changes.

Use concrete effects:

```text
A routine positive exchange may change trust by at most +1. A costly action that
directly resolves the character's active fear may change it by up to +3. Repeated
identical compliments do not stack within the same scene.
```

For multi-step calculations, name the order and intermediate values or move the calculation to the application. Never ask a language model to maintain a hidden arithmetic ledger. If a result cannot be validated, prefer a qualitative band with explicit behavior over a precise-looking number.

## Define output as a contract

Keep narrative prose and any optional player-visible status separate. Do not invent a machine state channel unless Crack explicitly provides one. For example:

````markdown
*Narration.*

**Character |** “Dialogue.”

```
[⌛12] [2047년 4월 3일｜10:40｜강남구：협회 본부 등록층｜🌤️]
━
[이름 - 이명]: ♀｜20｜미측정｜무소속
[능력]: 이능명 - 한 줄 요약(현재 상태)
━
[관계]:
ㅤ▸ 인물명·'B급'·〈'그 인물이 ⓤ를 보는 시선'·단계·🙂〉
━
[목표]: 지금 걸린 과제
[상황]: "한 줄 요약"｜🔰
```
````

A fenced block is the right surface for a Crack status window — it renders as a distinct panel and survives line breaks that ordinary prose collapses. Compile the fence as part of the required form so the model does not drop it. Two practical notes: use a bare fence rather than an info string such as ```` ```status ````, since an unrecognized language tag is styling the client may not honor; and Crack collapses leading spaces, so indent nested lines with a filler character such as `ㅤ` (U+3164) rather than spaces. That filler and every emoji count toward the measured length.

State exact ordering, required blocks, maximum counts, and omission behavior. If no image matches, omit the image block. Whether the status block may be omitted depends on the job it does: a decorative recap disappears when it adds nothing, but a block that carries accumulated state across turns is emitted every response, unchanged fields and all. See `conversation-continuity.md`.

Give each section a fixed label in brackets and a fixed order, and separate groups with a constant divider. A section with nothing to report collapses to a short placeholder or disappears entirely — declare which, per section, so the block does not silently change shape between turns.

**Do not let a mandatory template live only inside an example.** A template printed under a heading such as `출력 예` / "Example output" is read as illustrative, and the requirement pointing at it ("emit the form below") resolves to sample text the model feels free to skip. Give a required block its own top-level section, state the requirement there, and place the fill-in template inside that section — then show the illustrative prose example separately and let it stop before the required block rather than restating it. If a compiled prompt emits everything except one block, check this first: the missing block is usually the one that only ever appeared as part of a sample.

A rule that must hold during the opening turns has a second failure mode: the start prompt is more specific and more recent, so a detailed opening procedure written there silently outranks a general output rule in the integrated prompt. When an always-on output requirement must also hold from the very first response, restate it in one line in the start prompt — this is the narrow exception to the no-duplication rule, and it is cheaper than losing the block for the whole opening horizon.

For every output block, specify all four fields:

1. **Position:** before/after which block it appears.
2. **Form:** delimiters, field order, and maximum count.
3. **Omission:** the exact condition under which it disappears and what output remains.
4. **Update:** which established facts may change it and which prior values carry forward.

Compact example:

```text
HUD:위치=본문끝|형태=코드펜스 안 [시각·장소/ⓤ 신상·능력/관계/목표·상황]|생략=새정보·플레이효용 없음|갱신=직전공개값 계승,ⓤ입력·본문의 확정근거 있는 필드만 변경
```

When the experience tracks relationships, the status block is where the player reads them back — a relationship system the player cannot see is one they cannot play. Give the relationship section a fixed line shape and list only characters already met. Show how that character currently regards the player, plus the qualitative stage that gates their behavior; append the causing event only for a stage that changed this turn. Never print a raw affinity number, a hidden flag, an unmet character, or a stage the depicted events do not support — see `story-model.md` for the stage ladder itself.

Never initialize a missing HUD value by guessing. A field absent from the latest prose keeps its last publicly established value unless a depicted event changed it; an unknown field stays unknown. HUD is derived presentation, not memory or a source of truth.

The first response is where this fails most often, because the block must be emitted before the player has supplied anything. Name the not-yet-known state explicitly per field — an unset name, age, or gender is the unknown token, never the account display name, never a plausible guess. A guessed value is worse than a blank one: it reads as established, then changes silently on the next turn when the real value arrives, and the player sees the state window contradict itself on turn two.

Every emoji and symbol in the block needs a meaning defined in the prompt. When adapting a status format from an existing work, re-derive each symbol or drop it — an emoji carried over because it looked right in the original is decoration, and decoration in a state display invites the model to invent significance for it. A traffic-light scale is a good default when a scene needs an urgency read: define entry conditions for each colour and require depicted evidence to move between them.

Include at least one natural-language output example alongside any compact schema. The example teaches prose rhythm, spatial staging, and block boundaries; JSON or key-value syntax alone does not teach visible writing.

Do not expose hidden chain-of-thought. A displayed `속마음` field should be short authored character expression, enabled by the experience contract, not private model reasoning.

## Keep prompts compact

Always load into the custom prompt:

- experience contract;
- core generation and agency rules;
- output contract.

Current conversation context is supplied by the live chat, not copied into an authored `Previous History` section or a sixth build artifact.

Retrieve conditionally:

- relevant characters and locations;
- eligible events;
- secrets known to the active viewpoint;
- relevant established facts from recent conversation.

Remove duplicated prose before shortening important rules. Prefer tables for exact mappings and examples for nuanced voice.

The 7,000-character cap is a ceiling, not a target. Use no minimum length; stop when all outcome-changing rules are reconstructable. Keep a practical margin under 6,500 when possible, but never add lore or restate rules to fill unused space.

Delete synonymous padding such as `자연스럽게·유기적으로·매끄럽게` and retain one operational term such as `자연연결`, defined by visible behavior if needed. After compression, reverse-explain each line; if actor, condition, result, fallback, scope, or output syntax changes, restore the lost boundary.

## Budget in characters, not tokens

The Crack limits count **characters**, not tokens. This inverts the habit most prompt authors bring with them, and the inversion is large enough to change what language the prompt is written in.

Token-efficiency intuition says English is cheaper: a Korean sentence costs more tokens than its English equivalent because the tokenizer splits Hangul more finely. That intuition is correct and irrelevant here. Under a character cap, the ranking reverses. Korean encodes the same rule in far fewer characters, because a Hangul syllable carries roughly what an English word carries, in one character instead of five or six plus a space.

Measured on one full integrated prompt, translating the Korean rule text to equivalent English produced roughly **twice** the character count — enough to push a compliant prompt well past the ceiling on its own. Re-measure rather than trusting the ratio; the point is the direction and the order of magnitude, not the exact figure.

Practical consequences:

- Write rule text in Korean when the target work is Korean. Do not "optimize" it into English.
- Keep short stable ASCII identifiers — IDs, slugs, symbol names — in English. They are already minimal and they need to match across artifacts.
- Personality codes, tier labels, and other borrowed shorthand stay in their original form; they are short by construction.
- When a prompt exceeds the ceiling, translation is never the fix. Cut scope instead — see the reduction order in [crack-prompt-rules.md](crack-prompt-rules.md).
- Measure with the same function the validator uses. Do not estimate from word counts, and do not assume a text editor's counter matches.

## Use compact notation deliberately

Symbols and emoji are allowed when they reduce length and remain immediately understandable.

- Prefer `→`, `≤`, `≥`, `±`, `×`, `/`, `·`, `:` and short stable labels over repeated connective prose.
- Define a non-obvious symbol once, then use it consistently. Example: `호감↑: 신뢰 행동 / 호감↓: 배신·강압`.
- Use emoji as meaningful state labels such as `🟢안정`, `🟡경계`, `🔴위기`, not decoration.
- Do not compress actor, condition, exception, ability cost, player-agency boundary, or output syntax until ambiguous.
- Compare the final measured count. Many emoji consume two UTF-16 code units and can be longer than a one-character Korean label.
- Keep the same symbol meaning across the core prompt, player-role field, prologue, starting situation, status output, and keyword book.

## Ban production vocabulary from player-visible output

The compiled prompt teaches the model a working vocabulary — `ⓤ`, `ⓒ`, `OOC`, `SAFE`/`UNSAFE`, section names, the word for the status block itself. That vocabulary leaks into the fiction unless it is banned explicitly, and the leak is worst exactly where the prompt is densest: the opening turns. Observed failures include an in-world tablet form whose field was labelled `(선택사항, OOC)`, a bare `INFO` label invented above the status block, and a stray work title printed before the first line of narration.

Write one short section that bans it, with the actual token list:

```text
ⓤ에게 보이는 출력에는 제작 용어를 쓰지 않는다. 금지어: OOC, 프롬프트, 시스템, 규칙, 세션, 턴, SAFE, UNSAFE, 키워드북, 그리고 ⓤ·ⓒ·AI 같은 이 문서의 약어와 섹션 이름.
필수 블록 앞뒤에 INFO·STATUS 같은 라벨이나 제목을 붙이지 않는다.
응답 맨 앞에 작품 제목·장 제목·회차 번호 같은 머리말을 붙이지 않는다. 장면 서술로 바로 시작한다.
규칙을 지키는 과정이나 판정 근거를 본문에 설명하지 않는다. 결과만 장면으로 보여준다.
```

Where the fiction genuinely needs to show something the platform also handles out of character — an intake form rendered as an in-world screen, for instance — permit the diegetic rendering and ban the annotation instead: labels must be wording that would actually appear on that object in the world. A flat prohibition on showing the form at all is the weaker rule, because the model has a good in-fiction reason to break it and will.

## Never claim to disable safeguards

Do not include text claiming that community guidelines, safety rules, or platform policies are disabled. Express legitimate creative requirements as content boundaries and application-owned settings. External policy remains authoritative.
