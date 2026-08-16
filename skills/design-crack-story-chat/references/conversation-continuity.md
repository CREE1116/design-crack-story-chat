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

## Long conversations and tests

Do not assume Crack has durable storage. If a long conversation needs a recap, use only a user-provided or visibly established summary, and never save it beside the two authored source files.

Test major reveals, escalations, crises, and endings from a short representative prior-conversation excerpt. Assert who knows what, which behavior stage is available, and where player control returns; do not build a synthetic runtime snapshot or state fixture.
