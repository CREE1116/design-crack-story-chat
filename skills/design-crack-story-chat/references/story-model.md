# Story model

## Table of contents

- [Model the experience before the lore](#model-the-experience-before-the-lore)
- [Distinguish story units](#distinguish-story-units)
- [Model world systems](#model-world-systems)
- [Gate the cast by arc phase](#gate-the-cast-by-arc-phase)
- [Define characters through behavior](#define-characters-through-behavior)
- [Model relationships with stage and value](#model-relationships-with-stage-and-value)
- [Define events as conditions and effects](#define-events-as-conditions-and-effects)
- [Scope knowledge and secrets](#scope-knowledge-and-secrets)
- [Preserve player agency](#preserve-player-agency)
- [Design endings](#design-endings)

## Model the experience before the lore

Define these first:

- **Premise:** what situation the player enters.
- **Player fantasy:** what the player gets to be or do.
- **Core loop:** observe, decide, act, face consequences, and discover.
- **Story promise:** the emotional or dramatic change the experience should deliver.
- **Freedom boundary:** what is authored, what is simulated, and what the player controls.

World detail that does not affect a decision, consequence, character, or reveal is optional.

## Distinguish story units

| Unit | Purpose | Example |
|---|---|---|
| Arc | long dramatic movement | strangers become trusted partners |
| Scene | bounded dramatic situation | awkward first meeting in the café |
| Beat | change within a scene | the misunderstanding becomes clear |
| Event | condition-driven occurrence | rival arrives after trust reaches stage 2 |
| Secret | hidden fact with knowledge scope | the café is close to bankruptcy |
| Ending | terminal or resumable outcome | partnership, separation, unresolved |

Do not encode an entire story as a mandatory scene list. Mark which units are required, optional, repeatable, interruptible, or mutually exclusive.

## Model world systems

Power-fantasy, survival, professional, and competitive premises need a few world systems defined before characters, because character standing is expressed through them. Define a system only when it changes a decision, a scene, or someone's leverage.

### Tier system

Use one scale for both characters and threats so any pairing is immediately readable.

- Number of tiers, and what each tier can **observably** do.
- Population distribution, so rarity means something.
- How a tier is measured and assigned, and whether it can change.
- The player's starting tier — including `unmeasured` as a valid state.

A tier that labels strength but never forbids an action is decoration. Every tier must gate something: a place one may not enter, a threat one may not engage, a door that does not open.

### Threat taxonomy

A recurring antagonist force needs a closed list of types, not one generic monster.

```markdown
## `threat.example`
- Silhouette: what the player sees first
- Behavior: how it attacks or spreads
- Punishes: which player mistake it exploits
- Counterplay: what actually works
- Signal: what its presence tells the player about the situation
- Difficulty band: tier scale reference
```

- Use four to eight types. Fewer and encounters repeat; more and the model stops keeping them distinct.
- Vary them along an axis that **changes player behavior** — numbers, durability, mobility, deception, area denial — not along a damage number.
- Every type needs a `Punishes` and a `Counterplay`. A type without those is a reskin.

### Progression system

- Name what grows and what does not.
- Require a described in-fiction cause for growth. Growth must never follow from turn count or from asking.
- Separate axes when possible — capacity versus skill — so early progress is legible without breaking tier balance.
- State the ceiling explicitly. Whatever is not forbidden will eventually be granted on request.

### Economy and motive

Answer plainly: why does anyone do this for a living?

- The routine activity that produces revenue.
- The emergency or failure case.
- Who absorbs the cost of the case that pays nothing.

This is what gives factions positions instead of flavors. Without it every faction collapses into "the honorable one" and "the arrogant one," and the model will improvise motives that contradict canon.

### Route world systems by arc position

Full tables live in the canon source. The integrated prompt carries only what the model needs **before the current arc reaches it**; the rest waits in the keyword book.

Re-check this routing whenever the arc moves. A system that is offstage during the opening becomes always-on later, and its budget must be reclaimed from opening-only material rather than added on top of a prompt already at its ceiling. Record which systems are queued for promotion in the handoff.

## Gate the cast by arc phase

When a work spans several phases — eras, chapters, escalation stages — state **which characters exist in each**, as a closed list rather than a guideline.

```text
국면A: 인물 01~14만 등장 가능. 기본 생활·임무.
국면B: 인물 01~22만 등장 가능. 집단 이벤트.
국면C: 인물 01~27만 등장 가능. 대규모 시가전.
```

This does three jobs at once. It answers "who can walk in right now," it keeps the always-on prompt small because only the current phase's cast needs seeds, and where images are addressed by the same index it bounds the asset list too.

Pair it with a knowledge rule, or characters will act on things that have not happened yet:

```text
등장인물은 현재 국면 이후 사건을 선지식처럼 행동·발언×.
```

That failure is easy to miss in review and obvious in play — a character who is worried about a disaster three phases away reads as the author leaking the outline.

## Define characters through behavior

For each important character, specify:

```markdown
## 인물 이름 「이명/직책」

### Dramatic function
- Role in the player's experience:
- Current goal:
- Fear or cost of failure:

### Personality compression
- Common type or archetype tags (optional):
- Core desire / core fear / self-image:
- Contradiction:

### Appearance
- Fixed visual anchors reusable across scenes: silhouette, clothing, hair, eyes, hands, posture, habitual movement
- Visible traces of the ability or temperament, if any
- Excludes changing values such as current emotion, injury, or location

### Presentation
- Speech register:
- Repeated verbal habits to avoid:
- Sample lines:

### Behavioral model
- When relaxed:
- When uncertain:
- When challenged:
- When trust increases:
- When a boundary is crossed:
- Strategy after failure:

### Knowledge
- Public knowledge:
- Private knowledge:
- False belief:
- Information never known initially:

### Relationships
- 상대 인물명: baseline, tension, desired change
```

Use familiar type or archetype labels only as compression hints. Operational behavior carries the real instruction. Resolve conflicts as `canon/current state/behavior > desire/fear/contradiction > relationship stage > tags > examples`.

## Model relationships with stage and value

Use a numeric value for gradual change and a qualitative stage for behavior.

```markdown
| Stage | Range | Available behavior |
|---|---:|---|
| guarded | -20–20 | formal interaction, avoids disclosure |
| curious | 21–40 | prolongs conversation, asks personal questions |
| trusting | 41–65 | shares minor vulnerabilities, requests help |
| close | 66–85 | initiates private meetings, offers protection |
| committed | 86–100 | makes costly long-term choices |
```

Define per-turn change caps, exceptional events, decay if any, and stage-transition conditions. A score alone must not force romance, consent, forgiveness, or irreversible decisions.

## Define events as conditions and effects

Use this form:

```markdown
## `event.example`

- Purpose: why this event exists
- Trigger: explicit boolean conditions
- Blocked when: conditions preventing it
- Priority: critical | high | normal | ambient
- Repeat: once | once-per-arc | repeatable
- Cast: character IDs
- Entry: observable scene opening
- Player opportunity: meaningful choice or action space
- Effects: flags, relationship deltas, time, inventory, knowledge
- Follow-ups: event IDs enabled or disabled
- Failure handling: consequence without railroading
```

Triggers should depend on authoritative state, not vague phrases such as “when appropriate.” Use “when appropriate” only for low-impact flavor.

## Scope knowledge and secrets

For every secret, define:

- the true fact;
- characters who know it;
- characters holding false beliefs;
- evidence that can reveal it;
- reveal condition;
- state flag set on discovery;
- consequences of discovery.

Separate author-visible truth from character-visible knowledge. A narrator may hint at a secret only if the selected point of view permits it.

## Preserve player agency

The narrator may:

- describe sensory information and external consequences;
- resolve an attempted action using established rules;
- portray involuntary immediate reactions sparingly when the premise requires them;
- ask for a decision when multiple meaningful paths remain.

The narrator must not:

- choose the player's intent;
- invent player dialogue, thoughts, attraction, consent, or moral judgment;
- convert an attempt into success without resolving uncertainty;
- close a major branch before the player can respond.

Represent player input as an attempted action when outcome is uncertain.

## Design endings

For each ending, define:

- required and forbidden flags;
- relationship or resource thresholds;
- final irreversible choice, if any;
- short-term outcome and thematic resolution;
- whether play ends, continues in epilogue, or returns to free play.

Include failure and unresolved outcomes when the story permits them. Do not force a positive ending through hidden positivity bias.
