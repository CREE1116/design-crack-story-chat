# Conversation continuity without a dialogue-history field

## No runtime artifact

For this Crack workflow, “runtime” is not a project file, a sixth deliverable, or an assumed platform feature. The current creator-custom setup has no authored dialogue-history field. Do not create `Previous History` instructions, conversation-record files, state files, memory logs, JSON patches, hidden ledgers, or save/load commands.

Changing facts exist only in the live conversation: the profile the user supplied, visible scene outcomes, and prior dialogue. Canon remains in `story.md` and `characters.md`; the five build files contain static prompts only.

## First-input profile

Derive the player-profile fields from what the current project's `story.md` and `characters.md` actually require. The final start prompt parses the first reply to Crack's externally shown form into that project-defined list; it never assumes a fixed six-field schema or invents an ability axis for a world that has none.

- Prefer explicit labels, then the confirmed external-form order, then unambiguous natural language.
- Preserve commas and line breaks inside free-text fields such as an ability description or desired situation.
- Do not invent missing fields. Ask only for the missing field; do not repeat the form.
- `없음` is a valid desired dialogue/situation.
- Treat the desired dialogue/situation as an opening request, never as a player action or spoken line already completed.
- Interpret a user ability through the world canon's scope, cost, and limits before narrating its effect; do not create an external approval status or hidden record.

## Continuity rules

- Advance time only from depicted or summarized action, not response count.
- Keep relationship behavior tied to depicted causes and qualitative stages. A number, a turn count, or a status emoji never grants consent, romance, forgiveness, a reveal, or an irreversible decision.
- Treat a fact as established only when it appeared in the conversation or is canonical. Do not recover lost context by inventing a memory.
- If the story uses a status block, make it a brief public recap of already observed facts: current location/time, present people, public condition, or scene goal. Do not expose secrets, invisible flags, private reasoning, or NPC-only knowledge.
- Decide first which of two jobs the status block does, because the emission rule follows from it.
  - **Decorative recap** — a convenience summary of what the player just read. Omit it when it adds no playable information.
  - **Fixed HUD** — the block shows accumulated public state such as date/time, location, the player's own sheet, equipment and inventory, relationship standing per character met, and the current objective. Emit it every response only when the experience deliberately promises a fixed HUD; inherit unchanged public fields verbatim.
- A fixed HUD is still derived presentation, not an authority. It restates only what the conversation already depicted or established; it never becomes a dialogue history, hidden ledger, save file, persistence guarantee, or substitute for canon.
- When a status/HUD block is emitted, inherit its last publicly established values. Change only fields supported by the player's latest explicit input or a depicted/summarized event in the conversation; never reset, randomize, or fill an unknown value merely because the block reappears.
- Specify every HUD with `position | form | omission | update`. Example: `위치=본문끝|형태=코드펜스 안 [시각·장소/ⓤ 신상·능력/장비·소지품/관계/목표·상황]|생략=고정HUD면 없음|갱신=직전공개값계승,본문근거필드만변경`.

## Design the HUD as an interface, not a readout

A fixed HUD that only mirrors prose earns little. The same block can carry the story's mechanics if each field is designed for a job. Five patterns, all cheap.

### Give the core loop a field

Whatever the story is *about* should be legible in the block. A project whose premise was inventing a lost combat style carried `[체계]` — the method the player has established so far, named by the player, `없음` until something works. The field starts empty and fills as the player earns it, so the block shows progress toward the story promise rather than restating the scene.

Pick the one field whose value a reader could not guess from the last paragraph. That is the field worth having.

### Separate single-select slots from cumulative markers

Two different jobs get confused when both are "an emoji in the relationship line."

- **Single-select** — one value from an enumerated set, replaced when it changes. Current feeling toward the player: `😐중립 🙂호의 😄친밀 🥰애착 🫂신뢰 😳동요 🤨의심 😠적대`.
- **Cumulative** — a fact that, once true, stays true and is appended. A history marker sits *after* the feeling and persists even when the feeling turns cold.

Say which kind each marker is. Without it a history marker gets overwritten the first time the mood changes, and the block quietly loses the thing it existed to remember.

### A state field can gate a rule

The strongest use: let a field be the visible precondition for something the model may otherwise attempt too early.

```text
🔞=성적 장면 진입 가능, [상황] 신호등 뒤에. 조건=관계 친밀 이상+사적 공간+둘만+상호 의사가 본문에 드러남.
하나라도 깨지면(이동·제3자·거절) 즉시 뗀다.
🔞 없으면 성적 접촉·유혹·암시 진입×, ⓒ는 시도조차×. 🔞 있어도 표시≠동의: 진입은 ⓤ의 명시적 행동으로만.
```

Three properties make this work. The gate is **visible**, so the player reads the world's state instead of guessing it. It is **conditional on depicted facts**, so it cannot be argued into existence. And the marker is explicitly **not** consent — availability and permission stay separate, which is the distinction a plain "slow burn" instruction never manages to hold.

The same shape suits any precondition the fiction gates: a duel that needs a safety declaration, a restricted archive that needs faculty approval, a contract that needs a witness.

### Declare a starting value per field

The first response has to emit the block before the player has supplied anything. Every field needs a stated turn-one value, or the model guesses one and contradicts it two turns later.

```text
기숙사·학년·학부: 학부=ⓤ 선택값, 기숙사 시작=상록관 · [측정]: 미측정 · [체계]: 없음 · [관계]: 없음
```

Distinguish *not yet known* (`미상` — the player has not said) from *established as empty* (`없음` — canon says there is nothing yet). They behave differently on update: the first gets filled by player input, the second by a depicted event.

### Scope fields to the variant that can set them

A field the SAFE variant can never populate is noise on every SAFE turn. Gate and history markers tied to explicit content belong in the UNSAFE delta only; the shared core keeps the fields both variants actually use.

This does not break the pair rule. Variants must not differ in outcomes, canon, consent, or syntax — dropping a marker that is unreachable in one profile changes none of those. What must stay identical is the behaviour the marker gates: SAFE still forbids NPCs from initiating, it simply says so in prose instead of showing a badge.

### The block's emoji are also keyword triggers

Anything the block prints every turn is a reliable keyword-book trigger, and the two lifetimes match for free. See `keyword-book.md`.

## NPC statements are not settled fact

A rule worth stating explicitly, because its absence produces a specific tangle: the model writes an NPC line that contradicts canon or an earlier scene, then defends it, because whatever it output reads as established.

```text
ⓒ의 발언·판단·기억=확정 사실×. 새 정보·반박·모순이 나오면 검토하고, 틀렸으면 고집·합리화 없이 인정·수정한다.
직전 출력의 ⓒ 발언=그 ⓒ가 한 말. 설정·상황과 모순되면 말실수·오해로 정정하되, ⓤ의 발언으로 떠넘기지 않는다.
```

Three things happen here. NPC speech is demoted from narration to **a claim by that character**, which can be mistaken. Contradictions get an in-fiction repair path — the character misspoke or misunderstood — rather than a retcon. And the repair is fenced: the model may not resolve its own inconsistency by attributing words to the player. Without that last clause the correction mechanism becomes an agency violation.

## Long conversations and tests

Do not assume an author-controllable dialogue-history or durable-storage field. If a long conversation needs a recap, use only a user-provided or visibly established summary in the live chat, and never save it beside the two authored source files.

Test major reveals, escalations, crises, and endings from a short representative prior-conversation excerpt. Assert who knows what, which behavior stage is available, and where player control returns; do not build a synthetic runtime snapshot or state fixture.
