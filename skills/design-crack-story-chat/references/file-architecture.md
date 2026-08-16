# File architecture

## Contract

Keep the author project intentionally small. Its only editable intermediate files are story and character canon. System prompts are created directly in the final build and never kept as project source files.

```text
story-chat/
├── story.md
├── characters.md
└── build/                         # generated; exact final files only
    ├── prologue.md                # ≤1,000 chars
    ├── integrated-prompt-safe.md  # ≤7,000 chars
    ├── integrated-prompt-unsafe.md # ≤7,000 chars
    ├── start-prompt.md            # ≤1,000 chars
    └── keyword-book.md            # one registration sheet; entry text ≤400 chars
```

Do **not** create intermediate `manifest`, `world`, `player`, `prologue`, `story-design`, `generation-rules`, `content-profiles`, `output-contract`, `media-rules`, `runtime`, or `keyword-book` files/directories. Those splits can clarify a large software system, but they are needless authoring debris for this Crack workflow.

`build/` is generated output, not a third source. It may be absent before the first compilation. After compilation it contains exactly the five regular files above and nothing else.

`scripts/check_project_layout.py` ignores dot-prefixed entries at the project root, so a hidden tooling directory such as `.agents/` (including a synced copy of this skill) or `.git/` does not fail the layout check. Everything visible at the root other than `story.md`, `characters.md`, and `build/` does fail it.

Production assets that ship alongside the story chat but are not story-chat sources — image-generation prompts, an asset roster, hosting notes — are neither canon nor build output, so they do not belong at the project root and would fail the layout check there. Keep them in a dot-prefixed directory such as `.assets/`. Facts they depend on still live in the two sources: an image prompt sheet derives its appearance text from `characters.md` rather than becoming a second place where a character's look is defined.

## Ownership

| Source | Owns | Must not contain |
|---|---|---|
| `story.md` | premise, invariant player role, world canon, factions/locations, hard limits, conflict loop, arcs/events/secrets/endings, prologue draft, first situation draft, optional non-character lore candidates | narrator instructions, parser wording, OOC policy, output syntax, SAFE/UNSAFE directives |
| `characters.md` | character IDs/names, roles, goals/fears/contradictions, observable behavior, speech, knowledge, relationships, abilities/costs/limits, optional character or ability detail candidates | narrator instructions, output syntax, keyword-book UI metadata |
| `build/*` | all player-facing text and all model-facing system instructions | author notes, source paths, TODOs, unresolved choices |
| live conversation | current profile, scene facts, prior outcomes, and any visible status | a third source, assumed API, or hidden ledger |

One fact still has one owner: world/event/player-role facts belong in `story.md`; identity/behavior/ability facts belong in `characters.md`. Reference stable IDs across the two files instead of copying a fact.

## What belongs in the two sources

### `story.md`

Use compact factual sections such as:

```markdown
# Story
## Core
- Premise / player role / central pressure / meaningful cost:
- Tone and core loop:

## World canon
- Hard rules, institutions, locations, history needed in play:

## Story engine
### `event.example`
- trigger / blocker / consequence / player decision point:

## Opening material
### Prologue draft
[player-visible prose only]
### First situation draft
[place, present cast, visible problem, first player-controlled opening]

## Optional lore candidates
### `kb.example`
- Topic and factual detail worth loading only after a relevant mention:
- Suggested names/aliases (1–5):
```

The prologue and first situation are fiction drafts, not hidden instructions. The compiler turns them into their separate final fields and adds the required first-input parser to the final start prompt itself.

### `characters.md`

Use one self-contained section per character:

```markdown
# Characters
## `char.example` — Display Name
- Role / current goal / fear or cost / contradiction:
- Behavior: relaxed→; pressure→; trust→; boundary breach→:
- Speech: register, vocabulary, 2–5 varied sample lines:
- Knowledge: public / private / false belief / unknown:
- Ability: effect / activation / cost / hard limit / failure:
- Relationships: target IDs and current qualitative stage:
- Optional detail candidate: topic, factual detail, suggested names/aliases (1–5)
```

Use familiar archetypes or personality labels only as shorthand for behavior. The behavior rule wins if a label and observed characterization differ.

## Direct-to-build system compilation

The skill, not a project source file, supplies the reusable system contract. At build time, write these directly into the relevant final artifact:

| Final artifact | Directly compiled system material |
|---|---|
| `integrated-prompt-safe.md` | always-on role/agency boundary, anti-impersonation, scoped knowledge, initiative/pacing/consequence rules, OOC routing, response contract, optional visible-status rule, safe presentation delta |
| `integrated-prompt-unsafe.md` | same invariant contract and structure, with only a compliant mature/high-intensity presentation delta |
| `start-prompt.md` | first-input parser plus opening situation and rules useful only in the conservative 10-turn bootstrap horizon; ask only for missing fields; never repeat the external form |
| `keyword-book.md` | actual Crack start-setting activation selection, 1–5 keywords, and ≤400-character injected text for each selected source candidate; optional separately labeled shortcut registrations when requested |
| `prologue.md` | vivid, polished player-visible prose only; no hidden system wording unless the platform requires it |

Only compile confirmed Crack UI setting/value pairs into keyword-book entries. If they are unknown, keep the factual candidate in its story/character source and omit that final entry until confirmed; do not create a third metadata draft. A requested user shortcut is a bounded prompt invoked by the player, not an always-on rule or keyword-book entry. Keep the physical five-file contract by recording its UI registration block in `build/keyword-book.md`, clearly outside the keyword-book entry blocks.

## Conversation-continuity boundary

There is no runtime deliverable or assumed Crack state API. Current profile, scene facts, relationships, and prior outcomes live only in the conversation that generated them. Do not create a state schema, JSON patch, event log, memory file, save/load command, or hidden persistence contract. Add a compact **player-visible** status block to the final prompt only when the story benefits from one; it summarizes already established facts and never becomes an independent source of truth.

## Build discipline

1. Edit only `story.md` and `characters.md`.
2. Resolve canon conflicts and mark only genuine author decisions as unresolved.
3. Compile all five final artifacts in one pass from those two files plus this skill's reusable rules.
4. Regenerate both integrated variants whenever either source changes; never hand-edit one variant as a separate canon.
5. Run `python scripts/check_project_layout.py STORY_CHAT_DIR` after compiling. Use `--allow-unbuilt` only before the first build.
6. Upload the prologue, one selected integrated variant, and start prompt to their matching Crack fields. Register keyword-book entries individually from the fifth file.

## Stable IDs

Keep IDs inline where their canon lives. Recommended prefixes: `char.`, `loc.`, `faction.`, `arc.`, `scene.`, `event.`, `goal.`, `secret.`, `flag.`, `ending.`, and `kb.`. Do not reuse an ID after release; display names may change without changing an ID.

## Change discipline

Before changing a fact, find its owning one of the two source files and all stable-ID references. Classify the change as editorial, canon/behavioral, or continuity-impacting. For the last type, update the final prompt's visible handling and test it against a representative prior conversation; never write current play values back into `story.md` or `characters.md`.
