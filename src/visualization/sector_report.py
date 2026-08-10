"""Reusable builder for the long-horizon sector analysis PDFs.

The sector reports all share one visual language: a dark title page, section
headers with a rule, tier tables colour-coded by conviction, and callout boxes
for the parts an investor is most likely to get wrong. Each sector script
supplies content; this module owns the layout.
"""

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# Palette. Ink is near-black rather than pure black so long passages read
# softer on screen; accent is the colour used for rules and tier-1 emphasis.
INK = colors.HexColor("#141821")
MUTED = colors.HexColor("#5A6472")
ACCENT = colors.HexColor("#1F6F8B")
RULE = colors.HexColor("#C9D2DB")
BAND = colors.HexColor("#EEF3F7")
WARN_BG = colors.HexColor("#FDF3E3")
WARN_ED = colors.HexColor("#D9A441")
KEY_BG = colors.HexColor("#E8F1F5")

# Tier colours run from strongest conviction (deep teal) to weakest (grey).
TIER_COLORS = [
    colors.HexColor("#1F6F8B"),
    colors.HexColor("#3E8FA6"),
    colors.HexColor("#7FAEBE"),
    colors.HexColor("#A9A9A9"),
    colors.HexColor("#8C8C8C"),
]

PAGE_W, PAGE_H = A4
MARGIN = 2.0 * cm


def _styles():
    ss = getSampleStyleSheet()
    s = {}
    s["title"] = ParagraphStyle(
        "title", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=30,
        leading=35, textColor=colors.white, alignment=TA_CENTER, spaceAfter=0,
    )
    s["subtitle"] = ParagraphStyle(
        "subtitle", parent=ss["Normal"], fontName="Helvetica", fontSize=13,
        leading=18, textColor=colors.HexColor("#B9C6D2"), alignment=TA_CENTER,
    )
    s["kicker"] = ParagraphStyle(
        "kicker", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=9,
        leading=12, textColor=colors.HexColor("#7FAEBE"), alignment=TA_CENTER,
    )
    s["h1"] = ParagraphStyle(
        "h1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=17,
        leading=21, textColor=INK, spaceBefore=6, spaceAfter=2,
    )
    s["h2"] = ParagraphStyle(
        "h2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=12.5,
        leading=16, textColor=ACCENT, spaceBefore=12, spaceAfter=4,
    )
    s["body"] = ParagraphStyle(
        "body", parent=ss["Normal"], fontName="Helvetica", fontSize=9.8,
        leading=14.2, textColor=INK, alignment=TA_JUSTIFY, spaceAfter=6,
    )
    s["lead"] = ParagraphStyle(
        "lead", parent=s["body"], fontSize=11, leading=16,
        textColor=colors.HexColor("#2B3240"),
    )
    s["bullet"] = ParagraphStyle(
        "bullet", parent=s["body"], leftIndent=12, bulletIndent=2, spaceAfter=3,
    )
    s["cell"] = ParagraphStyle(
        "cell", parent=ss["Normal"], fontName="Helvetica", fontSize=7.8,
        leading=10.2, textColor=INK,
    )
    s["cellb"] = ParagraphStyle(
        "cellb", parent=s["cell"], fontName="Helvetica-Bold",
    )
    s["cellh"] = ParagraphStyle(
        "cellh", parent=s["cell"], fontName="Helvetica-Bold",
        textColor=colors.white,
    )
    s["callout"] = ParagraphStyle(
        "callout", parent=s["body"], fontSize=9.4, leading=13.4, spaceAfter=0,
    )
    s["calloutH"] = ParagraphStyle(
        "calloutH", parent=s["body"], fontName="Helvetica-Bold", fontSize=9.4,
        leading=13.4, spaceAfter=3, textColor=INK,
    )
    s["caption"] = ParagraphStyle(
        "caption", parent=s["body"], fontSize=8.2, leading=11,
        textColor=MUTED, alignment=TA_CENTER, spaceBefore=3,
    )
    s["foot"] = ParagraphStyle(
        "foot", parent=s["body"], fontSize=8.2, leading=11, textColor=MUTED,
    )
    return s


S = _styles()


# --------------------------------------------------------------------------
# Flowable helpers
# --------------------------------------------------------------------------

def h1(text, num=None):
    """Section header with a rule under it."""
    label = f"{num}. {text}" if num else text
    bar = Table([[""]], colWidths=[PAGE_W - 2 * MARGIN], rowHeights=[1.6])
    bar.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ACCENT)]))
    return KeepTogether([Spacer(1, 10), Paragraph(label, S["h1"]), bar, Spacer(1, 7)])


def h2(text):
    return Paragraph(text, S["h2"])


def p(text, style="body"):
    return Paragraph(text, S[style])


def bullets(items):
    return [Paragraph(f"&bull;&nbsp;&nbsp;{i}", S["bullet"]) for i in items]


def _box(title, text, bg, edge):
    inner = []
    if title:
        inner.append(Paragraph(title, S["calloutH"]))
    inner.append(Paragraph(text, S["callout"]))
    t = Table([[inner]], colWidths=[PAGE_W - 2 * MARGIN])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0.8, edge),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return KeepTogether([Spacer(1, 4), t, Spacer(1, 8)])


def key_box(title, text):
    """Blue box: the load-bearing insight of a section."""
    return _box(title, text, KEY_BG, ACCENT)


def warn_box(title, text):
    """Amber box: the caveat, the thing that breaks the thesis."""
    return _box(title, text, WARN_BG, WARN_ED)


def table(header, rows, widths, align_right=(), font_size=7.8):
    """Standard data table. `rows` are lists of already-plain strings."""
    data = [[Paragraph(c, S["cellh"]) for c in header]]
    for r in rows:
        data.append([Paragraph(str(c), S["cell"]) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, RULE),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), BAND))
    for c in align_right:
        style.append(("ALIGN", (c, 0), (c, -1), "CENTER"))
    t.setStyle(TableStyle(style))
    return t


def tier_table(tier_idx, title, header, rows, widths, align_right=()):
    """A ranking tier: coloured caption bar plus the table beneath it."""
    col = TIER_COLORS[min(tier_idx, len(TIER_COLORS) - 1)]

    # Caption and column header live inside the same table as rows 0 and 1 and
    # are set to repeat, so a long tier can split across pages without leaving
    # a half-empty page behind it or an orphaned caption bar.
    ncols = len(header)
    data = [[Paragraph(title, S["cellh"])] + [""] * (ncols - 1)]
    data.append([Paragraph(c, S["cellb"]) for c in header])
    for r in rows:
        data.append([Paragraph(str(c), S["cell"]) for c in r])

    t = Table(data, colWidths=widths, repeatRows=2)
    style = [
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), col),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#DCE5EC")),
        ("TOPPADDING", (0, 0), (-1, 0), 5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 1), (-1, -1), 0.4, RULE),
        ("LINEBEFORE", (0, 0), (0, -1), 2.2, col),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 1), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 3.5),
    ]
    for i in range(2, len(data)):
        if i % 2 == 1:
            style.append(("BACKGROUND", (0, i), (-1, i), BAND))
    for c in align_right:
        style.append(("ALIGN", (c, 1), (c, -1), "CENTER"))
    t.setStyle(TableStyle(style))
    return [Spacer(1, 9), t, Spacer(1, 5)]


def chart(path, width_cm=16.0):
    from PIL import Image as PILImage
    with PILImage.open(path) as im:
        w, h = im.size
    w_pt = width_cm * cm
    return Image(path, width=w_pt, height=w_pt * h / w)


# --------------------------------------------------------------------------
# Document assembly
# --------------------------------------------------------------------------

class _Doc(BaseDocTemplate):
    def __init__(self, filename, footer_label, **kw):
        super().__init__(filename, pagesize=A4, leftMargin=MARGIN,
                         rightMargin=MARGIN, topMargin=MARGIN,
                         bottomMargin=1.7 * cm, **kw)
        self.footer_label = footer_label
        frame = Frame(MARGIN, 1.7 * cm, PAGE_W - 2 * MARGIN,
                      PAGE_H - MARGIN - 1.7 * cm, id="body")
        cover = Frame(0, 0, PAGE_W, PAGE_H, id="cover",
                      leftPadding=0, rightPadding=0,
                      topPadding=0, bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[cover], onPage=self._cover_bg),
            PageTemplate(id="body", frames=[frame], onPage=self._chrome),
        ])

    def _cover_bg(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(INK)
        canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
        canvas.setFillColor(ACCENT)
        canvas.rect(0, PAGE_H - 0.5 * cm, PAGE_W, 0.5 * cm, stroke=0, fill=1)
        canvas.restoreState()

    def _chrome(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, PAGE_H - MARGIN + 0.35 * cm,
                    PAGE_W - MARGIN, PAGE_H - MARGIN + 0.35 * cm)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN, PAGE_H - MARGIN + 0.55 * cm, self.footer_label)
        canvas.line(MARGIN, 1.35 * cm, PAGE_W - MARGIN, 1.35 * cm)
        canvas.drawRightString(PAGE_W - MARGIN, 0.95 * cm, str(doc.page - 1))
        canvas.drawString(MARGIN, 0.95 * cm,
                          "Análisis para decisión propia — no es asesoramiento financiero")
        canvas.restoreState()


def cover(title, subtitle, kicker, meta_rows):
    """Title-page flowables. `meta_rows` is a list of (label, value)."""
    out = [Spacer(1, 6.2 * cm), Paragraph(kicker, S["kicker"]), Spacer(1, 0.7 * cm)]
    out.append(Paragraph(title, S["title"]))
    out.append(Spacer(1, 0.7 * cm))

    rule = Table([[""]], colWidths=[6 * cm], rowHeights=[1.5])
    rule.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ACCENT)]))
    rule.hAlign = "CENTER"
    out += [rule, Spacer(1, 0.7 * cm), Paragraph(subtitle, S["subtitle"])]

    meta_style = ParagraphStyle(
        "meta", fontName="Helvetica", fontSize=9, leading=15,
        textColor=colors.HexColor("#98A6B4"), alignment=TA_CENTER,
    )
    out.append(Spacer(1, 2.4 * cm))
    for label, value in meta_rows:
        out.append(Paragraph(
            f'<font color="#63707E">{label}</font>&nbsp;&nbsp;{value}', meta_style))
    out.append(NextPageTemplate("body"))
    out.append(PageBreak())
    return out


def build(filename, footer_label, story):
    _Doc(filename, footer_label).build(story)
    return filename
