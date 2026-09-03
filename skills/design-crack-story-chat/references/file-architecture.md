# File architecture

## Contract

Keep the author project intentionally small. Its only editable intermediate files are the story source and character source. System prompts are created directly in the final build and never kept as project source files.

```text
story-chat/
├── story.md
├── characters.md
└── build/                         # generated; exact final files only
    ├── prologue.md                # ≤1,000 chars
    ├── integrated-prompt-safe.md  # ≤7,000 chars
    ├── integrated-prompt-unsafe.md # ≤7,000 chars
    ├── start-prompt.md            # ≤1,000 chars
    ├── keyword-book.md            # one registration sheet; entry text ≤400 chars
    └── assets/                    # derived production inputs; never pasted into Crack
        ├── story-description.md   # story description for publish page (Markdown supported)
        ├── summary-comment.md     # plain-text listing/comment blurb (Markdown not supported)
        ├── image-prompts.md       # human-readable prompt sheet
        ├── prompts.json           # machine form of the same content
        └── build-stamp.json       # source digests recorded at compile time
```

Do **not** create intermediate `manifest`, `world`, `player`, `prologue`, `story-design`, `generation-rules`, `content-profiles`, `output-contract`, `media-rules`, `runtime`, or `keyword-book` files/directories. Those splits can clarify a large software system, but they are needless authoring debris for this Crack workflow.

`build/` is generated output, not a third source. It may be absent before the first compilation. After compilation its **files** are exactly the five above and nothing else.

`build/assets/` is the one permitted subdirectory. It holds **derived production inputs** — material compiled from the two sources that is never pasted into a Crack prompt field and never reaches the model as instructions. Core types include: release showcase descriptions (`story-description.md`, `summary-comment.md`), prompt sheets, and design logs. Anything model-facing goes in the five artifacts; if something feels like it needs a sixth prompt file, it is a routing mistake, not a missing artifact.

Derived does not mean optional. These files are regenerated on every compile exactly like the five, and hand-editing one makes it a second source of truth for whatever it contains. An image prompt sheet takes its appearance text from `characters.md`; a summary blurb takes its claims from the compiled artifacts, not from memory.

`scripts/check_project_layout.py` ignores dot-prefixed entries at the project root, so a hidden tooling directory such as `.agents/` (including a synced copy of this skill) or `.git/` does not fail the layout check. Everything visible at the root other than `story.md`, `characters.md`, and `build/` does fail it.

Authored material that is neither canon nor generated — test fixtures such as a scene list for the three-slot simulation, hosting notes, scratch work — goes in a dot-prefixed directory such as `.assets/`, which the layout check ignores. The distinction is authorship, not subject: a scene fixture someone writes by hand lives in `.assets/`, while an image prompt sheet the compiler produces lives in `build/assets/`.

Generated image assets themselves (the PNG files) belong in neither place. They are large binaries with their own hosting lifecycle — keep them outside the project or in an ignored directory, and let the deploy tooling move them.

## Ownership

| Source | Owns | Must not contain |
|---|---|---|
| `story.md` | premise, invariant player role, world canon, factions/locations, hard limits, conflict loop, arcs/events/secrets/endings, prologue draft, first situation draft, optional non-character lore candidates | narrator instructions, parser wording, OOC policy, output syntax, SAFE/UNSAFE directives |
| `characters.md` | character IDs/names, roles, goals/fears/contradictions, observable behavior, speech, knowledge, relationships, abilities/costs/limits, optional character or ability detail candidates | narrator instructions, output syntax, keyword-book UI metadata |
| `build/*` | all player-facing text and all model-facing system instructions | author notes, source paths, TODOs, unresolved choices |
| live conversation | current profile, scene facts, prior outcomes, and any visible status | a third source, assumed API, or hidden ledger |

One fact still has one owner: world/event/player-role facts belong in `story.md`; identity/behavior/ability facts belong in `characters.md`. Reference stable labels across the two files instead of copying a fact. Use natural Korean names or hyphenated labels; never use dotted programmer namespaces.

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
### `사건-첫교전`
- trigger / blocker / consequence / player decision point:

## Opening material
### Prologue draft
[player-visible prose only]
### First situation draft
[place, present cast, visible problem, first player-controlled opening]

## Optional lore candidates
### `키워드-마도학`
- Topic and factual detail worth loading only after a relevant mention:
- Suggested names/aliases (1–5):
```

The prologue and first situation are fiction drafts, not hidden instructions. The compiler turns them into their separate final fields and adds the required first-input parser to the final start prompt itself.

### `characters.md`

Use one self-contained section per character:

```markdown
# Characters
## 인물 이름 「이명/직책」
- Role / current goal / fear or cost / contradiction:
- Behavior: relaxed→; pressure→; trust→; boundary breach→:
- Speech: register, vocabulary, 2–5 varied sample lines:
- Knowledge: public / private / false belief / unknown:
- Ability: effect / activation / cost / hard limit / failure:
- Relationships: target names and current qualitative stage:
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
4. Regenerate both integrated variants whenever either source changes; never hand-edit one variant as a separate source of truth.
5. Run `python scripts/check_project_layout.py STORY_CHAT_DIR` after compiling. Use `--allow-unbuilt` only before the first build.
6. Upload the prologue, one selected integrated variant, and start prompt to their matching Crack fields. Register keyword-book entries individually from the fifth file.

## Stable Names and Identities

Keep character and world definitions inline where their canon lives. Use clear, unambiguous display names (e.g. `심가을 「測候」`, `헌터협회 본부`). Do not reuse an identity after release.

## Change discipline

Before changing a fact, find its owning one of the two source files and all stable-ID references. Classify the change as editorial, canon/behavioral, or continuity-impacting. For the last type, update the final prompt's visible handling and test it against a representative prior conversation; never write current play values back into `story.md` or `characters.md`.
