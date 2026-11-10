---
name: make-slides
description: Build and edit Google Slides decks from a .pptx template, with a python-pptx deck builder, the Slides API recipes for editing a deck in place, figure insertion through a link-shared Drive folder, and a render-and-look verification loop. Use this whenever the user asks for slides, a deck, a talk or a presentation, asks for slides summarising a paper or a note, or asks to add, restyle, recolour, reformat or fix slides in an existing Google Slides deck. Also use it when they ask to put a figure or a plot on a slide, change a deck's colours, or check a deck for overflowing text and overlapping figures.
---

# Make slides

This skill builds decks on a Google Slides template the user already owns,
and edits them afterwards through the Slides API. It assumes a template
with a title layout, a section-header layout and a title-and-body layout,
and a footer carrying a name, a date and a page number.

Read `references/templates.md` before building anything: it holds the
palette scheme, the layout order, the type sizes and the slide
conventions, and it tells you what to fill in for a template you have not
seen before. Read `references/google-slides.md` before touching a deck in
Drive: it holds the figure-insertion route, the API pitfalls and the
verification loop.

## Configure it for this user, once

Three things are specific to whoever is using this and are not in the
repository:

1. **The reference deck** whose .pptx export is the template. Ask for a
   Drive link, or list their decks and confirm the title before using one.
2. **The footer name** already written on the template's layouts, and the
   name they want on the deck.
3. **A Drive folder shared as anyone-with-the-link → Viewer**, used as a
   staging area for figures. See `references/google-slides.md`.

Record them in the project's `CLAUDE.md` or in your memory rather than
asking again every time.

## Decide the route first

**A new deck → build a .pptx and upload it.** Export the reference deck
as .pptx for the template, build with `scripts/deck_builder.py`, upload
with Drive `create_file` and the pptx mime type so Drive converts it.
Figures are embedded directly, so there is no per-figure upload, and the
whole deck is one operation.

**An existing deck → edit it in place with the Slides API.** The link the
user already has keeps working and so do any comments on it. Use this for
every revision after the first, including adding a slide to a deck you
built earlier in the session. Recreating a deck to avoid an edit loses
their link, so it is not a shortcut worth taking.

## Building a new deck

1. **Find the source material.** Slides usually summarise something that
   already exists: a paper, a note, a set of figures. Read it rather than
   paraphrasing from the request, and take the numbers from it verbatim.
   If the project has print-quality figures, use those files.
2. **Check for newer results than the source.** A paper's figures can lag
   the analysis. Scan the output directory for files newer than the source
   and say what you find, rather than silently presenting the old story.
   This is the single most valuable thing the skill does: nobody thanks
   you for a deck that is three weeks behind.
3. **Export the template**: Drive `download_file_content` on the reference
   deck with the pptx mime type. The export is large and the host usually
   saves it to a JSON file; decode it with a few lines of Python.
4. **Build** with `scripts/deck_builder.py` (see the module docstring for
   the API). Pass the palette, the talk date and the footer name.
5. **Upload** with Drive `create_file`, passing the file as a
   `sha256:<digest>:<absolute path>` reference rather than typed base64.
6. **Verify by looking at it** — see below. Always.

## Shape of a deck

Follow the source's own structure; a summary of a paper usually becomes:
title, introduction and motivation, method, one section per study with a
figure each, summary, next steps. Section dividers earn their place once a
deck passes about fifteen slides.

A content slide is a label title, the evidence, and a takeaway line. Most
slides are a figure with one or two "→" lines under it; bullet-only slides
should be the minority, and three bullet slides in a row usually means one
of them contains a figure that was not drawn.

## Checking the result

Geometry from the API does not tell you whether text collides with a
figure. Export the deck to PDF, render it, and read it:

```
python scripts/render_check.py <drive-export.json> <outdir>
```

That writes page images and contact sheets of four slides. Look for text
running into the footer band, bullets overlapping a figure, a chip over an
axis label, and anything clipped. Fix, re-render only the changed pages
(`--pages 11,13,16`), and check again. Report what you fixed and what you
deliberately left.

## Figures into an existing deck

`createImage` needs a URL Google can fetch anonymously, so a local PNG
goes through the shared Drive folder first. The full cycle, the
fetchability check and the 2048 px ceiling are in
`references/google-slides.md`. Trash the uploaded file afterwards; the
deck keeps its own copy.

## Defaults worth keeping

- Label titles, not story titles. The finding goes in the takeaway line
  under the figure, not in the heading.
- One message per slide, and the figure is the evidence.
- Use the figures the project already produces. Do not redraw a plot in a
  slide style unless asked.
- When a figure looks soft, check the real pixel size before promising an
  improvement. Google caps inserted images at about 2048 px, and the usual
  cause is a print figure being enlarged.
