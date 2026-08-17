# Conversation continuity without a runtime layer

## No runtime artifact

For this Crack workflow, “runtime” is not a project file, a sixth deliverable, or an assumed platform feature. Do not create state files, memory logs, JSON patches, hidden ledgers, or save/load commands.

Changing facts exist only in the live conversation: the profile the user supplied, visible scene outcomes, and prior dialogue. Canon remains in `story.md` and `characters.md`; the five build files contain static prompts only.

## First-input profile

The final start prompt parses the first reply to Crack's externally shown form as name, age, gender, ability name, ability description, and desired dialogue/situation.

- Prefer explicit labels, then the confirmed external-form order, then unambiguous natural language.
- Preserve commas and line breaks inside ability description and desired situation.
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
  - **Continuity carrier** — the block is where accumulated state is written down: date/time, location, the player's own sheet, equipment and inventory, relationship standing per character met, and the current objective. Because Crack keeps no durable store, re-emitting the block is what carries that state into the next turn's context. Emit it **every response without exception**, inheriting unchanged fields verbatim. A single skipped turn leaves the next turn with no prior value to inherit, and drift starts there.
- A carrier block is still derived presentation, not an authority. It restates only what the conversation already depicted or established; it never becomes a hidden ledger, a save file, or a substitute for canon.
- When a status/HUD block is emitted, inherit its last publicly established values. Change only fields supported by the player's latest explicit input or a depicted/summarized event in the conversation; never reset, randomize, or fill an unknown value merely because the block reappears.
- Specify every HUD with `position | form | omission | update`. Example: `위치=본문끝|형태=코드펜스 안 [시각·장소/ⓤ 신상·능력/장비·소지품/관계/목표·상황]|생략=연속성 운반이면 없음|갱신=직전값계승,본문근거필드만변경`.

## Platform history summarization

Some Crack works ship an explicit instruction for how prior conversation should be summarized, which implies the platform performs summarization the author can steer:

```text
Previous History:주요캐릭터별核心現況만要約,事件細部·行爲·臺詞記錄無
단편사건위주:Previous History를 절대로 활용하지 않음
```

The first keeps a per-character current-state digest and discards scene detail — appropriate for a long ensemble arc where who-stands-where matters more than what was said. The second disables history entirely, which suits an episodic work whose scenes are meant to be independent.

Decide which the work needs and state it, because the default is neither: an unsteered summary tends to keep vivid detail and drop standing state, which is exactly backwards for continuity. **Whether Crack honours this instruction is unverified** — treat it as a request until observed, and never let continuity depend on it alone. The status block remains the carrier.

## NPC statements are not settled fact

A rule worth stating explicitly, because its absence produces a specific tangle: the model writes an NPC line that contradicts canon or an earlier scene, then defends it, because whatever it output reads as established.

```text
ⓒ의 발언·판단·기억=확정 사실×. 새 정보·반박·모순이 나오면 검토하고, 틀렸으면 고집·합리화 없이 인정·수정한다.
직전 출력의 ⓒ 발언=그 ⓒ가 한 말. 설정·상황과 모순되면 말실수·오해로 정정하되, ⓤ의 발언으로 떠넘기지 않는다.
```

Three things happen here. NPC speech is demoted from narration to **a claim by that character**, which can be mistaken. Contradictions get an in-fiction repair path — the character misspoke or misunderstood — rather than a retcon. And the repair is fenced: the model may not resolve its own inconsistency by attributing words to the player. Without that last clause the correction mechanism becomes an agency violation.

## Long conversations and tests

Do not assume Crack has durable storage. If a long conversation needs a recap, use only a user-provided or visibly established summary, and never save it beside the two authored source files.

Test major reveals, escalations, crises, and endings from a short representative prior-conversation excerpt. Assert who knows what, which behavior stage is available, and where player control returns; do not build a synthetic runtime snapshot or state fixture.
