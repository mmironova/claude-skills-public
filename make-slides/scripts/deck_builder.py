"""Build a deck on a "wave" Google Slides template with python-pptx.

The template is a Google Slides theme. Everything here works on a .pptx
export of it, because the Slides API cannot insert a local image and is
slow for a deck built from scratch; the finished .pptx is uploaded to
Drive and converted back to Google Slides.

Colours live as literal RGB fills on the layout shapes, not as theme
colours, so a recolour is a string substitution over the layout, master and
slide XML. That happens in save(), after python-pptx has written the file.

Typical use:

    from deck_builder import Deck
    d = Deck("template.pptx", palette="blue", footer_date="08 November 2026",
             footer_name="A. Author", template_footer_name="Your Name")
    d.title_slide("Title line one\\nTitle line two",
                  ["A. Author", "Some Project, Some Lab", "8 November 2026"])
    s = d.content("Validation: energy deposition")
    d.picture(s, "fig_a.png", 0.55, 0.78, h=3.05)
    d.chip(s, "Most probable value", 0.3, 0.72)
    d.takeaway(s, ["Model agrees with the reference formula to 2.8 %"], 0.4, 3.88, 9.2)
    d.save("deck.pptx")

SOURCE below must match the palette your own template actually uses, and
template_footer_name must be the name already written on its layouts;
both are read out of the .pptx export once and then left alone.

Inches throughout, matching the 10 x 5.625 in page. Run with any Python
that has python-pptx and Pillow.
"""
import copy
import re
import zipfile

from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

# The template's own colours (green) and the hardware variant (blue).
# Roles: wave_light = upper wave and footer band, wave_mid = lower wave and
# section fill, dark = titles, footer text and chip text, chip = chip fill.
PALETTES = {
    "green": {"wave_light": "B6D7A8", "wave_mid": "6AA84F", "dark": "274E13", "chip": "D9EAD3"},
    "blue":  {"wave_light": "9FC5E8", "wave_mid": "3D85C6", "dark": "073763", "chip": "CFE2F3"},
}
# Alternating table rows: paler than the chip tint, so the highlighted row
# still stands out against them.
BANDS = {"green": "ECF4E8", "blue": "E9F1FA"}
SOURCE = PALETTES["green"]
FONT = "Open Sans Medium"
CENTER, RIGHT = PP_ALIGN.CENTER, PP_ALIGN.RIGHT

# _{...} and ^{...} become sub- and superscript runs, so chemical formulae
# and V_dep read correctly without hand-building runs at every call site.
_TOK = re.compile(r"(_\{[^}]*\}|\^\{[^}]*\})")


def add_runs(par, text, size=None, bold=None, italic=None, color=None, font=None):
    """Append text to a paragraph, honouring _{sub} and ^{sup} markers."""
    for part in _TOK.split(text):
        if not part:
            continue
        base = 0
        if part.startswith("_{"):
            part, base = part[2:-1], -25000
        elif part.startswith("^{"):
            part, base = part[2:-1], 30000
        r = par.add_run()
        r.text = part
        f = r.font
        if size:
            f.size = Pt(size)
        if bold is not None:
            f.bold = bold
        if italic is not None:
            f.italic = italic
        if color is not None:
            f.color.rgb = color
        if font:
            f.name = font
        if base:
            r._r.get_or_add_rPr().set("baseline", str(base))


def set_text(tf, text, **kw):
    """Replace a text frame's content; newlines start new paragraphs."""
    tf.clear()
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        add_runs(p, line, **kw)


def _border(cell, side, color="BFBFBF", w=9525):
    """Set one cell border; color=None removes it."""
    tcPr = cell._tc.get_or_add_tcPr()
    tag = {"B": "a:lnB", "T": "a:lnT", "L": "a:lnL", "R": "a:lnR"}[side]
    for old in tcPr.findall(qn(tag)):
        tcPr.remove(old)
    ln = etree.SubElement(tcPr, qn(tag), w=str(w if color else 0))
    if color:
        etree.SubElement(etree.SubElement(ln, qn("a:solidFill")), qn("a:srgbClr"), val=color)
    else:
        etree.SubElement(ln, qn("a:noFill"))


class Deck:
    """A deck under construction on the wave template."""

    def __init__(self, template, palette="green", footer_date=None,
                 footer_name=None, footer_size=13, template_footer_name=None):
        self.prs = Presentation(template)
        self.target = PALETTES[palette] if isinstance(palette, str) else palette
        self.band = BANDS.get(palette if isinstance(palette, str) else "", "F2F2F2")
        self.footer_date, self.footer_name, self.footer_size = footer_date, footer_name, footer_size
        self.template_footer_name = template_footer_name
        self.dark = RGBColor.from_string(self.target["dark"])
        self.chip_fill = RGBColor.from_string(self.target["chip"])
        L = self.prs.slide_layouts
        self.L_TITLE, self.L_SECTION, self.L_BODY = L[0], L[1], L[2]
        # The template ships with example slides; keep the first as the title
        # slide and drop the rest.
        ids = self.prs.slides._sldIdLst
        for sldId in list(ids)[1:]:
            self.prs.part.drop_rel(sldId.rId)
            ids.remove(sldId)
        if self.template_footer_name and footer_name:
            self._widen_footer()

    def _widen_footer(self, width=4.5):
        """The template's footer box is sized for the name already in it.

        A longer replacement wraps, and the second line falls below the
        band, so widen the box on every layout that has one. On this
        template the date box starts at about 5.9 in, so 4.5 in is safe.
        """
        for layout in self.prs.slide_layouts:
            for sh in layout.shapes:
                if sh.has_text_frame and sh.text_frame.text.strip().startswith(self.template_footer_name):
                    sh.width = Inches(width)

    # -- slides ----------------------------------------------------------
    def _ph(self, slide, idx):
        for s in slide.placeholders:
            if s.placeholder_format.idx == idx:
                return s

    def _slide_number(self, slide, layout):
        """Copy the layout's slide-number placeholder onto the slide.

        python-pptx does not inherit it, and without this the page numbers
        are missing from every slide it creates.
        """
        for sp in layout.placeholders:
            if sp.placeholder_format.idx == 12:
                slide.shapes._spTree.append(copy.deepcopy(sp._element))

    def title_slide(self, title, subtitle_lines, title_size=26, keep_logos=True):
        """Fill the template's own title slide. Returns it."""
        s = self.prs.slides[0]
        t = self._ph(s, 0)
        t.top, t.height, t.width = Emu(1_850_000), Emu(1_450_000), Inches(9.3)
        set_text(t.text_frame, title, size=title_size)
        sub = self._ph(s, 1)
        set_text(sub.text_frame, "\n".join(subtitle_lines))
        # The subtitle placeholder carries a hanging indent from the
        # template, which indents every line after the first.
        for p in sub.text_frame.paragraphs:
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", "0")
            pPr.set("indent", "0")
        if not keep_logos:
            for sh in list(s.shapes):
                if sh.shape_type == 13:
                    sh._element.getparent().remove(sh._element)
        return s

    def drop_logo(self, slide, keep_leftmost=True):
        """Remove logos from the title slide; keeps the leftmost by default.

        Use when a deck should carry fewer logos than the template.
        """
        pics = [sh for sh in slide.shapes if sh.shape_type == 13]
        for sh in sorted(pics, key=lambda p: p.left)[1 if keep_leftmost else 0:]:
            sh._element.getparent().remove(sh._element)

    def content(self, title, title_size=24):
        """A title-and-body slide. The body placeholder is left in place;
        call bullets() to fill it or drop_body() if the slide is a figure."""
        s = self.prs.slides.add_slide(self.L_BODY)
        set_text(self._ph(s, 0).text_frame, title, size=title_size)
        self._slide_number(s, self.L_BODY)
        return s

    def section(self, title, subtitle, title_size=30, subtitle_size=16):
        """A section divider."""
        s = self.prs.slides.add_slide(self.L_SECTION)
        set_text(self._ph(s, 0).text_frame, title, size=title_size)
        set_text(self._ph(s, 1).text_frame, subtitle, size=subtitle_size)
        self._slide_number(s, self.L_SECTION)
        return s

    def drop_body(self, slide):
        b = self._ph(slide, 1)
        if b is not None:
            b._element.getparent().remove(b._element)

    # -- content ---------------------------------------------------------
    def bullets(self, slide, items, x, y, w, h, size=13, space=4):
        """Fill the body placeholder. items is [(level, text), ...].

        Using the placeholder rather than a new text box keeps the
        template's bullet glyphs and indents.
        """
        b = self._ph(slide, 1)
        b.left, b.top, b.width, b.height = Inches(x), Inches(y), Inches(w), Inches(h)
        tf = b.text_frame
        tf.clear()
        tf.word_wrap = True
        for i, (lvl, text) in enumerate(items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.level = lvl
            p.space_after = Pt(space)
            add_runs(p, text, size=size if lvl == 0 else size - 1)
        return b

    def picture(self, slide, path, x, y, w=None, h=None):
        """Place an image, preserving its aspect ratio. Returns (w, h) in inches."""
        W, H = Image.open(path).size
        if w is None:
            w = h * W / H
        if h is None:
            h = w * H / W
        slide.shapes.add_picture(path, Inches(x), Inches(y), Inches(w), Inches(h))
        return w, h

    def chip(self, slide, text, x, y, w=None, size=11):
        """A small italic label in a rounded box, for naming a panel."""
        w = w or (0.35 + 0.075 * len(text))
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                    Inches(x), Inches(y), Inches(w), Inches(0.3))
        sh.fill.solid()
        sh.fill.fore_color.rgb = self.chip_fill
        sh.line.fill.background()
        sh.shadow.inherit = False
        tf = sh.text_frame
        tf.margin_left = tf.margin_right = Inches(0.08)
        tf.margin_top = tf.margin_bottom = Inches(0.02)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        set_text(tf, text, size=size, italic=True, color=self.dark, font=FONT)
        tf.paragraphs[0].alignment = CENTER
        return sh

    def takeaway(self, slide, lines, x, y, w, size=12):
        """One or more "-> ..." lines under a figure: what the figure shows."""
        tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(0.3 * len(lines)))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.1)
        tf.margin_top = tf.margin_bottom = Inches(0.03)
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.space_after = Pt(3)
            add_runs(p, "→ " + line, size=size, font=FONT)
        return tb

    def table(self, slide, rows, x, y, widths, size=12, row_h=0.32,
              align=None, highlight=None, colour=True):
        """A table styled to the deck: dark header, alternating rows.

        rows is a list of lists, the first being the header. highlight is the
        index of the row that carries the message; it gets a stronger tint and
        bold text. align is a per-column alignment list (RIGHT for numbers).
        """
        nr, nc = len(rows), len(rows[0])
        gs = slide.shapes.add_table(nr, nc, Inches(x), Inches(y),
                                    Inches(sum(widths)), Inches(row_h * nr))
        tbl = gs.table
        # Drop the stock table style, whose banding and header bar fight the
        # template.
        tblPr = tbl._tbl.tblPr
        for a in ("firstRow", "bandRow"):
            tblPr.set(a, "0")
        sid = tblPr.find(qn("a:tableStyleId"))
        if sid is not None:
            sid.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"   # No Style, No Grid
        for j, wdt in enumerate(widths):
            tbl.columns[j].width = Inches(wdt)
        head = RGBColor.from_string(self.target["dark"])
        tint = RGBColor.from_string(self.target["chip"])
        band = RGBColor.from_string(self.band)
        white = RGBColor(0xFF, 0xFF, 0xFF)
        for i, row in enumerate(rows):
            tbl.rows[i].height = Inches(row_h)
            for j, val in enumerate(row):
                c = tbl.cell(i, j)
                c.margin_left = c.margin_right = Inches(0.08)
                c.margin_top = c.margin_bottom = Inches(0.03)
                c.vertical_anchor = MSO_ANCHOR.MIDDLE
                if not colour:
                    c.fill.background()
                elif i == 0:
                    c.fill.solid(); c.fill.fore_color.rgb = head
                elif highlight is not None and i == highlight:
                    c.fill.solid(); c.fill.fore_color.rgb = tint
                else:
                    c.fill.solid(); c.fill.fore_color.rgb = band if i % 2 else white
                bold = i == 0 or j == 0 or (highlight is not None and i == highlight)
                col = white if (colour and i == 0) else None
                set_text(c.text_frame, val, size=size, bold=bold, color=col, font=FONT)
                if align and align[j]:
                    c.text_frame.paragraphs[0].alignment = align[j]
                for side in "TLR":
                    _border(c, side, None)
                _border(c, "B", self.target["dark"] if i == 0 else "D9D9D9",
                        12700 if i == 0 else 9525)
        return gs

    # -- output ----------------------------------------------------------
    def save(self, path, tmp=None):
        """Write the deck, applying the recolour and the footer.

        python-pptx writes first, then the XML parts are rewritten, because
        the colours are literal fills inside the layouts and master.
        """
        tmp = tmp or path + ".tmp"
        self.prs.save(tmp)
        sub = {SOURCE[k]: self.target[k] for k in SOURCE if SOURCE[k] != self.target[k]}
        with zipfile.ZipFile(tmp) as zin, zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                n = item.filename
                if n.endswith(".xml") and ("slideLayout" in n or "slideMaster" in n or "/slides/" in n):
                    txt = data.decode("utf8")
                    for a, b in sub.items():
                        txt = txt.replace(f'val="{a}"', f'val="{b}"').replace(f'val="{a.lower()}"', f'val="{b}"')
                    if self.footer_date:
                        txt = re.sub(r"\d{2} \w+ 20\d\d", self.footer_date, txt)
                    if self.footer_name and self.template_footer_name:
                        txt = txt.replace(f"<a:t>{self.template_footer_name}</a:t>",
                                          f"<a:t>{self.footer_name}</a:t>")
                    if self.footer_size and "slideLayout" in n:
                        # The footer name, date and page number are the only
                        # 15 pt text on the layouts.
                        txt = txt.replace('sz="1500"', f'sz="{int(self.footer_size) * 100}"')
                    data = txt.encode("utf8")
                zout.writestr(item, data)
        return path
