# The wave template: colours, layouts and conventions

## The template

A Google Slides theme: a dark title slide with three stacked waves, light
wave bands at the top and bottom of each content slide, and a footer
carrying a name, a date and a page number.

The colours are literal RGB fills on the layout shapes, not theme colours,
so recolouring means substituting hex values across the layout, master and
slide XML. `deck_builder.Deck(palette=...)` does this in `save()`, and it
is what makes a second colourway cheap.

Two colourways ship with the builder. Pick by subject, not by taste, and
keep a given subject on one colour across talks:

| Variant | Suggested use | wave_light | wave_mid | dark | chip |
|---|---|---|---|---|---|
| **green** | data analysis | `B6D7A8` | `6AA84F` | `274E13` | `D9EAD3` |
| **blue** | hardware and simulation | `9FC5E8` | `3D85C6` | `073763` | `CFE2F3` |

The four roles are: `wave_light` for the upper wave and the footer band,
`wave_mid` for the lower wave and the section fill, `dark` for titles,
footer text and chip text, and `chip` for the chip fill. For a third
colourway, pick a light / mid / dark triple of one hue plus a pale tint
for chips and keep the same roles.

`SOURCE` in `deck_builder.py` is the palette the template file itself
uses, and the substitution is from that to the target. If your template is
not the green one above, read its own four colours out of the .pptx once
and set `SOURCE` accordingly.

**Reference deck.** Keep one deck per colourway in Drive and export it as
the .pptx template. Confirm it by title before relying on an id: ids
change if the deck is re-created.

## Layouts

A .pptx export exposes the Google layouts in this order, which
`deck_builder` relies on: `[0]` TITLE, `[1]` SECTION_HEADER, `[2]`
TITLE_AND_BODY, then TITLE_AND_TWO_COLUMNS, TITLE_ONLY, ONE_COLUMN_TEXT,
MAIN_POINT, SECTION_TITLE_AND_DESCRIPTION, CAPTION_ONLY, BIG_NUMBER,
BLANK. Check this on an unfamiliar template before building.

Nearly every slide is TITLE_AND_BODY. Use SECTION_HEADER between the major
parts of a long deck. The body placeholder carries the template's bullet
glyphs (● then ○), so fill it rather than adding a text box: a text box
loses the bullets and the indents.

## Type

- Titles: 24 pt on content slides, 26 pt on the title slide, 30 pt on
  section dividers. The layout sets the face; only the size is worth
  passing.
- Body: 12 to 13 pt, one step smaller for the second level. Below 12 pt
  the slide is too full — split it instead.
- Chips, takeaway lines and table cells: 11 to 12 pt.
- Footer: 13 pt.

## Footer

The name and date are two text boxes on the TITLE_AND_BODY **layout**, not
on the slides, so one edit changes the whole deck. The page number is a
placeholder that python-pptx does not inherit, which is why
`deck_builder` copies it onto each slide it creates.

To change the name, pass both `template_footer_name` (what the template
already says) and `footer_name` (what it should say). The builder widens
the box to about 4.5 in, because at the template's original width a longer
name wraps onto a second line and collides with the band.

## Slide conventions

- **Label titles, not story titles.** "Field uniformity", not "The field
  is uniform only with metal between the pads". Name the topic and let the
  takeaway line carry the finding.
- **One message per slide**, and the figure is the evidence.
- **Chips** name a panel when two figures sit side by side: a small italic
  label in a rounded tinted box, placed just above the figure's top-left.
  A chip is 0.3 in tall, so the figure needs to start about 0.35 in below
  the chip's top or the two overlap. On a slide whose figure starts right
  under the title band there is no gap: either move the figure down, or
  put the chip inside the figure's own white margin.
- **Takeaway lines** start with "→" and sit under the figure. One or two,
  stating what the figure shows and the number that matters. This is where
  the finding goes, since the title is a label.
- **Tables** get a dark header row with white bold text, alternating pale
  and white body rows, and a stronger tint plus bold on the row that is
  the message. Row labels in the first column are bold; number columns are
  right-aligned.
- **Figures** usually come from the project's print-quality outputs. They
  are drawn at print size with small fonts, so on a slide they are being
  enlarged: see the resolution note in `google-slides.md` before promising
  a quality improvement.
