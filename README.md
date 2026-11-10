# Claude Code skills for scientific work

Three skills for [Claude Code](https://claude.com/claude-code), written for the kind of
work that ends in a paper: making slides from results, drawing physics plots with ROOT,
and keeping prose in one author's voice.

| Skill | What it does |
|---|---|
| [`make-slides`](make-slides/) | Builds Google Slides decks from a .pptx template with python-pptx, edits existing decks through the Slides API, gets figures in through a link-shared Drive folder, and checks the result by rendering it to PNGs and looking at them. |
| [`physics-plots`](physics-plots/) | ROOT plots in ATLAS style: limit plots with Brazil bands, 2D exclusion planes, p-value scans, distributions and heatmaps, with a style helper and a save route that produces a cropped vector PDF with embedded fonts plus a clean PNG. |
| [`writing-voice`](writing-voice/) | A method and a linter for writing in a particular author's voice: a profile built from their own paragraphs and corrections, and a checker that reports sentence statistics and flags the habits they avoid. |

Each is a plain Claude Code skill: a `SKILL.md` with YAML frontmatter, plus `scripts/`
and `references/`. The scripts are ordinary Python and can be used on their own.

## Install

Claude Code reads personal skills from `~/.claude/skills/`, and an entry there may be a
symlink, so clone once and link:

```bash
git clone https://github.com/<you>/claude-skills-public.git ~/claude-skills-public
mkdir -p ~/.claude/skills
ln -s ~/claude-skills-public/make-slides    ~/.claude/skills/make-slides
ln -s ~/claude-skills-public/physics-plots  ~/.claude/skills/physics-plots
ln -s ~/claude-skills-public/writing-voice  ~/.claude/skills/writing-voice
```

Skills are read when a session starts, so a new one is picked up on the next session
rather than the current one. Updating is `git pull`. To use only one of them, link only
that directory.

Cloud sessions do not read `~/.claude/skills/`; for those, commit a copy into a project
at `<repo>/.claude/skills/` or enable it on the account.

## Fill in your own details

The skills deliberately contain no account-specific values. Three things need supplying
the first time you use them, and are best recorded in your project's `CLAUDE.md`:

- **`make-slides`**: the Drive id of the deck whose .pptx export is your template, the
  name already written on its footer, and the id of a Drive folder shared as
  *anyone with the link → Viewer*, used as a staging area for figures.
- **`physics-plots`**: the axis titles, process names and symbols of your analysis. The
  recipes use placeholders.
- **`writing-voice`**: a voice profile built from your own writing. Start from
  `writing-voice/references/voice-profile-template.md`, and copy
  `writing-voice/scripts/rules.example.json` to `rules.json` to set the patterns the
  linter flags.

## Dependencies

- `make-slides`: `python-pptx`, `Pillow`, and `pymupdf` for the render check. The Drive
  and Slides connectors are used through Claude Code's MCP connectors.
- `physics-plots`: pyROOT. The ATLAS style macros are loaded from CVMFS when present and
  the module falls back to plain ROOT when they are not.
- `writing-voice`: the standard library only.

## A note on what is not here

These were generalised from a private working copy. The samples, analysis details and
account ids that made them useful in one project were removed rather than anonymised,
which is why the voice profile is a template and the plot recipes name no process. If a
skill looks like it is missing the interesting part, that is the part you supply.

Figures and plots marked internal to a collaboration should not be posted to public URLs.
`make-slides` stages figures in a link-shared Drive folder and `physics-plots` says the
same thing in its own words; both are worth reading before pointing them at unpublished
work.

## Licence

MIT. See [LICENSE](LICENSE).
