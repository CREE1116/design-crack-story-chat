# Validation

Run this checklist before handing off a story-chat design or prompt revision.

## Table of contents

- [Structure](#structure)
- [Experience](#experience)
- [Story craft](#story-craft)
- [Characters and knowledge](#characters-and-knowledge)
- [Story progression](#story-progression)
- [Crack prompt assembly](#crack-prompt-assembly)
- [Keyword book](#keyword-book)
- [Prompt behavior](#prompt-behavior)
- [Conversation continuity](#conversation-continuity)
- [Output contract](#output-contract)
- [Boundary tests](#boundary-tests)
- [Derived documents and tooling](#derived-documents-and-tooling)
- [Handoff evidence](#handoff-evidence)

## Structure

- The authored project contains only `story.md`, `characters.md`, and (after compilation) `build/`.
- `story.md` owns world, player-role, event, opening, and non-character lore facts; `characters.md` owns identity, behavior, knowledge, relationships, and ability facts.
- No intermediate manifest, numbered source, profile, generation-rule, content-profile, output-contract, media-rule, keyword-book, state, memory, or runtime file/directory exists.
- System instructions exist only in the five final build artifacts.
- Changing facts are transient conversation context, never authored canon or a required external API.
- References resolve to defined stable IDs kept inline in the two sources.

## Experience

- The premise, player fantasy, core loop, and story promise agree.
- Fixed player attributes are necessary and clearly disclosed.
- Player customization cannot silently contradict the premise.
- The invariant player role remains in the integrated prompts; the six personalized intake values apply only to the current chat profile.
- Tone and point of view are concrete enough to guide output.

## Story craft

- The one-line premise names the player role, desire, obstacle, and meaningful cost.
- The core loop gives the player a recurring action other than listening.
- External and relationship or internal conflict can each generate scenes.
- Every major scene changes information, relationship, position, resources, risk, or choices.
- Each major scene passes the compact `goal→conflict→outcome→reaction→dilemma→decision` causality check, with a reasonable omission for quiet or fast scenes.
- Quiet scenes are not repeated without new pressure or information.
- Presented choices have materially different consequences and do not block free input.
- Failure produces a consequence or new route instead of ending progression by default.
- Major reveals use evidence and conditions rather than arbitrary exposition.

## Characters and knowledge

- Important traits have observable behaviors and varied dialogue examples.
- Character detail matches the format: compact for ensembles, richer for 1:1 character focus.
- Personality codes and archetypes are optional, non-redundant compression hints mapped to observable behavior.
- Core desire, fear, contradiction, and pressure behavior remain clear without relying only on type codes.
- Explicit behavior and current relationship stage override generic type or trope expectations.
- Character tests cover ordinary interaction, opportunity, challenge, failure, trust, and boundary violation without one catchphrase or strategy repeating everywhere.
- Character goals can drive action without forcing player choices.
- Each secret has owners, reveal conditions, and consequences.
- Characters cannot access author-only or other-character knowledge.
- Relationship stages cause behavioral changes without guaranteeing consent or romance.
- If personality is adaptive, each stage transition has a depicted cause, bounded change, and fixture test; raw model-managed scores are not the sole authority.
- **Every character has a filled appearance section** — no character is left visually undefined. Each one carries reusable fixed anchors (silhouette, hair, eyes, clothing, posture, habitual movement) and excludes changing values such as current emotion, injury, or location.
- **Every character has one identifying feature no one else has**, and the roster was reviewed as a whole rather than one entry at a time. Reduced to silhouette with colour removed, any two characters remain tellable apart; no axis (hair length, build, garment shape, accessory, posture) has all its values bunched together. Where a shared uniform flattens one axis, another axis is widened to compensate.
- Identifying features are hard to remove — a scar, a prosthetic, mismatched eyes, permanent equipment — rather than an outfit that changes between scenes, and each states in one short phrase.
- Features tied to a character's ability, cost, or history are preferred, since appearance then carries setting information at no extra character budget. Not every character needs this, but zero is a missed opportunity.
- Appearance exists in exactly one place. Where image assets are used, their base prompts are derived from that section rather than written separately, so the two cannot drift.
- Required per-character fields — gender, age, tier, appearance, speech register — are checked as a roster table, not one character at a time. Blank cells in a roster of ten or more are invisible during individual review.

## Story progression

- Every major event has explicit triggers, blockers, effects, and repeat behavior.
- At least one valid continuation exists when an expected trigger fails.
- Mandatory beats do not erase meaningful player decisions.
- Failure, rejection, delay, and scene closure are handled.
- Endings have explicit conditions and terminal behavior.
- A short prior-conversation excerpt can enter immediately before each major reveal, escalation, crisis, or ending and reproduce its invariant checks.

World systems, where the premise defines them:

- Each tier in the tier scale gates at least one observable action; no tier exists only as a label.
- The player's starting tier is stated, including an explicit `unmeasured` state if that is the opening condition.
- The recurring threat force is a closed list of four to eight types, each with what it punishes and what counters it; no two types differ only in strength.
- Growth requires a described in-fiction cause and cannot follow from turn count or from the player asking. The ceiling is stated.
- The routine, revenue-producing activity is distinguished from the emergency case, and the cost-bearer of the unprofitable case is named. Faction positions follow from this rather than from temperament.

## Crack prompt assembly

- There are exactly five final artifacts: `build/prologue.md`, `build/integrated-prompt-safe.md`, `build/integrated-prompt-unsafe.md`, `build/start-prompt.md`, and `build/keyword-book.md`.
- The two authoring sources are not treated as upload fields, and no separate system-prompt source exists.
- Both integrated prompts include required system, character, reusable world/story, generation, and output rules and are independently 7,000 characters or fewer.
- SAFE and UNSAFE are regenerated from one canon; their differences are limited to presentation intensity and content handling.
- Canon, mechanics, event outcomes, relationship changes, knowledge scope, agency, consent ownership, and output syntax are identical across variants.
- UNSAFE contains no safeguard-disabling, policy-bypass, unfiltered-mode, or forced-compliance claim.
- Personalized player profile, prologue, and starting situation do not appear in the core artifact; invariant player role and premise constraints do.
- Prologue and start prompt are 1,000 characters or fewer each.
- The product presents the profile form externally; the starting situation does not display or repeat it.
- The starting situation parses the first response into name, age, gender, ability name, ability description, and desired dialogue or situation.
- The first input is parsed into the current chat profile; missing values are not invented.
- The start prompt has a clear path for partial and complete profile intake without creating a separate state channel.
- All six values must be explicit before normal play begins; `none` is a valid explicit opening request.
- Desired dialogue or situation is treated as an opening request, not as an action or line already performed by the player.
- The intake form is never emitted by the model; missing values trigger only a short request for those values.
- Prologue provides lead-in without deciding player action; starting situation stops at the first player-controlled decision.
- Prologue and starting situation connect without duplicating the same incident description.
- The keyword-book registration sheet is the fifth artifact. Current conversation context is not a sixth artifact.
- `scripts/check_project_layout.py STORY_CHAT_DIR` passes and confirms exactly two authored Markdown sources plus the five required regular build files; no obsolete split prompt, system source, or extra build directory remains.
- The working draft targets 6,200–6,500 characters unless the task requires otherwise.
- Character count was measured on the actual final string, including whitespace and Markdown syntax.
- The final check used `scripts/check_prompt_length.py --require-single` on prologue, SAFE integrated, UNSAFE integrated, and start prompt separately.
- The publish artifact contains no source links, indexes, author notes, TODOs, unresolved alternatives, or inactive material.
- Compact symbols and emoji have stable meanings and actually reduce the measured count; no critical rule became ambiguous.
- Hidden source and integrated-prompt prose is optimized for recoverability and length, not literary polish; player-visible prose remains natural.
- Common genre, trope, personality, and narrative labels replace generic explanation only when the target meaning can be reconstructed.
- Definitions and glosses are included in the character count; shorthand that becomes longer after explanation was removed.
- Agency, ability limits, unique canon deviations, secret scope, state transitions, event conditions, and output syntax were never delegated to common knowledge.
- Actual platform-supported variable and media syntax has been verified or clearly left as a placeholder.
- Always-loaded rules are separated from conditionally retrieved canon and events.
- Only present characters, relevant locations, eligible events, scoped secrets, and useful memories are included.
- The same fact does not appear in multiple assembled sections.
- User profile, user notes, in-character input, and OOC requests have distinct handling.
- A fixed-setting conflict does not trigger an unexplained automatic bad ending or punishment.
- Time advances from depicted action rather than response count.
- State icons map to stable state IDs and are not the sole source of meaning.
- A public status window contains no hidden flags, unrevealed secrets, or private reasoning.
- When shortening, agency, current state, ability limits, knowledge boundaries, active triggers, and output syntax were preserved.
- Published prompts do not assume a state API, JSON patch, hidden ledger, save/load command, or injected memory layer. Optional status output only summarizes already established public facts.

## Keyword book

- Keyword-book entries are registered separately and are not appended to the single story-prompt artifact.
- Every entry declares which Crack setting is checked and which value/state permits activation.
- Every entry has 1–5 total keywords, including aliases and spacing variants.
- Every exact injected entry text is 400 characters or fewer, including whitespace and Markdown.
- `build/keyword-book.md` contains registration fields and separately delimited entry texts; it is never pasted whole into either integrated prompt.
- Every entry owns one coherent optional topic.
- Trigger words are specific, include necessary aliases, and avoid common ambiguous words.
- Trigger collisions and overlapping entries were tested.
- Entry text does not duplicate the always-on story payload.
- Current scene facts, agency rules, output syntax, and currently required ability limits remain outside the keyword book.
- Character and ability details may live in keyword-book entries, but first-appearance and first-resolution invariants remain available before activation.
- A keyword first appearing in model output affects the following output, not the output that introduced it.
- Activation setting conditions are not confused with keyword detection scope; user messages and model output can both supply keywords.
- Knowledge scope prevents unrevealed secrets from entering an unauthorized viewpoint.
- Activation does not depend on recursive keyword matching unless Crack explicitly supports it.
- Every planned scene needs no more than three simultaneously activated entries; a fourth entry is never indispensable.
- Each intended keyword is medium-specificity and naturally likely to appear under regex matching, rather than a one-word generic trigger or exact long phrase.
- A needed next-turn entry has a story-natural cue in the preceding NPC/narration output; no cue exists solely to force-load or leak a secret.
- Unknown Crack keyword-book fields beyond the confirmed three-entry cap are marked as unconfirmed rather than invented.
- Entry IDs and aliases are unique across the entire keyword book; simultaneous activation load is reviewed against the three-entry cap.
- Each entry block uses the field names the validator enforces — `activation_setting`, `activation_when`, and `keywords` — with `keywords` as the only bracketed list, and `scripts/check_keyword_book.py build/keyword-book.md` passes on every block.
- The three-slot cap was checked by **simulation, not by inspection**: a list of realistic scenes, each with the words it would plausibly contain, run against every entry's keywords with `scripts/check_kb_slots.py`. Reviewing entries one at a time does not find collisions; only enumerating scenes does.
- Where a simulated scene exceeds three entries, the fix is recorded: entries reordered so the losses fall across different factions or topics, or a keyword narrowed, or an entry merged. Registration order is part of the artifact, not an accident of authoring order.
- When entry order or keywords changed after a prior registration, the handoff lists exactly which entries must be re-registered and states that the order changed. Crack registration is manual; a silent reorder desynchronizes the live product from the build.
- Entries are classified by type and registered in that order — scene-deepening, then roster, then lookup, then filler. Any effectively-always-on entry sits at the bottom, there are at most two of them, and each one's body is expendable: a turn without it still works. `check_kb_slots.py` reports match rate per entry and fails when a high-match entry is registered high.
- Where a set of characters or factions can be named all at once and outnumbers the three slots, a thin roster entry carrying names and affiliations sits above the individual detail entries — or the names live in the integrated prompt. Otherwise the member that loses the slot race has no name loaded at all and gets invented.
- **Reachability:** every proper noun the model is expected to *say* — an alias, an epithet, a place name, a term of art — appears inside loaded text, not only in the canon source. Entry titles, headings, IDs, and field names are registration metadata and are not injected; a name that exists only in a title is unreachable and the model will invent a substitute.

## Prompt behavior

- Rules state actor, condition, behavior, fallback, and visible result where needed.
- No rule claims to disable platform safeguards or policies.
- Priority slogans and duplicate prohibitions have been removed.
- The narrator never invents player dialogue, thoughts, consent, or decisions.
- Uncertain actions are resolved as attempts.
- Initiative rules do not create repeated questions or forced interaction.
- Escalation follows explicit relationship, trust, scene, and player-action conditions; selecting UNSAFE alone never triggers intimacy or violence.
- Hidden chain-of-thought is never requested or displayed.

## Conversation continuity

- Current time, location, scene, active cast, and relationship behavior follow already established conversation facts.
- No separate state-update authority, hidden ledger, memory file, or event log is assumed.
- Derived claims cannot contradict canonical or visible prior facts.
- Unconfirmed player intentions are never treated as completed facts.
- A public status block, if used, is a compact recap rather than persistent memory.

## Output contract

- Block order and delimiters are exact.
- Required, optional, empty, and omission cases are defined.
- Machine-readable output is used only when a confirmed platform parser consumes it.
- Narrative cannot be mistaken for an optional public status block.
- Every symbol or abbreviation that carries assigned meaning is defined in the compiled prompt before its first use, and the definition list matches the symbols actually present in the final string.
- The status block's job is decided explicitly: a decorative recap may be omitted when empty, while a continuity carrier is emitted every response with unchanged fields inherited verbatim.
- No mandatory output block exists only inside an `출력 예` / example region; every required block has its own section stating the requirement and holding the fill-in template.
- Any always-on output requirement that must hold from the first response is also restated in one line in the start prompt, so a detailed opening procedure cannot outrank it.
- The output contract **bans enumerated choice menus explicitly** and names what replaces them. Merely permitting decision points "when needed" reads as permission, and within a few turns every response ends in a numbered list. Where a work deliberately uses menus, options state the action only — a parenthetical gloss on each option assigns the player's motive and is an agency violation regardless of format.
- Response length has a stated target and ceiling, measured on the body excluding the status block.
- Player-visible output cannot contain production vocabulary: the prompt's own abbreviations, section names, `OOC`, variant names, or an invented label above a required block.
- Every emoji and symbol in the status block has a meaning defined in the prompt; none was carried over from a reference format without being re-derived.
- On the first response, fields the player has not yet supplied render as the declared unknown token rather than a guess or an account display name, and no field silently changes value once the real one arrives.
- The start prompt states the ordered bootstrap sequence, what each step settles, what signal starts the first event, and which branch is the default path.
- If relationships are tracked, the status block shows them for characters already met, using the same stage vocabulary the behavior rules gate on.
- Media output has eligibility, count or placement-unit, placement, and fallback rules.
- If media uses a composed external URL pattern, every axis is a closed list written into the prompt, the base address stays a placeholder, a missing combination degrades to omission instead of a broken link, and the experience still reads correctly with no image rendered at all.

## Boundary tests

Test at least these scenarios against the resulting prompts:

1. The player provides only dialogue and no explicit action.
2. The player attempts an action that may fail.
3. The player contradicts a fixed canon fact.
4. An NPC is asked about a secret they do not know.
5. No authored event is currently eligible.
6. A relationship score crosses a stage boundary.
7. The player rejects the intended romantic or narrative direction.
8. A scene ends with no natural question.
9. No media asset matches the scene.
10. A public status block would expose an unknown, hidden, or out-of-scope fact.
11. A user note contradicts a fixed player attribute.
12. A player ignores the presented choices and attempts a valid freeform action.
13. Two NPCs know different versions of the same event.
14. A repeated compliment attempts to farm relationship points.
15. A major scene reaches its turning point and still requires player commitment.
16. A common word accidentally activates an unrelated keyword-book entry.
17. Multiple aliases activate duplicate entries for the same topic.
18. A secret keyword-book entry would activate before its reveal condition.
19. No keyword-book entry matches; the core story payload must still remain coherent.
20. The first input answers the externally presented profile form and establishes the current chat profile without the model repeating the form.
21. The first input omits one field; the model asks only for that field and does not restart the entire form.
22. The requested dialogue or situation would force player action; the model creates an opportunity without speaking or deciding for the player.
23. The same input is run against SAFE and UNSAFE; state changes and outcomes match while presentation intensity differs.
24. An intimate or violent scene lacks its escalation prerequisites; neither variant jumps ahead, and UNSAFE does not treat its profile as consent.
25. A secret is absent from the active context before its reveal condition; neither variant hints from author-only knowledge.
26. A keyword-book entry stops activating; indispensable canon remains stable and omitted detail is not invented as fact.
27. A multi-step calculation or random check is resolved in the declared order or omitted; no hidden arithmetic ledger is assumed.
28. A short prior-conversation excerpt is supplied directly before a reveal or ending; the same invariant holds without replaying the prologue.
29. NPC narration introduces a story-natural medium-specificity keyword; its optional detail is available on the following output, not prematurely.
30. Four keyword-book entries could match one scene; the design remains coherent after reducing the dependency to at most three.

For each test, record expected invariants rather than one exact prose answer. Revise the narrowest owning file when a test fails.

## Derived documents and tooling

Derived material — the summary/comment blurb and the image prompts — is compiled into `build/assets/` from the same two sources as the five artifacts, and is regenerated on every build rather than maintained.

- No derived file was hand-edited. The moment someone edits one directly it becomes a second source of truth for whatever it holds, and nothing downstream will notice.
- `build/` contains exactly the five Crack files plus, at most, the `assets/` directory. A sixth model-facing prompt file is a routing mistake, never a missing artifact.
- `check_image_assets.py` passes: every character in `characters.md` has image prompts and vice versa, slugs are URL-safe, seeds are unique, and no two characters share their leading tags.
- Axis slugs in the image prompts appear in the published closed lists, so the model can actually compose them.
- `check_freshness.py` reports no stale sections; the stamp was refreshed as the last step of the compile. Sources edited after a build leave no visible trace — the build still passes every other check while the published prompt plays an outdated character.

- Every claim in a summary or promotional document was checked against the artifact that actually ships. A setting that exists only in the canon source is not "in the build," and a summary that lists it is wrong.
- Counts stated anywhere — cast size, composition ratios, entry totals, character lengths — were produced by a script, not by hand. Hand counts in this workflow have been wrong.
- **Verification scripts get a negative control.** Before trusting a checker that reports "no problems," feed it a case that must fail and confirm it fails. A check that silently passes everything is worse than no check, because it ends the search. One real instance: a membership test written against a tuple of whole strings instead of a substring search reported a clean result while hiding three mismatches.
- Scripts that call an external API were exercised against a mock that returns the real error shapes, not only success. Anything the mock cannot cover — actual hardware, drivers, live rendering — is reported as unverified rather than as tested.
- Platform behavior nobody has observed in the real Crack UI is listed as unconfirmed: whitespace and indent rendering in the status block, emoji rendering, external image loading, and the true set of activation-setting values.

If a world system was queued for promotion into the integrated prompt at a later arc, that queue is recorded with what must be cut to make room.

After any compression pass:

- Every rule in the pre-compression version was written out as a fingerprint — a set of words unique to that rule — and checked mechanically against the compressed text. Reading the result over is not a check; a deleted rule leaves no trace that draws the eye.
- Partial fingerprint misses were resolved by hand as either rephrasing or loss, not auto-passed.
- Agency, consent, and prohibition boundaries were compressed **less** than descriptive material. These are where the model falls back when a situation is ambiguous, so a few saved characters are never worth added interpretive room.
- Freed budget was not fully spent. Compression exists to create margin, and refilling it returns the project to where it started.

## Handoff evidence

Report:

- files created, removed, split, merged, or renamed;
- assumptions made because Crack platform syntax was unavailable;
- source-of-truth conflicts found and how they were resolved;
- boundary tests run and failed invariants;
- measured counts, with the script that produced them;
- what was verified against a mock versus against the real platform or hardware;
- remaining author decisions that materially affect the experience.
