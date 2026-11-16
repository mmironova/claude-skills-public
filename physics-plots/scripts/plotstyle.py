"""Self-contained ROOT helpers for ATLAS-style physics plots (quick-look and publication quality).

    import sys; sys.path.insert(0, "<skill dir>/scripts"); import plotstyle as ps
    c = ps.canvas("lim", logx=True, logy=True)
    fr = ps.frame(0.06, 40, 1e-5, 1e-2, "c#tau_{X} [mm]", "95% CL upper limit on #sigma #times #it{B} [fb]")
    ps.log_x_labels(fr, [0.1, 0.3, 1, 3, 10, 30], 1e-5)
    ps.band(x, lo2, hi2, ps.BAND2); ps.band(x, lo1, hi1, ps.BAND1)
    ps.line(x, exp, 1, style=2); ps.line(x, obs, 1, marker=20)
    ps.atlas_label(["#sqrt{s} = 13 TeV, 140 fb^{-1}", "m_{X} = 1.2 GeV"])
    ps.save(c, "plots/limit_vs_ctau")          # -> .pdf (fonts embedded, cropped to the canvas) + .png

Run with a ROOT that has pyROOT. On a machine with CVMFS, an LCG view works, called by full path
because setupATLAS is not available non-interactively:
    source /cvmfs/sft.cern.ch/lcg/views/LCG_106/x86_64-el9-gcc13-opt/setup.sh
    /cvmfs/sft.cern.ch/lcg/views/LCG_106/x86_64-el9-gcc13-opt/bin/python3 script.py

The ATLAS style macros are picked up from CVMFS if present and the module falls back to plain ROOT
if they are not, so everything here also runs against a stock ROOT install.

Do not import this module into processes that also load fit libraries (quickFit/RooFitExtensions):
keep plotting and fitting in separate processes, they have segfaulted together.
"""
import array
import math
import re
import subprocess
import sys
import zlib
from pathlib import Path

sys.path.insert(0, "/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase/x86_64/astyle/current/astyle")
import ROOT  # noqa: E402

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kWarning
try:
    import AtlasStyle  # noqa: E402,F401
    import AtlasLabels  # noqa: E402,F401
    ROOT.SetAtlasStyle()
    HAVE_ATLAS_STYLE = True
except Exception as exc:  # noqa: BLE001
    print("WARNING: AtlasStyle not available, using plain ROOT:", exc)
    HAVE_ATLAS_STYLE = False
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetErrorX(0.5)

# --------------------------------------------------------------------------- colours
# Publication palette: Petroff-10 (colour-blind safe, the one ATLAS recommends).
PETROFF = ["#3f90da", "#ffa90e", "#bd1f01", "#94a4a2", "#832db6", "#a96b59", "#e76300", "#b9ac70", "#717581", "#92dadd"]
# Quick-look palette: bright saturated colours, easy to tell apart on a screen at a glance.
BRIGHT = {"blue": "#0066FF", "red": "#FF2A2A", "green": "#00B050", "orange": "#FF8C00", "purple": "#9B30FF",
          "cyan": "#00B4D8", "grey": "#777777"}
BAND1_HEX, BAND2_HEX = "#00cc00", "#ffcc00"     # Brazil bands
MASK_HEX = "#d9d9d9"                             # plain light grey for masked / excluded regions
_CACHE = {}
_KEEP = []


def hexcolor(h):
    if h not in _CACHE:
        _CACHE[h] = ROOT.TColor.GetColor(h)
    return _CACHE[h]


def palette(i):
    """Petroff colour, 1-indexed (palette(1) = #3f90da)."""
    return hexcolor(PETROFF[(i - 1) % len(PETROFF)])


def bright(name):
    return hexcolor(BRIGHT[name])


BAND1, BAND2 = hexcolor(BAND1_HEX), hexcolor(BAND2_HEX)


def tint(hexstr_or_index, frac):
    """Opaque colour mixed with white (frac = fraction of white). PostScript/EPS has no alpha: use tints for
    overlapping fills instead of SetFillColorAlpha."""
    h = PETROFF[(hexstr_or_index - 1) % 10] if isinstance(hexstr_or_index, int) else hexstr_or_index
    h = h.lstrip("#")
    rgb = [int(h[k:k + 2], 16) for k in (0, 2, 4)]
    return hexcolor("#" + "".join(f"{round(v + (255 - v) * frac):02x}" for v in rgb))


def keep(*objs):
    """Keep ROOT objects alive until the canvas is saved."""
    _KEEP.extend(objs)
    return objs[0] if len(objs) == 1 else objs


# --------------------------------------------------------------------------- text
# ROOT 6.32 TLatex renders a literal space next to a symbol character (#rightarrow, #gamma, #pm) far too wide.
_NONSYM = {"bf", "it", "font", "scale", "splitline", "sqrt", "color", "kern", "lower", "frac", "bar", "hat",
           "left", "right", "mbox"}


def fix(t):
    """Normal-width spaces before symbol-font characters: 'H #rightarrow #gamma' renders as it should."""
    if not t or "#" not in t:
        return t
    return re.sub(r" (?=#([a-zA-Z]+))", lambda m: "#scale[0.5]{ }" if m.group(1) not in _NONSYM else " ", t)


def text(x, y, t, size=0.04, align=11, color=1, ndc=True, angle=0, font=42):
    lat = ROOT.TLatex()
    lat.SetNDC(ndc); lat.SetTextFont(font); lat.SetTextSize(size); lat.SetTextAlign(align)
    lat.SetTextColor(color); lat.SetTextAngle(angle)
    lat.DrawLatex(x, y, fix(t))
    return keep(lat)


def atlas_label(lines=(), x=0.2, y=0.87, label="Internal", size=0.04, step=0.06):
    """'ATLAS Internal' then text lines; returns the NDC y below the last line (put legends below it).

    The status word defaults to 'Internal', which is the safe choice: 'Preliminary' and the bare
    'ATLAS' mark are reserved for approved results. Pass label= to change it."""
    if HAVE_ATLAS_STYLE:
        ROOT.ATLASLabel(x, y, label)
    else:
        text(x, y, "ATLAS", size=0.05, font=72); text(x + 0.13, y, label, size=0.05)
    yy = y - step
    for ln in lines:
        if ln:
            text(x, yy, ln, size=size)
            yy -= step
    return yy


def atlas_label_pad(x, y, label, size, canvas_wh=(800, 600), pad_h_frac=1.0):
    """ATLASLabel mis-spaces 'ATLAS' and the label inside sub-pads; this draws it with the right word spacing."""
    w, h = canvas_wh
    delx = 0.115 * 696 * h / (472 * w) * pad_h_frac * (size / 0.05)
    text(x, y, "ATLAS", size=size, font=72)
    if label:
        text(x + delx, y, label, size=size)


def legend(x1, y1, x2, y2, size=0.04, ncol=1, header=None):
    """Borderless, transparent, font 42. Entries pass through fix()."""
    leg = ROOT.TLegend(x1, y1, x2, y2)
    leg.SetBorderSize(0); leg.SetFillStyle(0); leg.SetTextFont(42); leg.SetTextSize(size); leg.SetNColumns(ncol)
    if header:
        leg.SetHeader(fix(header))
    orig = leg.AddEntry
    leg.AddEntry = lambda obj, lab="", opt="lpf": orig(obj, fix(lab), opt)
    return keep(leg)


# --------------------------------------------------------------------------- canvas / frame
def canvas(name="c", w=800, h=600, logx=False, logy=False, left=0.16, right=0.05, top=0.05, bottom=0.16):
    """800x600 is the publication default (text sizes below assume it); use 1800x1300 only for quick looks."""
    c = ROOT.TCanvas(name, name, w, h)
    c.SetLogx(logx); c.SetLogy(logy)
    c.SetLeftMargin(left); c.SetRightMargin(right); c.SetTopMargin(top); c.SetBottomMargin(bottom)
    return keep(c)


def frame(xmin, xmax, ymin, ymax, xtitle, ytitle, name=None):
    h = ROOT.TH1F(name or f"frame{len(_KEEP)}", "", 100, xmin, xmax)
    h.SetMinimum(ymin); h.SetMaximum(ymax)
    h.GetXaxis().SetTitle(fix(xtitle)); h.GetYaxis().SetTitle(fix(ytitle))
    h.SetStats(0); h.Draw("AXIS")
    return keep(h)


def log_headroom(ymin, ydata_max, frac=0.45):
    """y max on a log axis so that the top `frac` of the frame is free for label and legend."""
    a, b = math.log10(ymin), math.log10(ydata_max)
    return 10 ** (b + frac / (1 - frac) * (b - a))


def log_x_labels(fr, values, ymin, size=None):
    """Replace ROOT's crowded or sparse log-axis labels by labels at the given values (e.g. 0.1, 0.3, 1, 3, 10)."""
    ax = fr.GetXaxis()
    size = size or ax.GetLabelSize()
    ax.SetLabelSize(0)
    p = ROOT.gPad
    lo, hi = math.log10(ax.GetXmin()), math.log10(ax.GetXmax())
    for v in values:
        x = p.GetLeftMargin() + (1 - p.GetLeftMargin() - p.GetRightMargin()) * (math.log10(v) - lo) / (hi - lo)
        text(x, p.GetBottomMargin() - 0.015, f"{v:g}", size=size, align=23)


def boxes(ranges, ymin, ymax, color=MASK_HEX):
    """Plain opaque grey boxes for masked windows. Draw them FIRST so curves and contours sit on top."""
    out = []
    for lo, hi in ranges:
        b = ROOT.TBox(lo, ymin, hi, ymax)
        b.SetFillColor(hexcolor(color)); b.SetFillStyle(1001); b.SetLineWidth(0); b.Draw()
        out.append(b)
    keep(*out) if out else None
    return out


def hline(y, xmin, xmax, style=2, color=ROOT.kGray + 2, width=1):
    ln = ROOT.TLine(xmin, y, xmax, y); ln.SetLineStyle(style); ln.SetLineColor(color); ln.SetLineWidth(width); ln.Draw()
    return keep(ln)


def vline(x, ymin, ymax, style=2, color=ROOT.kGray + 2, width=1):
    ln = ROOT.TLine(x, ymin, x, ymax); ln.SetLineStyle(style); ln.SetLineColor(color); ln.SetLineWidth(width); ln.Draw()
    return keep(ln)


# --------------------------------------------------------------------------- graphs
def graph(xs, ys):
    return keep(ROOT.TGraph(len(xs), array.array("d", xs), array.array("d", ys)))


def band(xs, lo, hi, color):
    """Filled band between lo and hi (Brazil bands: band(..., BAND2) first, then BAND1)."""
    g = graph(list(xs) + list(xs)[::-1], list(lo) + list(hi)[::-1])
    g.SetFillColor(color); g.SetLineWidth(0); g.Draw("F")
    return g


def line(xs, ys, color, style=1, width=2, marker=None, msize=1.0):
    """Line (+ markers). Line widths are ABSOLUTE in the PDF: 2 for main curves, 1 for secondary ones on 800x600."""
    g = graph(xs, ys)
    g.SetLineColor(color); g.SetLineStyle(style); g.SetLineWidth(width); g.SetMarkerColor(color)
    if marker:
        g.SetMarkerStyle(marker); g.SetMarkerSize(msize)
        g.Draw("LP" if width > 0 and len(xs) > 1 else "P")
    else:
        g.Draw("L")
    return g


def segments(points, breaks=(), max_gap=None):
    """Split sorted (x, ...) tuples into runs: at x values in `breaks` (regime boundaries such as 5.5 GeV) and at
    gaps larger than max_gap. Draw one line per run so curves do not bridge masked regions or change of method."""
    runs, cur = [], []
    for p in points:
        if cur:
            gap = max_gap is not None and p[0] - cur[-1][0] > max_gap
            crossed = any(cur[-1][0] < b <= p[0] for b in breaks)
            if gap or crossed:
                runs.append(cur); cur = []
        cur.append(p)
    if cur:
        runs.append(cur)
    return runs


# --------------------------------------------------------------------------- histograms (quick look)
def th1(name, edges, values, color, weights=None, norm=False, width=2, style=1, fill=None, xtitle="", ytitle=""):
    """TH1D filled from a sequence. `edges` = (nbins, lo, hi) or explicit bin edges (e.g. log bins).
    Under/overflow is clipped into the first/last bin. `fill` = opaque fill colour (use tint(), not alpha)."""
    if isinstance(edges, tuple):
        h = ROOT.TH1D(name, "", edges[0], edges[1], edges[2]); lo, hi = edges[1], edges[2]
    else:
        h = ROOT.TH1D(name, "", len(edges) - 1, array.array("d", edges)); lo, hi = edges[0], edges[-1]
    h.Sumw2(); h.SetDirectory(0)
    eps = 1e-9 * (hi - lo)
    for i, x in enumerate(values):
        h.Fill(min(max(x, lo + eps), hi - eps), 1.0 if weights is None else weights[i])
    if norm and h.Integral() > 0:
        h.Scale(1.0 / h.Integral())
    h.SetLineColor(color); h.SetMarkerColor(color); h.SetLineWidth(width); h.SetLineStyle(style); h.SetMarkerSize(0)
    if fill is not None:
        h.SetFillColor(fill)
    h.GetXaxis().SetTitle(fix(xtitle)); h.GetYaxis().SetTitle(fix(ytitle))
    return keep(h)


def save_linlog(c, hists, stem, lin_headroom=1.7, log_headroom=300, logmin=None, **save_kw):
    """Save stem_lin and stem_log of an overlay whose first histogram owns the axes. The headroom keeps the label
    block and legend clear of the data; log plots with a big legend can need x1000-x5000."""
    contents = [h.GetBinContent(b) for h in hists for b in range(1, h.GetNbinsX() + 1)]
    mx = max(contents)
    mn = logmin or max(min([v for v in contents if v > 0] + [mx]) * 0.5, mx * 1e-5)
    for h in hists:                       # every histogram: SAME overlays with an unset minimum break log axes
        h.SetMaximum(mx * lin_headroom); h.SetMinimum(0)
    c.SetLogy(False); c.Modified(); c.Update()
    save(c, f"{stem}_lin", **save_kw)
    for h in hists:
        h.SetMaximum(mx * log_headroom); h.SetMinimum(mn)
    c.SetLogy(True); c.Modified(); c.Update()
    save(c, f"{stem}_log", **save_kw)
    c.SetLogy(False)


# --------------------------------------------------------------------------- grid heatmaps
def grid_heatmap(name, xlabels, ylabels, cells, header, ztitle, zmin, zmax, stem,
                 xtitle="m_{X} [GeV]", ytitle="c#tau [mm]", dark_below=None, label="Internal", **save_kw):
    """Parameter grid (e.g. mass x lifetime) as a colour map with text in every cell.

    cells:  {(i, j): {"value": float, "lines": ["main", "small", "small"]}}, i indexes xlabels, j ylabels.
            Missing cells stay white: say what white means in `header`.
    header: lines under 'ATLAS Internal': process / region / sqrt(s), what the map shows, then one small line
            explaining the cell contents and markers (e.g. '* N < 50').
    Use one fixed (zmin, zmax) for a family of maps so they can be compared. Cell text turns white below
    `dark_below` (default: lowest 30% of the z range)."""
    c = canvas(name, right=0.17, top=0.30, left=0.14, bottom=0.14)
    h = ROOT.TH2D(name, "", len(xlabels), 0, len(xlabels), len(ylabels), 0, len(ylabels))
    h.SetDirectory(0); keep(h)
    for i, s in enumerate(xlabels):
        h.GetXaxis().SetBinLabel(i + 1, str(s))
    for j, s in enumerate(ylabels):
        h.GetYaxis().SetBinLabel(j + 1, str(s))
    for (i, j), cell in cells.items():
        h.SetBinContent(i + 1, j + 1, cell["value"])
    h.GetXaxis().SetTitle(fix(xtitle)); h.GetYaxis().SetTitle(fix(ytitle)); h.GetZaxis().SetTitle(fix(ztitle))
    h.GetXaxis().SetTitleOffset(1.15); h.GetYaxis().SetTitleOffset(1.1); h.GetZaxis().SetTitleOffset(1.2)
    h.GetXaxis().SetLabelSize(0.05); h.GetYaxis().SetLabelSize(0.05)
    h.SetMinimum(zmin); h.SetMaximum(zmax)
    ROOT.gStyle.SetPalette(ROOT.kBird); ROOT.gStyle.SetNumberContours(100)
    h.Draw("COLZ")
    dark = dark_below if dark_below is not None else zmin + 0.3 * (zmax - zmin)
    for (i, j), cell in cells.items():
        lines = cell["lines"]
        for k, ln in enumerate(lines):          # first line large, the others small, stacked top to bottom
            y = j + (0.5 if len(lines) == 1 else 0.74 - 0.27 * k)
            text(i + 0.5, y, ln, size=0.030 if k == 0 else 0.019, align=22, ndc=False,
                 color=ROOT.kWhite if cell["value"] < dark else ROOT.kBlack)
    text(0.14, 0.93, "ATLAS", size=0.045, font=72)
    text(0.26, 0.93, label, size=0.045)
    y = 0.87
    for k, ln in enumerate(header):
        text(0.14, y, ln, size=0.036 if k < 2 else 0.028)
        y -= 0.05 if k < 2 else 0.04
    return save(c, stem, **save_kw)


# --------------------------------------------------------------------------- output
def save(c, stem, dpi=200, png=True):
    """stem.pdf: vector, cropped to the canvas, all fonts embedded; stem.png: antialiased raster of that PDF.

    Why not c.SaveAs('x.pdf') / c.SaveAs('x.png'): ROOT's PDF is an A4 page (the plot ends up in a corner and the
    PNG made from it is mostly white) and its PNGs are jagged. EPS -> ghostscript with EPSCrop gives the canvas
    size, and rasterising the PDF with gs gives smooth lines for slides.
    """
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    before = {id(p) for p in c.GetListOfPrimitives()}
    c.RedrawAxis()
    eps, pdf = stem.with_suffix(".eps"), stem.with_suffix(".pdf")
    c.SaveAs(str(eps))
    # RedrawAxis leaves a frozen copy of the frame histogram on the pad; drop it so a later save of the same
    # canvas (e.g. the _log version after _lin) does not paint stale axis ranges.
    for p in [p for p in c.GetListOfPrimitives() if id(p) not in before]:
        c.GetListOfPrimitives().Remove(p)
    subprocess.run(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-dSAFER", "-sDEVICE=pdfwrite", "-dEPSCrop",
                    "-dCompatibilityLevel=1.5", "-dPDFSETTINGS=/prepress", "-dEmbedAllFonts=true", "-dSubsetFonts=true",
                    "-dAutoRotatePages=/None", f"-sOutputFile={pdf}",
                    "-c", ".setpdfwrite <</NeverEmbed [ ]>> setdistillerparams", "-f", str(eps)],
                   check=True, capture_output=True)
    eps.unlink()
    if png:
        subprocess.run(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-dSAFER", "-sDEVICE=png16m", f"-r{dpi}",
                        "-dTextAlphaBits=4", "-dGraphicsAlphaBits=4", f"-sOutputFile={stem.with_suffix('.png')}",
                        str(pdf)], check=True)
    check_fonts(pdf)
    print(f"[saved] {pdf}" + (f" (+ .png, {dpi} dpi)" if png else ""))
    return pdf


def check_fonts(pdf):
    """Raise if any font in the PDF is not embedded (journals reject those)."""
    data = Path(pdf).read_bytes()
    n_font = len(re.findall(rb"/Type\s*/FontDescriptor", data))
    n_emb = len(re.findall(rb"/FontFile[23]?\b", data))
    if n_font == 0:
        for m in re.finditer(rb"stream\r?\n(.*?)endstream", data, re.S):
            try:
                d = zlib.decompress(m.group(1))
            except zlib.error:
                continue
            n_font += len(re.findall(rb"/Type\s*/FontDescriptor", d))
            n_emb += len(re.findall(rb"/FontFile[23]?\b", d))
    if n_emb < n_font:
        raise RuntimeError(f"{Path(pdf).name}: {n_font - n_emb} of {n_font} fonts not embedded")
