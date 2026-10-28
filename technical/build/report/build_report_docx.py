#!/usr/bin/env python3
"""Render a Markdown report to DOCX (python-docx) from the SINGLE canonical Markdown source.

    python build_report_docx.py <report.md> <out.docx> [--base-dir DIR]

The Markdown file is the only source of text: the DOCX is generated from it programmatically
(no second hand-maintained copy), so the two cannot diverge. PDF export + TOC/page-number field
update is done afterwards with Microsoft Word automation (export_pdf.ps1).

Supported Markdown: front-matter-free; # / ## / ### headings, paragraphs, bullet/ordered lists
(nested), pipe tables, fenced code, block quotes, images (+ italic caption paragraph that follows),
inline **bold**, *italic*, `code`, [links](url), and '---' rules (ignored). A line containing only
`<!-- pagebreak -->` forces a page break; `<!-- toc -->` marks the table-of-contents location;
`<!-- titlepage ... -->` blocks are handled by build script constants (see TITLE_*).
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from markdown_it import MarkdownIt
from PIL import Image

NAVY = RGBColor(0x14, 0x2B, 0x4D)
GREY = RGBColor(0x55, 0x5B, 0x66)
BODY_FONT = "Calibri"
MONO_FONT = "Consolas"


def set_cell_shading(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def set_repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def no_split_row(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:cantSplit")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def add_field(run, instr):
    for t, txt in (("begin", None), (None, instr), ("separate", None), (None, "1"), ("end", None)):
        if t:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), t)
            run._r.append(el)
        elif txt == instr:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = instr
            run._r.append(it)
        else:
            tx = OxmlElement("w:t")
            tx.text = txt
            run._r.append(tx)


def add_hyperlink(paragraph, text, url, size=None):
    part = paragraph.part
    r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
                          is_external=True)
    h = OxmlElement("w:hyperlink")
    h.set(qn("r:id"), r_id)
    r = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    c = OxmlElement("w:color")
    c.set(qn("w:val"), "1F4E9C")
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rPr.append(c)
    rPr.append(u)
    if size:
        sz = OxmlElement("w:sz")
        sz.set(qn("w:val"), str(int(size * 2)))
        rPr.append(sz)
    r.append(rPr)
    t = OxmlElement("w:t")
    t.text = text
    t.set(qn("xml:space"), "preserve")
    r.append(t)
    h.append(r)
    paragraph._p.append(h)


def fmt_runs(paragraph, inline_tokens, size=None, base_italic=False, base_bold=False, color=None):
    bold = em = False
    link = None
    for tk in inline_tokens:
        t = tk.type
        if t == "strong_open":
            bold = True
        elif t == "strong_close":
            bold = False
        elif t == "em_open":
            em = True
        elif t == "em_close":
            em = False
        elif t == "link_open":
            link = dict(tk.attrs).get("href")
        elif t == "link_close":
            link = None
        elif t in ("softbreak", "hardbreak"):
            paragraph.add_run(" ")
        elif t == "html_inline":
            continue
        elif t in ("text", "code_inline"):
            if link and t == "text":
                add_hyperlink(paragraph, tk.content, link, size)
                continue
            r = paragraph.add_run(tk.content)
            r.bold = bold or base_bold
            r.italic = em or base_italic
            if t == "code_inline":
                r.font.name = MONO_FONT
                r._element.rPr.rFonts.set(qn("w:eastAsia"), MONO_FONT)
                r.font.size = Pt((size or 10.5) - 1)
                r.font.color.rgb = RGBColor(0x7A, 0x1F, 0x3D)
            else:
                if size:
                    r.font.size = Pt(size)
                if color:
                    r.font.color.rgb = color
        elif t == "image":
            continue


def setup_document():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.2)
    sec.top_margin, sec.bottom_margin = Cm(2.2), Cm(2.0)
    st = doc.styles["Normal"]
    st.font.name = BODY_FONT
    st.font.size = Pt(10.5)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
    st.paragraph_format.space_after = Pt(6)
    st.paragraph_format.line_spacing = 1.12
    for name, size, before, after in (("Heading 1", 17, 18, 8), ("Heading 2", 13.5, 14, 5), ("Heading 3", 11.5, 10, 3)):
        h = doc.styles[name]
        h.font.name = BODY_FONT
        h.element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
        h.element.rPr.rFonts.set(qn("w:ascii"), BODY_FONT)
        h.element.rPr.rFonts.set(qn("w:hAnsi"), BODY_FONT)
        h.font.size = Pt(size)
        h.font.bold = True
        h.font.color.rgb = NAVY
        h.paragraph_format.space_before = Pt(before)
        h.paragraph_format.space_after = Pt(after)
        h.paragraph_format.keep_with_next = True
    return doc


def add_page_break(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def title_page(doc, meta):
    for _ in range(4):
        doc.add_paragraph()
    p = doc.add_paragraph()
    r = p.add_run(meta["title"])
    r.bold = True
    r.font.size = Pt(26)
    r.font.color.rgb = NAVY
    p.paragraph_format.space_after = Pt(8)
    p = doc.add_paragraph()
    r = p.add_run(meta["subtitle"])
    r.font.size = Pt(14)
    r.font.color.rgb = GREY
    p.paragraph_format.space_after = Pt(28)
    for k, v in meta["fields"]:
        p = doc.add_paragraph()
        r = p.add_run(k + ": ")
        r.bold = True
        r.font.size = Pt(11)
        if v.startswith(("https://", "http://")):
            add_hyperlink(p, v, v, size=11)
        else:
            r2 = p.add_run(v)
            r2.font.size = Pt(11)
        p.paragraph_format.space_after = Pt(3)
    doc.add_paragraph()
    p = doc.add_paragraph()
    r = p.add_run(meta["status"])
    r.italic = True
    r.font.size = Pt(10)
    r.font.color.rgb = GREY
    add_page_break(doc)


def add_toc(doc):
    p = doc.add_paragraph()
    r = p.add_run("Contents")
    r.bold = True
    r.font.size = Pt(17)
    r.font.color.rgb = NAVY
    p = doc.add_paragraph()
    add_field(p.add_run(), 'TOC \\o "1-2" \\h \\z \\u')
    add_page_break(doc)


def footer_header(doc, short_title):
    sec = doc.sections[0]
    sec.different_first_page_header_footer = True
    hp = sec.header.paragraphs[0]
    hp.text = short_title
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for r in hp.runs:
        r.font.size = Pt(8.5)
        r.font.color.rgb = GREY
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run("Page ")
    r.font.size = Pt(8.5)
    r2 = fp.add_run()
    r2.font.size = Pt(8.5)
    add_field(r2, "PAGE")


def render_table(doc, rows, header=True):
    ncol = max(len(r) for r in rows)
    t = doc.add_table(rows=len(rows), cols=ncol)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = True
    size = 9 if ncol <= 5 else 8
    if ncol >= 7:
        size = 7.5
    for i, row in enumerate(rows):
        for j in range(ncol):
            cell = t.cell(i, j)
            cell.text = ""
            par = cell.paragraphs[0]
            par.paragraph_format.space_after = Pt(1)
            par.paragraph_format.space_before = Pt(1)
            par.paragraph_format.line_spacing = 1.0
            toks = row[j] if j < len(row) else []
            fmt_runs(par, toks, size=size, base_bold=(i == 0 and header))
            if i == 0 and header:
                set_cell_shading(cell, "DCE4F0")
                par.paragraph_format.keep_with_next = True
        no_split_row(t.rows[i])
    if header:
        set_repeat_header(t.rows[0])
    # column widths proportional to content (python-docx/Word default to equal thirds otherwise)
    def cell_len(toks):
        return sum(len(tk.content) for tk in toks if tk.type in ("text", "code_inline"))
    weights = []
    for j in range(ncol):
        lens = [cell_len(r[j]) if j < len(r) else 0 for r in rows]
        weights.append(max(4.0, 0.6 * max(lens) + 0.4 * (sum(lens) / len(lens))))
    total_w = 16.6
    widths = [max(2.3 if ncol <= 4 else 1.3, total_w * w / sum(weights)) for w in weights]
    scale = total_w / sum(widths)
    widths = [w * scale for w in widths]
    t.autofit = False
    tblPr = t._tbl.tblPr
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tblPr.append(lay)
    for j, wcm in enumerate(widths):
        t.columns[j].width = Cm(wcm)
        for r_ in t.rows:
            r_.cells[j].width = Cm(wcm)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def build(md_path, out_path, base_dir):
    md = MarkdownIt("commonmark", {"html": True}).enable("table")
    text = Path(md_path).read_text(encoding="utf8")
    tokens = md.parse(text)
    doc = setup_document()
    meta = {}
    # title-page metadata is declared in an HTML comment block at the top of the Markdown
    m = re.search(r"<!--\s*titlepage\s*(.*?)-->", text, re.S)
    if m:
        block = m.group(1)
        meta["title"] = re.search(r"^title:\s*(.+)$", block, re.M).group(1).strip()
        meta["subtitle"] = re.search(r"^subtitle:\s*(.+)$", block, re.M).group(1).strip()
        meta["status"] = re.search(r"^status:\s*(.+)$", block, re.M).group(1).strip()
        meta["fields"] = [tuple(x.strip() for x in ln[len("field:"):].split("|", 1))
                          for ln in block.splitlines() if ln.startswith("field:")]
        meta["short"] = re.search(r"^short:\s*(.+)$", block, re.M).group(1).strip()
        title_page(doc, meta)
        footer_header(doc, meta["short"])
    i = 0
    list_stack = []   # entries: ["bullet"|"ordered", counter]
    pending_caption_ok = False
    n_img = 0
    while i < len(tokens):
        tk = tokens[i]
        t = tk.type
        if t == "html_block":
            c = tk.content.strip()
            if c.startswith("<!-- toc"):
                add_toc(doc)
            elif c.startswith("<!-- pagebreak"):
                add_page_break(doc)
            i += 1
            continue
        if t == "heading_open":
            lvl = int(tk.tag[1])
            inline = tokens[i + 1]
            h = doc.add_heading("", level=min(lvl, 3))
            if lvl == 1 and meta and inline.content.strip() == meta.get("title"):
                # skip duplicate title heading
                h._element.getparent().remove(h._element)
            else:
                for r in h.runs:
                    r.text = ""
                fmt_runs(h, inline.children)
                for r in h.runs:
                    r.font.color.rgb = NAVY
                    r.font.name = BODY_FONT
                    r.bold = True
                if lvl <= 2 and doc.paragraphs and lvl == 2 and inline.content.strip()[:2] in ("1.",) and False:
                    pass
            i += 3
            continue
        if t in ("bullet_list_open", "ordered_list_open"):
            list_stack.append(["bullet" if t == "bullet_list_open" else "ordered", 0])
            i += 1
            continue
        if t in ("bullet_list_close", "ordered_list_close"):
            list_stack.pop()
            i += 1
            continue
        if t == "list_item_open":
            list_stack[-1][1] += 1
            i += 1
            continue
        if t == "paragraph_open":
            inline = tokens[i + 1]
            # image paragraph
            imgs = [c for c in inline.children if c.type == "image"]
            if imgs and len(inline.children) == 1:
                src = dict(imgs[0].attrs)["src"]
                p_img = (Path(base_dir) / src).resolve()
                par = doc.add_paragraph()
                par.alignment = WD_ALIGN_PARAGRAPH.CENTER
                par.paragraph_format.keep_with_next = True
                par.paragraph_format.space_after = Pt(2)
                with Image.open(p_img) as im:
                    w, h = im.size
                max_w, max_h = 16.2, 17.0
                wcm = min(max_w, max_h * w / h)
                par.add_run().add_picture(str(p_img), width=Cm(wcm))
                n_img += 1
                i += 3
                continue
            par = doc.add_paragraph()
            in_list = bool(list_stack)
            is_cap = (not in_list and inline.children and inline.children[0].type == "em_open"
                      and re.match(r"^(Figure|Table)\s", inline.content))
            if in_list:
                depth = len(list_stack)
                kind, cnt = list_stack[-1]
                marker = "•" if kind == "bullet" else f"{cnt}."
                par.paragraph_format.left_indent = Cm(0.6 * depth + 0.2)
                par.paragraph_format.first_line_indent = Cm(-0.5)
                par.paragraph_format.space_after = Pt(3)
                par.add_run(marker + "  ")
            if is_cap:
                par.alignment = WD_ALIGN_PARAGRAPH.CENTER
                par.paragraph_format.space_after = Pt(10)
                fmt_runs(par, inline.children, size=9, color=GREY)
            else:
                fmt_runs(par, inline.children)
            i += 3
            continue
        if t == "table_open":
            rows, cur, is_head = [], None, False
            i += 1
            while tokens[i].type != "table_close":
                tt = tokens[i].type
                if tt == "tr_open":
                    cur = []
                elif tt == "tr_close":
                    rows.append(cur)
                elif tt in ("th_open", "td_open"):
                    cur.append(tokens[i + 1].children or [])
                    i += 2
                i += 1
            render_table(doc, rows)
            i += 1
            continue
        if t in ("fence", "code_block"):
            for line in tk.content.rstrip("\n").split("\n"):
                par = doc.add_paragraph()
                par.paragraph_format.space_after = Pt(0)
                par.paragraph_format.left_indent = Cm(0.4)
                par.paragraph_format.line_spacing = 1.0
                r = par.add_run(line if line else " ")
                r.font.name = MONO_FONT
                r._element.rPr.rFonts.set(qn("w:eastAsia"), MONO_FONT)
                r.font.size = Pt(8)
                pPr = par._p.get_or_add_pPr()
                shd = OxmlElement("w:shd")
                shd.set(qn("w:val"), "clear")
                shd.set(qn("w:fill"), "F3F5F8")
                pPr.append(shd)
            doc.add_paragraph().paragraph_format.space_after = Pt(2)
            i += 1
            continue
        if t == "blockquote_open":
            # render quote paragraphs italic with left indent
            j = i + 1
            while tokens[j].type != "blockquote_close":
                if tokens[j].type == "paragraph_open":
                    par = doc.add_paragraph()
                    par.paragraph_format.left_indent = Cm(0.8)
                    fmt_runs(par, tokens[j + 1].children, base_italic=True, color=GREY)
                j += 1
            i = j + 1
            continue
        i += 1
    doc.core_properties.title = meta.get("title", "")
    doc.core_properties.author = "Shourya Sarkar"
    doc.core_properties.last_modified_by = "Shourya Sarkar"
    doc.core_properties.comments = ""
    doc.save(out_path)
    return n_img


if __name__ == "__main__":
    md_path, out_path = sys.argv[1], sys.argv[2]
    base = Path(md_path).parent
    if "--base-dir" in sys.argv:
        base = Path(sys.argv[sys.argv.index("--base-dir") + 1])
    n = build(md_path, out_path, base)
    print(f"wrote {out_path} ({n} figures)")
