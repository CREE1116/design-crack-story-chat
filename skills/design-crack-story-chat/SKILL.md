---
name: design-crack-story-chat
description: Design, compile, or audit a Crack story-chat project with exactly two authored Markdown sources (`story.md` and `characters.md`) and five final build artifacts. Use when developing a playable story concept; structuring world, world systems (tier scale, threat taxonomy, progression, faction economy), character personality, player role, plot, prologue, opening situation, keyword-book candidates, shortcuts, or final prompt behavior; managing WebP asset directories, Cloudflare Pages hosting, and interactive web showcase gallery; routing rules by lifetime and activation; compressing lore into a compact LLM-reconstructable dialect; compiling a 1,000-character prologue, safe and unsafe 7,000-character integrated-prompt variants, a 1,000-character start prompt, and a keyword-book sheet with 1–5 keywords and at most 400 characters per entry; parsing the player profile from first input; or diagnosing contradictions, agency violations, knowledge leaks, pacing, three-slot collisions, undefined symbols, or prompt-density problems.
---

# Design Crack Story Chat

Author a story chat from two compact canon sources, then publish each Crack field as its own artifact. Keep story/character facts in the two authored files; emit all model-facing system instructions only into the five final build artifacts. Make every fact have one authoritative owner.

## Route the work

Read the following references completely when their condition applies:

- Creating or reorganizing files: [references/file-architecture.md](references/file-architecture.md)
- Developing the premise, conflict, scenes, pacing, choices, relationships, or endings: [references/story-craft.md](references/story-craft.md)
- Defining worlds, characters, relationships, events, branches, secrets, or endings: [references/story-model.md](references/story-model.md)
- Applying community production patterns, system design, or quality heuristics: [references/production-patterns.md](references/production-patterns.md)
- Designing or compressing personality, temperament, archetype, voice, or dynamic dialogue tone: [references/character-personality.md](references/character-personality.md)
- Designing high-precision visual fingerprints, body form, hair 3-elements, and color-bound outfits for prompt reproducibility: [references/character-appearance-guide.md](references/character-appearance-guide.md)
- Designing landscape scenery CGs and staged character-in-scene environment prompts: [references/scene-design-guide.md](references/scene-design-guide.md)
- Writing or revising any model-facing prompt: [references/prompt-writing.md](references/prompt-writing.md)
- Adopting ready-to-use 100% pure system prompt presets by genre: [references/system-prompt-presets.md](references/system-prompt-presets.md)
- Designing HUD, status block, situation tagging, or memory anchors: [references/status-window-guide.md](references/status-window-guide.md)
- Creating the paired safe/unsafe integrated prompts or defining content intensity and escalation boundaries: [references/content-variants.md](references/content-variants.md)
- Shortening an integrated prompt, lore, character sheet, or rules with shared cultural/model knowledge: [references/semantic-compression.md](references/semantic-compression.md)
- Assembling files into a Crack prompt, status window, user-note rule, or media rule: [references/crack-prompt-rules.md](references/crack-prompt-rules.md)
- Designing image directories, Cloudflare Pages hosting, and showcase web gallery: [references/image-assets.md](references/image-assets.md)
- Writing in-prompt media rules, URL schemas, and throttling image output: [references/image-output-rules.md](references/image-output-rules.md)
- Engineering NovelAI V4/V5 prompts, POV camera geometry, S01~S18 emotion & A01~A15 adult pose tag dictionaries: [references/novelai-prompt-engineering.md](references/novelai-prompt-engineering.md)
- Writing release showcase story descriptions, clickable banner links, asset count tables, and creator comments: [references/story-description-guide.md](references/story-description-guide.md)
- Creating, splitting, triggering, or auditing Crack keyword-book entries and trigger directives: [references/keyword-book.md](references/keyword-book.md)
- Designing conversation continuity, relationship progression, time, or long-session recall: [references/conversation-continuity.md](references/conversation-continuity.md)
- Designing the 7-step zoom-in prologue and hot-start bootstrap start prompt: [references/opening-design-guide.md](references/opening-design-guide.md)
- Formatting narration, dialogue syntax, media calls, and output contracts: [references/output-contract.md](references/output-contract.md)
- Finishing any creation, revision, or audit: [references/validation.md](references/validation.md)

Use [assets/story-chat-template](assets/story-chat-template) as the starter bundle. Its only authored files are `story.md` and `characters.md`; it deliberately contains no manifest, state/memory layer, output-contract, generation-rule, content-profile, media-rule, parser, or keyword-book source file. Keep the fifth build artifact even when it records no entries.

## Follow the workflow

1. Inspect existing files before proposing a structure. Preserve authored material and identify contradictions instead of silently choosing a winner.
2. Create or keep only `story.md` and `characters.md` as author-editable intermediate sources. Put world, player-role invariants, events, prologue, opening situation, and optional lore candidates in `story.md`; put identities, behavior, relationships, knowledge, abilities, and optional character-detail candidates in `characters.md`.
3. Establish the experience contract and build the conflict engine before expanding lore. Ensure every major scene changes information, relationship, position, resources, or available choices. Where the premise implies them, define the world systems — tier scale, threat taxonomy, progression, and the economy that gives factions positions — before detailing characters, because character standing is expressed through those systems.
4. Assign each authored fact to exactly one of the two source files. Do not create a manifest, numbered split sources, state/memory files, profile file, keyword-book source directory, output-contract file, generation-rules file, content-profile file, media-rules file, or any other project-level system-prompt intermediate.
5. Model story progression through scenes, events, conditions, effects, secrets, and endings. Do not use relationship score as the only progression mechanism. Treat changing play facts as transient conversation context, never as a required third project layer, dialogue-history artifact, JSON ledger, or assumed Crack API. Do not emit or instruct a separate `Previous History` field.
6. At compilation time, derive observable system rules directly from this skill and the two canon sources. Route each rule once: always-on→both integrated prompts; opening bootstrap→start prompt; conditional detail & trigger directives (kiss, 19+ mature, special combat)→keyword book; player-invoked repeated task or progression command→Crack shortcut. Route by persistence rather than by category: keyword activation is per-turn and unreliable, so an on-stage character's voice belongs always-on even though it reads as reference material, while situational staging and pacing directives belong in the keyword book even though they read as rules. Keyword-book entries are conditional prompt fragments, not encyclopedia entries, and carry directives; an integrated prompt out of budget is usually one whose keyword book holds only lore. Put role boundaries, 6-lock anti-impersonation, NPC active progression, 3-tier input parsing, OOC routing, opening anchoring volume rules, knowledge scope, 4-vector dynamic voice synthesis, response format, SAFE/UNSAFE delta, and visible-status (`Info` HUD) or media rules directly in the final build files. Do not assume a state API, JSON patch, save/load command, or hidden persistence feature. Optimize hidden text for LLM reconstruction, not literary polish; make prologue and all player-visible prose vivid, concrete, and polished.
7. Build exactly five final artifacts: `build/prologue.md`, `build/integrated-prompt-safe.md`, `build/integrated-prompt-unsafe.md`, `build/start-prompt.md`, and `build/keyword-book.md`. Generate both integrated variants from the same two canon sources in one pass; never maintain them as independent stories. Assume Crack presents the player-profile form externally or accepts freeform `*text*` inputs without artificial questionnaires. Put the compact first-input parsing contract only in the final start prompt; never render the form again. Compile the keyword-book file as a registration sheet whose entries are entered separately in Crack. Alongside the five, emit derived production inputs into `build/assets/` — the summary/comment blurb and the asset layout configuration. When the work uses external image hosting, emit the asset directory skeleton (`deploy.py --scaffold`) and interactive web showcase (`index.html`, `styles.css`, `app.js`) for Cloudflare Pages. Record source digests with `scripts/check_freshness.py <project> --stamp` as the last step of every compile.
8. Use Crack's current creator-custom prompt field as the contract: limit each integrated-prompt variant independently to the full 7,000 characters and exclude the personalized player profile, prologue, start prompt, keyword-book entries, shortcut bodies, and any imagined dialogue-history field from both. Treat 7,000 as a ceiling with no minimum; leave margin instead of filling it (target 6,200~6,500). Keep invariant player-role/premise constraints in both variants. Limit prologue and start prompt to 1,000 characters each. These caps count **characters, not tokens**, which inverts the usual token-efficiency instinct: Korean rule text is roughly half the length of equivalent English, so never "optimize" a Korean prompt into English to save budget — cut scope instead. Validate the exact project layout with `scripts/check_project_layout.py`; it enforces two source files plus the exact five-file build.
9. Derive optional, trigger-specific lore, character/ability detail, and situational directives (kiss, 19+ mature, special combat, diplomacy) from candidates in `story.md` or `characters.md`. Each final keyword-book entry has 1–5 keywords, a Crack activation condition (`which setting` + `which value/state`), and at most 400 characters of injected text. Do not create a keyword-book draft source. Crack can load at most three entries together: design each scene around 0–2 intended entries, reserve the third slot, and never make a fourth entry indispensable. Use a naturally utterable, medium-specificity regex trigger; when detail is needed next turn, let narration/NPC speech introduce its cue naturally one turn early. Never use a cue merely as visible trigger bait or to leak a secret.
10. Run the validation reference and every bundled checker: `check_freshness.py` (sources edited since the last compile), `check_project_layout.py`, `check_prompt_length.py`, `check_build.py`, `check_keyword_book.py`, `check_image_assets.py` (roster parity between `characters.md` and the image prompts, plus leading-tag distinctness), `check_symbols.py` (symbols used without a definition), and `check_kb_slots.py` (three-slot load simulated against a written list of realistic scenes). Before trusting any checker that reports success, feed it a case that must fail and confirm it does; a check that silently passes everything ends the search early. Report assumptions, created or changed files, measured counts with the script that produced them, and unresolved author decisions.
11. For high-quality systems, apply [references/production-patterns.md](references/production-patterns.md): prefer qualitative behavior stages over model-managed raw numbers, opening-anchored volume control over static limits, 6-lock agency with active NPC initiative, negativity bias 6-point web, dynamic 4-vector voice synthesis over static speech lists, narrator persona mode switching, explicit event gates, spatial multi-character interaction, natural-language output examples, OOC routing, three-slot keyword-book planning, and late-context tests. Keep final prompt hierarchy to `#→##→one-line rules`; use one term per entity, `IF(condition)→result; impossible→fallback`, prohibition+alternative, one precedence rule, and four-part output contracts (`position/form/omission/update`). Reject undocumented platform folklore.

Before recompiling, check whether the author edited a build artifact directly. Compare artifact and source timestamps, and read any artifact newer than its sources — a rebuild overwrites it and there is nothing to restore from. Reflect what you find back into the two sources first, then compile. Authors do edit build files; treating that as impossible is how their work gets destroyed.

When an author edits `story.md` or `characters.md` after a build, do not patch the artifacts by hand. Run `scripts/check_freshness.py <project>` to see which sections moved and which artifacts each one implicates, then recompile from the sources and re-stamp. Editing a build file directly is how the two layers silently diverge.

Do not compile an artifact while decisions it depends on remain unresolved. Once compilation begins, remove source navigation, author notes, TODOs, metadata, indexes, and inactive material. Regenerate artifacts after either source changes; never maintain build files as second sources of truth. Use compact symbols or emoji when they shorten text without ambiguity, and count their actual Unicode/UTF-16 cost.

## Enforce non-negotiable rules

- Preserve player agency with 6-lock anti-impersonation, but empower active NPC initiative and world evolution so the narrative never stalls.
- Keep knowledge scoped. A character may use only public facts, personal knowledge, witnessed events, and information revealed to that character.
- Treat platform and application safety as external policy. Never write prompts claiming to disable policies, guidelines, or safeguards.
- Treat `unsafe` as a mature-content presentation profile, never as a safeguard bypass. Both variants preserve external policy, player agency, consent ownership, canon, mechanics, knowledge scope, and output syntax.
- Keep canon stable during play. Conversation events may change the current situation, but they do not rewrite authored history or identity without an explicit story mechanism.
- Use stable IDs for characters, locations, events, secrets, flags, and endings. Names are display labels and may change.
- Compress until every remaining string changes reconstruction or output. 1-line 10-slot pipes (`｜`), 3-line timelines, 1-line dictionaries, symbols, terse Korean, or unambiguous hanja are allowed only when actor, condition, result, fallback, scope, cost, and agency remain recoverable.
- Define change limits and transition conditions for numeric values. Pair relationship numbers with qualitative stages that determine behavior.
- Avoid forced continuation. Permit natural pauses, scene endings, rejection, failure, and consequences.
- Do not expose private reasoning. “Inner thoughts” are authored presentation content only when the experience explicitly enables them.

## Deliver concise handoff

Return:

1. the resulting file tree;
2. the important design decisions and assumptions;
3. validation performed and any remaining risks;
4. the next author decision only when it materially changes the design.
