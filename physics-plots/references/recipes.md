# Layouts for common figure types

All on 800x600 with `plotstyle` defaults unless noted. Coordinates are NDC. Axis titles are
placeholders: take the real ones from the analysis.

## Limit vs mass (one lifetime)

- **Axes**: log x and log y. Use `ps.log_x_labels` with values chosen to span the range, e.g. 0.4,
  0.5, 1, 2, 3, 5, 10. The y title is the limit being set, e.g.
  `95% CL upper limit on #sigma #times #it{B} [fb]`.
- **Draw order**:
  1. grey masked windows;
  2. the 2σ band, then the 1σ band;
  3. single-channel curves: thin, Petroff colours, dashed for expected, solid for observed;
  4. combined expected, dashed black;
  5. combined observed, solid black.
- **Breaks**: split every curve at a regime boundary and at gaps with `ps.segments`. Mark the
  boundary with `ps.vline(..., style=3)` and add small grey text naming the two regimes.
- **Legend**: top right (0.57-0.94, 0.60-0.91), size 0.033. Entries in the order observed,
  expected, ±1σ, ±2σ, then the single-channel curves.
- **Label**: `ps.atlas_label([lumi, process, model_point])`.

## Limit vs lifetime (one mass)

- **Axes**: log x over the simulated range, with labels at round values (0.1, 0.3, 1, 3, 10, 30).
  Tight y range: the lowest −2σ edge divided by 1.5, up to the top of the data plus about 1.6
  decades of headroom for the legend.
- **Markers**: large ones (size 1.1) at the simulated lifetimes, small ones (0.6) at reweighted or
  interpolated lifetimes, so the reader can see which points are real.
- **Single family per curve**: use the same input family at every point of a curve. Mixing native
  templates at the generated points with reweighted ones elsewhere puts kinks in the curve that
  are not physics.
- **Interpolation**: interpolating a few points in log-log space gives straight segments that hide
  the real shape. Reweight the samples instead where the shape matters.

## Channel comparison (single channels vs combined)

- **Colours**: one hue per channel, the combined result darkest, e.g. combined #08306B with its
  band in #2171B5 tints. Every channel gets its own ±1σ/±2σ band in its own tint, not just the
  combination.
- **Gain panel**: an optional lower panel shows the ratio of the best single channel to the
  combined limit.
- **Grids of panels**: for a grid of model points use 1000x820 px panels, e.g. 3x2. Draw the label
  with `ps.atlas_label_pad`, because ATLASLabel mis-spaces in sub-pads.

## 2D exclusion plane

- **Scales**: log y for a coupling or a lifetime axis.
- **Fills**: observed region as an opaque tint `ps.tint(1, 0.80)`, expected as `ps.tint(1, 0.50)`.
  The other kind is drawn as a dashed outline.
- **Single-channel contours**: drawn as outlines in the palette colours. Keep their closing edges
  at the window boundaries and drop the pieces that only follow the edge of the scanned grid.
- **Iso-curves** (e.g. constant lifetime): thin dotted grey. Label them at the left edge of the
  frame, all at the same x, small, light grey, placed just below their curve, with no background
  box and all at the same size. Keep them clear of the observed/expected labels; a little overlap
  with a contour is fine.
- **Windows**: plain grey, drawn before the fills.
- **Heatmap variant**: colour map plus contour lines only, no fills, right margin 0.17 for the z
  axis. There the map is drawn over the windows.

## Local p0 scan

- **Axes**: log y from about 5e-4 to 40, so the region above p0 = 0.5 holds the label. Dashed grey
  1σ/2σ/3σ lines labelled on the right.
- **Regimes**: grey windows, plus a dotted boundary line with the two method names in small grey
  text.
- **Overlays**: one curve per model point, with the scanned parameter as the legend header. In a
  single-parameter version, add one line giving the minimum local p0, its Z and where it falls.
- **Points with nothing observed**: no excess means p0 = 0.5. Show them at 0.5 and say so; do not
  leave a gap unexplained.

## Distributions and efficiencies (quick look)

- **Histograms**: `ps.th1(...)` from arrays; draw with `HIST E`, overlays with `HIST E SAME`. Save
  with `ps.save_linlog(c, hists, stem)`, which writes `stem_lin` and `stem_log` with headroom for
  the label and legend.
- **Mass distributions**: linear y. Label the y axis "Events / N MeV".
- **Other y axes**: plain events or fractions with the bin width ("Fraction of events / 0.025").
- **Model comparisons**: one model solid, the other dashed with a light opaque fill
  (`ps.tint(..., 0.88)`).
- **Legend header**: when entries carry numbers, put their meaning in the header and keep the
  entries short.
- **Efficiencies**: `TEfficiency` with `SetDirectory(nullptr)`, and the frame maximum at about 1.9
  so the label sits above the data.
- **Selection in the label**: when a cut changes, check the label still describes the selection
  that was applied.

## Heatmaps of a 2D grid

`ps.grid_heatmap(name, xlabels, ylabels, cells, header, ztitle, zmin, zmax, stem)`; see
`scripts/example_grid_heatmap.py`.

- **Header**: 3-4 lines under the experiment label: process, region and √s; what the map shows;
  one small line that explains the cell contents and markers.
- **Margins**: top 0.30 for the header, right 0.17 for the z axis titled with units. Use one fixed
  z range per family of maps so they can be compared.
- **Cells**: one large number plus at most two short small lines (`±err`, `+up −down`,
  `(fraction)`). Never stack super- and subscripts (`^{+a}_{-b}`) in a cell; they overlap. Cell
  text switches from white to black on light cells.
- **Missing or low statistics**: leave missing cells white and mark low-statistics cells with `*`;
  say what both mean in the header.
