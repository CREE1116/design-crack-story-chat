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

Write the UNSAFE delta as an imperative directive ("묘사한다"), not a permission grant ("묘사할 수 있다"). 실측: 한 실전 프로젝트에서 "노골적으로 묘사할 수 있다"로 둔 문장은 그 문서 다큐 서술 톤에 눌려 요약으로 흘렀고, 명령형으로 바꾸고서야 매 턴 반영됐다. UNSAFE는 이미 켜진 스위치를 알리는 문장이지, 켤지 말지 모델이 재량으로 판단하게 두는 문장이 아니다.

State non-negotiable hard limits inside the UNSAFE delta itself, in the built file — do not leave them implicit in this reference or assume the base model supplies them. At minimum: no sexualization of a minor-coded character, no sexual depiction of a real person, no glorifying non-consensual violence as spectacle (aftermath/consequence framing only). These apply to both variants without exception and sit next to the delta, not buried in `story.md`/`characters.md` canon where a rebuild could drop them.

## Turn-budget exception for scene-level intensity

A world/system contract that compresses many turns of story time into one output (a simulation clock, a multi-year timeskip, a montage format) will silently summarize or skip any scene-level content — sex, torture, a single conversation — no matter how graphic the delta's wording is, because the pacing rule outranks the intensity rule by default. Wording alone does not fix this.

If UNSAFE is meant to render such a scene in full, the delta must explicitly suspend the compression/timeskip rule for that turn and dedicate the turn's entire output budget to the one scene, then state when normal pacing resumes (e.g. "다음 턴부터 재개"). Confirmed cheap: adding this exception to one project's UNSAFE delta cost ~190 characters against a 7,000 cap — budget is not the constraint, remembering to write the exception is.

## Pair review

1. Confirm the common headings and stable IDs match.
2. Confirm the only semantic difference is presentation intensity.
3. Measure each final string, including whitespace and Markdown, at ≤7,000.
4. Run the same input through both: state changes and outcomes must match.
5. Verify neither file impersonates the player, leaks secrets, or claims to disable safeguards.
