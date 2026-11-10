---
name: physics-plots
description: Make publication-quality physics plots with ROOT in ATLAS style - limit plots (vs mass, vs lifetime, Brazil bands, channel comparisons), exclusion contours in 2D parameter planes, p-value scans, distributions, efficiencies and heatmaps - at quick-look or publication quality, with PDFs cropped to the canvas, embedded fonts and smooth PNGs for slides. Use this whenever the user asks for a plot, figure, comparison, "paper-quality" or "publication-ready" plots, plots for slides, or asks to remake, restyle, zoom, relabel or fix an existing plot in a ROOT-based analysis. Not for matplotlib or web charts.
---

# Physics plots

ROOT plots in the ATLAS style. Every plot leaves as a vector PDF plus a PNG, and every plot gets
looked at before it is reported.

`scripts/plotstyle.py` holds the style setup, palettes, labels, frames, bands, masked-window boxes
and the save route. Import it rather than re-deriving them; `scripts/example_limit_plot.py` is a
worked example that also serves as a smoke test. `references/recipes.md` has layouts for the
figure types this covers.

## Environment

pyROOT. On a machine with CVMFS, an LCG view works, called by full path because `setupATLAS` is
not available non-interactively:

```bash
source /cvmfs/sft.cern.ch/lcg/views/LCG_106/x86_64-el9-gcc13-opt/setup.sh
/cvmfs/sft.cern.ch/lcg/views/LCG_106/x86_64-el9-gcc13-opt/bin/python3 make_plot.py
```

The ATLAS style macros are loaded from CVMFS if present, and the module falls back to plain ROOT
if they are not. Keep plotting and fitting in separate processes: importing the style module into
a process that loads the fit libraries (quickFit, RooFitExtensions) has segfaulted.

## Two levels of polish

**Quick look** (studies, checks, debugging): bright saturated colours (`ps.BRIGHT`: blue #0066FF,
red #FF2A2A, green #00B050, orange #FF8C00, purple #9B30FF), data in black. Canvas 800x600, or
1800x1300 with line widths 4-5. Save `_lin` and `_log` versions of distributions.

**Publication or slides** (anything called nice, paper-quality, or destined for a slide):
- Canvas 800x600; the text sizes in the helper assume it.
- Petroff palette (`ps.palette(i)`), which is colour-blind safe.
- Brazil bands green #00cc00 and yellow #ffcc00.
- Observed limits: solid black. Expected limits: dashed black.
- Thin lines: width 2 for the main curves, 1 for secondary curves. PDF line widths are absolute,
  so a width that looked right on a large quick-look canvas is too heavy here.
- Opaque tints instead of transparency (EPS has no alpha).

When it is unclear which level is wanted, use publication style. Sloppy plots get noticed more
than over-polished ones.

## Conventions that always apply

- **Label block, top left**: `ps.atlas_label([...])` draws the collaboration mark and status, then
  the lines below it.
  - Default to "Internal". "Preliminary" and the bare mark are for approved results only, and that
    approval is not yours to assume.
  - Order of the lines: centre-of-mass energy and luminosity, then the process, then the model
    point (mass, lifetime).
  - Keep one spelling of each symbol across a whole set of figures, and take it from the analysis
    note rather than inventing one.
- **Legend**: borderless, transparent, font 42. Put it top right, inside the frame, clear of the
  curves; raise the y maximum (`ps.log_headroom`) rather than shrink the text.
- **Masked or excluded regions**: plain light-grey boxes (#d9d9d9), no hatching, drawn first so
  curves and contours sit on top. Curves that do have a result inside a window are drawn through
  it, over the grey.
- **Regime changes**: break the curve where the method changes (e.g. parametric fit → cut-and-count)
  and at gaps (`ps.segments`). Draw a thin dotted line at the boundary, labelled in small grey text.
- **Log axes**: replace ROOT's labels with chosen values (`ps.log_x_labels`, e.g. 0.1, 0.3, 1, 3,
  10, 30).
- **Text in the frame**: no background boxes behind labels and no explanatory footnotes inside the
  frame. Put explanations in the caption or the reply.
- **Spacing**: pass every TLatex string through `ps.fix()`. ROOT 6.32 renders a space before
  `#rightarrow`, `#gamma` or `#pm` far too wide.

## Saving

`ps.save(c, "dir/name")` writes `name.pdf` (cropped to the canvas, all fonts embedded, checked) and
`name.png` (200 dpi, antialiased, rasterised from that PDF). Never use `c.SaveAs("x.pdf")` or
`c.SaveAs("x.png")` directly:

- ROOT's PDF is an A4 page, so the plot ends up in a corner of a mostly white page.
- ROOT's PNGs are jagged, and they look bad on a slide.

For slides, a 200-300 dpi PNG made from the PDF is right.

## Look at every plot before reporting it

Open each PNG with the Read tool. Fix and re-render before reporting if anything is off. Failures
that have slipped through before:

- Legend or label text touching curves, or running off the frame.
- Axis titles or subscripts clipped at the canvas edge (increase the bottom margin).
- The y range much larger than the data, or the curves squashed into one corner. Zoom so the data
  fill the frame: set the y range from the data, typically the lowest −2σ band edge divided by 1.5
  up to the highest curve, and leave headroom only for the label and legend. Trim the x range to
  just beyond the data.
- Kinks from mixing inputs with different systematics at neighbouring points, for example native
  and reweighted templates, or interpolated and simulated points. Use one consistent input family
  for a whole curve, and mark interpolated or reweighted points with smaller markers. When a curve
  is not smooth, fix the input rather than smoothing the drawing; the one safe cosmetic smoothing
  is averaging band edges in log space, and never the observed curve.
- Unphysical outliers, such as a fit stuck in a false minimum giving a 9σ point. Investigate them;
  never plot them silently.
- A caption or reply that describes the plot wrongly. Describe what the image actually shows.

Report the PDF and PNG paths, and say in one or two lines what changed and what the plot shows.

## One thing to be careful about

Plots marked Internal are not public. Do not upload them to an image host, paste them into a
public issue, or put them anywhere that produces a public URL. If a figure has to move, hand over
the local path and let the user post it themselves.
