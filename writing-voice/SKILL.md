---
name: writing-voice
description: Write or rewrite prose in a particular author's voice, using a stored voice profile of their own paragraphs, the corrections they have made to earlier drafts, and a linter that reports sentence statistics and flags the patterns they do not use. Use this whenever the user asks to draft, rewrite, polish, shorten, "make it sound like me" or "write in my voice" for a paper, abstract, note, report, talk text or email that goes out under their name, and whenever they say a draft is convoluted, informal, too rhetorical, too long or does not sound like them. Also use it when polishing text written earlier in the same session.
---

# Writing voice

Matching someone's writing is not a matter of instructions alone. What works is a small
profile built from their own text, kept in the project and corrected over time, plus a
linter that catches the handful of habits a model falls back into.

This skill is the method and the tooling. The profile itself is personal, so the one in
this repository is a template; the first job in a new project is to fill it in.

## How a model gets it wrong

Two failure modes, in opposite directions, and the second usually follows an attempt to
fix the first.

**Unguided**, drafts drift into rhetoric: long multi-clause sentences, "X, not Y"
contrasts, fragments for effect, dramatic colons, a slogan where a result should be. Most
authors of formal prose read this as convoluted and informal.

**Over-corrected**, drafts become a staccato of ten-word sentences that state results
without connecting them, and understate what was achieved. That reads as choppy and oddly
modest.

Aim between the two: clear sentences of natural length, linked into paragraphs that carry
one line of thought, with the significance of the result stated plainly. The linter
measures both failure modes, which is the point of it.

## Setting up a profile for an author

Build `references/voice-profile.md` from `references/voice-profile-template.md` and fill
it in from real text. It takes one session and pays for itself immediately.

1. **Collect five to ten paragraphs they wrote**, verbatim, with sources: a thesis
   chapter, the summary of a paper, an abstract. Prefer finished published text over
   drafts. Keep them in the profile under their own heading.
2. **Measure them.** Run `voice_check.py` over the corpus and write the numbers into the
   profile: median sentence length, 90th percentile, longest, share of sentences under ten
   words. These are the target, and they are more useful than any adjective.
3. **Write down the conventions** that are not negotiable: spelling variant, how figures
   and sections are referenced, units, which names are used for what, whether "we" is
   allowed.
4. **Keep before-and-after pairs.** Every time the user corrects a draft, save the
   rejected version and their replacement as a pair. After a handful of these the pairs
   teach more than the rules do, because they show how far to go.
5. **Copy `scripts/rules.example.json` to `scripts/rules.json`** and edit it so the
   flagged patterns are the ones this author actually avoids. The checker loads
   `rules.json` if it exists and falls back to the example.

Store the finished profile with the project, not here, if the samples are not yours to
publish.

## Procedure for a piece of writing

1. If the register is in doubt, read the samples in the profile. Ten minutes with them is
   worth more than any set of rules.
2. Draft. Say what was done, what was found and what it means, in that order. Name a
   quantity before using it, give the reason with the result, and let each sentence pick up
   something from the one before.
3. Run the checker:
   `python3 scripts/voice_check.py <file.tex|.md|.txt> [--rules scripts/rules.json]`
   It reports sentence statistics, long sentences, fragments, a choppiness measure and
   every pattern flag, each with a line number. It is a linter, not a judge: fix what it
   flags unless there is a reason not to.
4. Reread once as the author: would they send this under their name to a referee? Remove
   anything that sounds like it is trying to impress.
5. When handing the text over, give one line of statistics (median sentence length, longest
   sentence) and list anything deliberately left as is.

## What the linter checks

- **Sentence length**: count, median, 90th percentile, maximum, and every sentence above
  the limit in the rules file.
- **Choppiness**: share of sentences under ten words and the longest consecutive run of
  them. Three in a row usually means the draft has been over-corrected.
- **Fragments**: sentences under four words.
- **Rhetoric**: a configurable word list ("remarkably", "it turns out", "what matters").
- **Fragment openers**: sentences starting "Not ...", "Because ...", "Nor ...".
- **Spelling variant**: a configurable list, e.g. American spellings in British text.
- **Naming**: project-specific regexes with the reason attached, which is where a
  recurring correction should end up so it is never repeated.
- **Punctuation habits**: em-dashes, semicolons, "X, not Y" contrasts, questions in prose.
- **Placeholders**: `\todo`, TBD, "to be added" left in a draft someone is about to read.

It strips LaTeX before counting, so it can be run on a `.tex` source directly.

## Defaults that suit most formal scientific prose

These are a starting point for a profile, not rules for every author:

- Declarative sentences of natural length. A sentence may carry a reason, a consequence or
  a qualification; what reads badly is stacking all three. If a sentence cannot be read
  aloud in one breath, split it. If two neighbouring sentences share a subject and a
  thought, join them.
- Paragraphs are arguments, not lists of findings. Open with the point, develop it, close
  with what follows. Connect sentences by carrying a noun or an idea forward, and only
  secondarily with connector words.
- Formal, confident, not inflated. Results are "found to be", "consistent with", "in good
  agreement with", with the number in the sentence that makes the claim. State plainly
  what is new when it is true, and do not bury the main result in a subordinate clause.
- No decoration: no adjectives doing the work of numbers, no verdicts announced ahead of
  the evidence. Give the number, then the interpretation, in measured words.
- Sections open by saying what they do. Introductions end with a structure paragraph.
- No placeholders in a draft someone will read. Leave a note in the chat instead.

## Files

- `references/voice-profile-template.md`: the profile to fill in per author.
- `scripts/voice_check.py`: the linter.
- `scripts/rules.example.json`: example pattern rules, copy to `rules.json` and edit.
