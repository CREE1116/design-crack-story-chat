# Safe/unsafe integrated-prompt pair

## Output contract

Always build both files together:

- `build/integrated-prompt-safe.md` — restrained, non-explicit presentation.
- `build/integrated-prompt-unsafe.md` — higher-intensity adult, violence, or dark-material presentation within the project's boundaries and external policy.

Each file is independently at most 7,000 characters. `unsafe` never means a policy bypass, unfiltered mode, or a replacement for consent.

## No profile source file

`story.md` and `characters.md` own fiction only. Do not create `content-profiles.md`, `safe.md`, `unsafe.md`, or another intermediate rules file.

At build time, compile the common canon and reusable system contract directly into both final files, then write one compact presentation delta into each.

```text
story.md + characters.md + skill contract
              ├─ common core + SAFE delta   → integrated-prompt-safe.md
              └─ common core + UNSAFE delta → integrated-prompt-unsafe.md
```

Never hand-maintain the two built prompts as separate stories. Rebuild both after either source changes.

## Invariants

The variants must match on:

- canon, player role, character goals/personality/knowledge, abilities and limits;
- player ownership of dialogue, thought, action, desire, consent, and decisions;
- event triggers, outcomes, relationship stages, secrets, failure routes, and endings;
- OOC handling, optional visible-status syntax, and output syntax;
- natural pauses, rejection, scene closure, and player opt-out.

If an intensity choice changes a result, creates consent, advances a relationship, or reveals information, the pair is invalid.

## Directly compiled deltas

SAFE should prioritize emotional consequence over graphic detail: violence is result-focused, intimacy can fade or summarize, and profanity/horror detail stays restrained without deleting the actual conflict.

UNSAFE may increase sensory density and directness for permitted adult/violent/dark material. It must still require established situation, relationship stage, and explicit player action where applicable; silence, hesitation, or selecting UNSAFE never supplies consent. Do not write `정책 무시`, `필터 우회`, `검열 해제`, `무조건 수행`, `unfiltered`, or equivalent bypass language.

## Pair review

1. Confirm the common headings and stable IDs match.
2. Confirm the only semantic difference is presentation intensity.
3. Measure each final string, including whitespace and Markdown, at ≤7,000.
4. Run the same input through both: state changes and outcomes must match.
5. Verify neither file impersonates the player, leaks secrets, or claims to disable safeguards.
