# -*- coding: utf-8 -*-
"""
Gerador de documento academico ABNT (PDF + DOCX) a partir de um Markdown-fonte.

Uso:  python gerar_documento.py <fonte.md> <saida_sem_extensao>

Sintaxe aceita no Markdown-fonte:
  :::meta ... :::        bloco de metadados da capa/folha de rosto
  # 1 TITULO             secao primaria (nova pagina, MAIUSCULA, negrito)
  # *REFERENCIAS         secao primaria sem numeracao (centralizada)
  ## 1.1 Titulo          secao secundaria (negrito)
  ### 1.1.1 Titulo       secao terciaria (negrito italico)
  ^Quadro 1 - Legenda    legenda que precede a tabela
  | a | b |              tabela
  !Fonte: ...            nota de fonte abaixo da tabela
  > texto                citacao direta longa (recuo 4 cm, corpo 10, entrelinha simples)
  - item                 lista com marcador
  1. item                lista numerada
  **negrito**  *italico* formatacao inline
"""
import io
import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (BaseDocTemplate, Flowable, Frame, Image, KeepTogether,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

# --------------------------------------------------------------------------- #
# Fontes
# --------------------------------------------------------------------------- #
FONTS = {"n": "Helvetica", "b": "Helvetica-Bold", "i": "Helvetica-Oblique",
         "bi": "Helvetica-BoldOblique"}
_win = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
_arial = {"n": "arial.ttf", "b": "arialbd.ttf", "i": "ariali.ttf", "bi": "arialbi.ttf"}
if all(os.path.exists(os.path.join(_win, f)) for f in _arial.values()):
    for k, f in _arial.items():
        name = "Arial" + {"n": "", "b": "-Bold", "i": "-Italic", "bi": "-BoldItalic"}[k]
        pdfmetrics.registerFont(TTFont(name, os.path.join(_win, f)))
        FONTS[k] = name
    pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold",
                                  italic="Arial-Italic", boldItalic="Arial-BoldItalic")

BASE, BOLD, ITAL = FONTS["n"], FONTS["b"], FONTS["i"]

# --------------------------------------------------------------------------- #
# Parser do Markdown-fonte
# --------------------------------------------------------------------------- #
def parse(path):
    with io.open(path, encoding="utf-8") as fh:
        raw = fh.read().replace("\r\n", "\n")

    meta = {}
    m = re.search(r":::meta\n(.*?)\n:::\n", raw, re.S)
    if m:
        for line in m.group(1).split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        raw = raw[m.end():]

    blocks, buf, tbl, i = [], [], [], 0
    lines = raw.split("\n")

    def flush_par():
        if buf:
            blocks.append(("p", " ".join(buf).strip()))
            del buf[:]

    def flush_tbl():
        if tbl:
            blocks.append(("table", list(tbl)))
            del tbl[:]

    while i < len(lines):
        ln = lines[i].rstrip()
        s = ln.strip()
        if not s:
            flush_par(); flush_tbl()
        elif s.startswith("|"):
            flush_par()
            cells = [c.strip() for c in s.strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                tbl.append(cells)
        elif s.startswith("@"):            # @caminho/figura.png | largura_cm
            flush_par(); flush_tbl()
            caminho, _, largura = s[1:].partition("|")
            caminho = os.path.join(os.path.dirname(os.path.abspath(path)), caminho.strip())
            blocks.append(("img", (caminho, float(largura or 16))))
        elif s.startswith("^"):
            flush_par(); flush_tbl()
            blocks.append(("caption", s[1:].strip()))
        elif s.startswith("!"):
            flush_par(); flush_tbl()
            blocks.append(("source", s[1:].strip()))
        elif s.startswith("> "):
            flush_par(); flush_tbl()
            q = [s[2:].strip()]
            while i + 1 < len(lines) and lines[i + 1].strip().startswith("> "):
                i += 1
                q.append(lines[i].strip()[2:].strip())
            blocks.append(("quote", " ".join(q)))
        elif s.startswith("### "):
            flush_par(); flush_tbl(); blocks.append(("h3", s[4:].strip()))
        elif s.startswith("## "):
            flush_par(); flush_tbl(); blocks.append(("h2", s[3:].strip()))
        elif s.startswith("# "):
            flush_par(); flush_tbl()
            t = s[2:].strip()
            blocks.append(("h1u", t[1:].strip()) if t.startswith("*") else ("h1", t))
        elif s.startswith("- "):
            flush_par(); flush_tbl(); blocks.append(("ul", s[2:].strip()))
        elif re.match(r"^\d+\.\s", s):
            flush_par(); flush_tbl()
            blocks.append(("ol", re.sub(r"^\d+\.\s", "", s)))
        else:
            flush_tbl(); buf.append(s)
        i += 1
    flush_par(); flush_tbl()
    return meta, blocks


def inline(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", t)
    return t


# --------------------------------------------------------------------------- #
# PDF
# --------------------------------------------------------------------------- #
LEAD = 14          # entrelinha simples para corpo 12 (padrao do modelo)
ML, MR, MT, MB = 3 * cm, 2 * cm, 3 * cm, 3 * cm
AVAIL = A4[0] - ML - MR

S = {
    "body": ParagraphStyle("body", fontName=BASE, fontSize=12, leading=LEAD,
                           alignment=TA_JUSTIFY, spaceAfter=6),
    "h1": ParagraphStyle("h1", fontName=BOLD, fontSize=12, leading=LEAD,
                         alignment=TA_LEFT, spaceBefore=12, spaceAfter=8),
    "h1c": ParagraphStyle("h1c", fontName=BOLD, fontSize=12, leading=LEAD,
                          alignment=TA_CENTER, spaceAfter=LEAD),
    "h1s": ParagraphStyle("h1s", fontName=BOLD, fontSize=12, leading=LEAD,
                          alignment=TA_CENTER, spaceAfter=LEAD),
    "h2": ParagraphStyle("h2", fontName=BOLD, fontSize=12, leading=LEAD,
                         alignment=TA_LEFT, spaceBefore=12, spaceAfter=6),
    "h3": ParagraphStyle("h3", fontName=BOLD, fontSize=12, leading=LEAD,
                         alignment=TA_LEFT, spaceBefore=10, spaceAfter=6),
    "quote": ParagraphStyle("quote", fontName=BASE, fontSize=10, leading=12,
                            alignment=TA_JUSTIFY, leftIndent=4 * cm,
                            spaceBefore=LEAD, spaceAfter=LEAD),
    "cap": ParagraphStyle("cap", fontName=BASE, fontSize=10, leading=12,
                          alignment=TA_LEFT, spaceBefore=LEAD, spaceAfter=3),
    "src": ParagraphStyle("src", fontName=BASE, fontSize=10, leading=12,
                          alignment=TA_LEFT, spaceBefore=3, spaceAfter=LEAD),
    "cell": ParagraphStyle("cell", fontName=BASE, fontSize=9, leading=11,
                           alignment=TA_LEFT),
    "cellh": ParagraphStyle("cellh", fontName=BOLD, fontSize=9, leading=11,
                            alignment=TA_LEFT),
    "li": ParagraphStyle("li", fontName=BASE, fontSize=12, leading=LEAD,
                         alignment=TA_JUSTIFY, leftIndent=1.0 * cm,
                         bulletIndent=0.3 * cm, spaceAfter=4),
    "ref": ParagraphStyle("ref", fontName=BASE, fontSize=12, leading=14,
                          alignment=TA_LEFT, spaceAfter=12),
    "capa": ParagraphStyle("capa", fontName=BOLD, fontSize=12, leading=LEAD,
                           alignment=TA_CENTER),
    "capan": ParagraphStyle("capan", fontName=BASE, fontSize=12, leading=LEAD,
                            alignment=TA_CENTER),
    "titulo": ParagraphStyle("titulo", fontName=BOLD, fontSize=14, leading=20,
                             alignment=TA_CENTER),
    "sub": ParagraphStyle("sub", fontName=BASE, fontSize=12, leading=LEAD,
                          alignment=TA_CENTER),
    "nat": ParagraphStyle("nat", fontName=BASE, fontSize=10, leading=12,
                          alignment=TA_JUSTIFY, leftIndent=8 * cm),
    "toc0": ParagraphStyle("toc0", fontName=BOLD, fontSize=12, leading=LEAD),
    "toc1": ParagraphStyle("toc1", fontName=BASE, fontSize=12, leading=LEAD,
                           leftIndent=0.7 * cm),
    "toc2": ParagraphStyle("toc2", fontName=BASE, fontSize=12, leading=LEAD,
                           leftIndent=1.4 * cm),
}

STATE = {"first_textual": 10 ** 6, "used": 10 ** 6}


class TextualMark(Flowable):
    """Marcador que registra em que pagina fisica comeca a parte textual."""
    def wrap(self, aw, ah):
        return (0, 0)

    def draw(self):
        STATE["first_textual"] = min(STATE["first_textual"],
                                     self.canv.getPageNumber())


def _page(canvas, doc):
    n = canvas.getPageNumber()
    if n > 1:                       # a capa nao recebe numeracao
        canvas.setFont(BASE, 10)
        canvas.drawRightString(A4[0] - MR, 1.6 * cm, str(n))


class Doc(BaseDocTemplate):
    def __init__(self, path, toc):
        BaseDocTemplate.__init__(self, path, pagesize=A4, leftMargin=ML,
                                 rightMargin=MR, topMargin=MT, bottomMargin=MB,
                                 title="Projeto Radice - Etapa 1")
        frame = Frame(ML, MB, AVAIL, A4[1] - MT - MB, id="f",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=_page)])
        self.toc = toc

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            st = flowable.style.name
            if st in ("h1", "h1c", "h2", "h3"):
                lvl = {"h1": 0, "h1c": 0, "h2": 1, "h3": 2}[st]
                txt = re.sub(r"<[^>]+>", "", flowable.getPlainText())
                self.notify("TOCEntry", (lvl, txt, self.page))


def col_widths(rows):
    ncol = max(len(r) for r in rows)
    weights = []
    for c in range(ncol):
        w = max(len(r[c]) if c < len(r) else 0 for r in rows)
        weights.append(max(6.0, min(float(w), 46.0)))
    tot = sum(weights)
    return [AVAIL * w / tot for w in weights]


def make_table(rows, kind):
    ncol = max(len(r) for r in rows)
    data = []
    for ri, r in enumerate(rows):
        r = list(r) + [""] * (ncol - len(r))
        st = S["cellh"] if ri == 0 else S["cell"]
        data.append([Paragraph(inline(c), st) for c in r])
    t = Table(data, colWidths=col_widths(rows), repeatRows=1, hAlign="LEFT")
    grey = colors.Color(0.90, 0.90, 0.90)
    line = colors.Color(0.35, 0.35, 0.35)
    cmds = [("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, 0), grey),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    if kind == "tabela":                      # padrao IBGE: laterais abertas
        cmds += [("LINEABOVE", (0, 0), (-1, 0), 0.9, line),
                 ("LINEBELOW", (0, 0), (-1, 0), 0.7, line),
                 ("LINEBELOW", (0, -1), (-1, -1), 0.9, line)]
    else:                                     # quadro: moldura fechada
        cmds += [("GRID", (0, 0), (-1, -1), 0.5, line),
                 ("BOX", (0, 0), (-1, -1), 0.9, line)]
    t.setStyle(TableStyle(cmds))
    return t


def build_story(meta, blocks, toc):
    st = []
    au = [a.strip() for a in meta.get("autores", "").split(";") if a.strip()]

    # ---- capa (instituicao, autores, titulo, natureza e orientador)
    st.append(Paragraph(meta["instituicao"], S["capa"]))
    st.append(Paragraph(meta.get("curso", ""), S["capan"]))
    if meta.get("unidade"):
        st.append(Paragraph(meta["unidade"], S["capan"]))
    st.append(Spacer(1, 2.6 * cm))
    for a in au:
        st.append(Paragraph(a, S["capan"]))
    st.append(Spacer(1, 3.0 * cm))
    st.append(Paragraph(meta["titulo"], S["titulo"]))
    if meta.get("etapa"):
        st.append(Spacer(1, 0.4 * cm))
        st.append(Paragraph(meta["etapa"], S["sub"]))
    st.append(Spacer(1, 2.2 * cm))
    st.append(Paragraph(meta.get("natureza", ""), S["nat"]))
    if meta.get("orientador"):
        st.append(Spacer(1, 0.4 * cm))
        st.append(Paragraph("Orientador: " + meta["orientador"], S["nat"]))
    st.append(Spacer(1, 2.2 * cm))
    st.append(Paragraph(meta.get("local", ""), S["capan"]))
    st.append(Paragraph(str(meta.get("ano", "")), S["capan"]))
    st.append(PageBreak())

    # ---- sumario
    st.append(Paragraph("SUMÁRIO", S["h1s"]))
    toc.levelStyles = [S["toc0"], S["toc1"], S["toc2"]]
    toc.dotsMinLevel = 0
    st.append(toc)

    # ---- corpo
    quebra = str(meta.get("quebra_secao", "sim")).strip().lower() not in ("nao", "não")
    in_refs = False
    first_h1 = True
    pend_cap = None
    for kind, val in blocks:
        if kind in ("h1", "h1u"):
            if first_h1 or quebra:
                st.append(PageBreak())
            if first_h1:
                st.append(TextualMark())
                first_h1 = False
            in_refs = kind == "h1u" or "REFER" in val.upper()
            st.append(Paragraph(inline(val.upper()),
                                S["h1c"] if kind == "h1u" else S["h1"]))
        elif kind == "h2":
            st.append(Paragraph(inline(val), S["h2"]))
        elif kind == "h3":
            st.append(Paragraph(inline(val), S["h3"]))
        elif kind == "p":
            st.append(Paragraph(inline(val), S["ref"] if in_refs else S["body"]))
        elif kind == "quote":
            st.append(Paragraph(inline(val), S["quote"]))
        elif kind == "ul":
            st.append(Paragraph(inline(val), S["li"], bulletText="\u2022"))
        elif kind == "ol":
            st.append(Paragraph(inline(val), S["li"], bulletText="\u2013"))
        elif kind == "caption":
            pend_cap = val
        elif kind == "table":
            kindt = "tabela" if (pend_cap or "").lower().startswith("tabela") else "quadro"
            grp = []
            if pend_cap:
                grp.append(Paragraph(inline(pend_cap), S["cap"]))
                pend_cap = None
            grp.append(make_table(val, kindt))
            st.append(KeepTogether(grp) if len(val) <= 8 else grp[0])
            if len(val) > 8:
                st.append(grp[1])
        elif kind == "img":
            caminho, largura = val
            iw, ih = ImageReader(caminho).getSize()
            w = min(largura * cm, AVAIL)
            grp = []
            if pend_cap:
                grp.append(Paragraph(inline(pend_cap), S["cap"]))
                pend_cap = None
            grp.append(Image(caminho, width=w, height=w * ih / iw, hAlign="LEFT"))
            st.append(KeepTogether(grp))
        elif kind == "source":
            par = Paragraph(inline(val), S["src"])
            if st and isinstance(st[-1], KeepTogether):
                st[-1]._content.append(par)   # fonte fica colada ao quadro
            else:
                st.append(par)
    return st


def build_pdf(meta, blocks, out):
    toc = TableOfContents()
    for _ in range(4):
        STATE["first_textual"] = 10 ** 6
        doc = Doc(out, toc)
        doc.multiBuild(build_story(meta, blocks, toc))
        if STATE["first_textual"] == STATE["used"]:
            break
        STATE["used"] = STATE["first_textual"]
    return out


# --------------------------------------------------------------------------- #
# DOCX
# --------------------------------------------------------------------------- #
def build_docx(meta, blocks, out):
    import docx
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt

    d = docx.Document()
    sec = d.sections[0]
    sec.left_margin, sec.right_margin = Cm(3), Cm(2)
    sec.top_margin, sec.bottom_margin = Cm(3), Cm(3)

    normal = d.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(12)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    pf = normal.paragraph_format
    pf.line_spacing = 1.0
    pf.space_after = Pt(5)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # numero de pagina no canto superior direito
    hp = sec.footer.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = hp.add_run()
    for el, attr in (("w:fldChar", {"w:fldCharType": "begin"}),
                     ("w:instrText", None),
                     ("w:fldChar", {"w:fldCharType": "end"})):
        e = OxmlElement(el)
        if el == "w:instrText":
            e.set(qn("xml:space"), "preserve")
            e.text = " PAGE "
        for k, v in (attr or {}).items():
            e.set(qn(k), v)
        r._r.append(e)
    sec.different_first_page_header_footer = True

    def par(text, style=None, align=None, bold=False, italic=False, size=None,
            indent=None, left=None, spacing=None, first=None):
        p = d.add_paragraph()
        if align is not None:
            p.alignment = align
        if left is not None:
            p.paragraph_format.left_indent = left
        if first is not None:
            p.paragraph_format.first_line_indent = first
        if spacing is not None:
            p.paragraph_format.line_spacing = spacing
        for chunk, b, i in split_runs(text):
            run = p.add_run(chunk)
            run.bold = bold or b
            run.italic = italic or i
            run.font.name = "Arial"
            if size:
                run.font.size = Pt(size)
        return p

    def split_runs(t):
        out, pos = [], 0
        for m in re.finditer(r"\*\*(.+?)\*\*|(?<!\*)\*([^*]+?)\*(?!\*)", t):
            if m.start() > pos:
                out.append((t[pos:m.start()], False, False))
            out.append((m.group(1) or m.group(2), m.group(1) is not None,
                        m.group(2) is not None))
            pos = m.end()
        if pos < len(t):
            out.append((t[pos:], False, False))
        return out or [(t, False, False)]

    C, J, L = (WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.JUSTIFY,
               WD_ALIGN_PARAGRAPH.LEFT)
    au = [a.strip() for a in meta.get("autores", "").split(";") if a.strip()]

    par(meta["instituicao"], align=C, bold=True)
    par(meta.get("curso", ""), align=C)
    if meta.get("unidade"):
        par(meta["unidade"], align=C)
    for _ in range(6):
        par("", align=C)
    for a in au:
        par(a, align=C)
    for _ in range(7):
        par("", align=C)
    par(meta["titulo"], align=C, bold=True, size=14)
    par("", align=C)
    par(meta.get("etapa", ""), align=C)
    for _ in range(4):
        par("", align=C)
    par(meta.get("natureza", ""), align=J, size=10, left=Cm(8))
    par("", align=J)
    par("Orientador: " + meta.get("orientador", ""), align=J, size=10, left=Cm(8))
    for _ in range(4):
        par("", align=C)
    par(meta.get("local", ""), align=C)
    par(str(meta.get("ano", "")), align=C)
    d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    par("SUMÁRIO", align=C, bold=True)
    par("")
    p = d.add_paragraph()
    r = p.add_run()
    b = OxmlElement("w:fldChar"); b.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve")
    it.text = r' TOC \o "1-3" \h \z \u '
    sp = OxmlElement("w:fldChar"); sp.set(qn("w:fldCharType"), "separate")
    tx = OxmlElement("w:t"); tx.text = "Clique com o botao direito e escolha 'Atualizar campo' para gerar o sumario."
    en = OxmlElement("w:fldChar"); en.set(qn("w:fldCharType"), "end")
    for e in (b, it, sp, tx, en):
        r._r.append(e)
    d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    quebra = str(meta.get("quebra_secao", "sim")).strip().lower() not in ("nao", "não")
    in_refs, first_h1, pend_cap = False, True, None
    for kind, val in blocks:
        if kind in ("h1", "h1u"):
            if not first_h1 and quebra:
                d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
            first_h1 = False
            in_refs = kind == "h1u" or "REFER" in val.upper()
            h = d.add_heading(level=1)
            h.alignment = C if in_refs else L
            run = h.add_run(re.sub(r"\*", "", val).upper())
            run.bold = True
            run.font.name = "Arial"
            run.font.size = Pt(12)
            run.font.color.rgb = docx.shared.RGBColor(0, 0, 0)
            par("")
        elif kind == "h2":
            h = d.add_heading(level=2)
            h.alignment = L
            run = h.add_run(re.sub(r"\*", "", val))
            run.bold = True
            run.font.name = "Arial"
            run.font.size = Pt(12)
            run.font.color.rgb = docx.shared.RGBColor(0, 0, 0)
        elif kind == "h3":
            h = d.add_heading(level=3)
            h.alignment = L
            run = h.add_run(re.sub(r"\*", "", val))
            run.bold = True
            run.italic = True
            run.font.name = "Arial"
            run.font.size = Pt(12)
            run.font.color.rgb = docx.shared.RGBColor(0, 0, 0)
        elif kind == "p":
            if in_refs:
                par(val, align=L, spacing=1.0)
                par("", spacing=1.0)
            else:
                par(val, align=J)
        elif kind == "quote":
            par(val, align=J, size=10, left=Cm(4), spacing=1.0)
            par("")
        elif kind == "ul":
            p = d.add_paragraph(style="List Bullet")
            p.alignment = J
            for chunk, bo, itl in split_runs(val):
                rr = p.add_run(chunk); rr.bold = bo; rr.italic = itl
                rr.font.name = "Arial"; rr.font.size = Pt(12)
        elif kind == "ol":
            p = d.add_paragraph(style="List Number")
            p.alignment = J
            for chunk, bo, itl in split_runs(val):
                rr = p.add_run(chunk); rr.bold = bo; rr.italic = itl
                rr.font.name = "Arial"; rr.font.size = Pt(12)
        elif kind == "caption":
            pend_cap = val
        elif kind == "table":
            if pend_cap:
                par(pend_cap, align=L, size=10, spacing=1.0)
                pend_cap = None
            ncol = max(len(r) for r in val)
            t = d.add_table(rows=0, cols=ncol)
            t.style = "Table Grid"
            for ri, row in enumerate(val):
                row = list(row) + [""] * (ncol - len(row))
                cells = t.add_row().cells
                for ci, c in enumerate(row):
                    cp = cells[ci].paragraphs[0]
                    cp.alignment = L
                    cp.paragraph_format.line_spacing = 1.0
                    for chunk, bo, itl in split_runs(c):
                        rr = cp.add_run(chunk)
                        rr.bold = bo or ri == 0
                        rr.italic = itl
                        rr.font.name = "Arial"
                        rr.font.size = Pt(9)
        elif kind == "img":
            if pend_cap:
                par(pend_cap, align=L, size=10, spacing=1.0)
                pend_cap = None
            d.add_picture(val[0], width=Cm(val[1]))
            d.paragraphs[-1].alignment = L
        elif kind == "source":
            par(val, align=L, size=10, spacing=1.0)
            par("")
    d.save(out)
    return out


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    src = sys.argv[1]
    stem = sys.argv[2]
    meta, blocks = parse(src)
    print("blocos:", len(blocks))
    build_pdf(meta, blocks, stem + ".pdf")
    print("PDF   ->", stem + ".pdf")
    build_docx(meta, blocks, stem + ".docx")
    print("DOCX  ->", stem + ".docx")
