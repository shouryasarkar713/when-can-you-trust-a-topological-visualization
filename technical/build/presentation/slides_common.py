"""Helpers for building slide descriptions (used by slides_main.py and slides_supp.py)."""

from pptx.dml.color import RGBColor  # noqa: E402

CB, CO, CG, CP = RGBColor(0x00, 0x72, 0xB2), RGBColor(0xD5, 0x5E, 0x00), RGBColor(0x00, 0x9E, 0x73), RGBColor(0x8A, 0x4F, 0x9E)
GREYC = RGBColor(0x5B, 0x64, 0x72)


def T(x, y, w, h, paras, size=18, bullet=False, **kw):
    return dict(type="text", x=x, y=y, w=w, h=h, paras=paras, size=size, bullet=bullet, **kw)


def I(name, x, y, w, h):
    return dict(type="img", name=name, x=x, y=y, w=w, h=h)


def C(x, y, w, text, size=11, h=0.45, **kw):
    return dict(type="cap", x=x, y=y, w=w, h=h, text=text, size=size, **kw)


def TB(x, y, w, rows, widths, size=14, row_h=0.4, hl=()):
    return dict(type="table", x=x, y=y, w=w, rows=rows, widths=widths, size=size, row_h=row_h, hl=hl)


def BX(x, y, w, h, head, paras, color=CB, size=15, bullet=False, hsize=16):
    return dict(type="box", x=x, y=y, w=w, h=h, head=head, paras=paras, color=color, size=size, bullet=bullet, hsize=hsize)


def F(title, els, notes, supp=False):
    d = {"title": title, "layout": "free", "els": els, "notes": notes}
    if supp:
        d["supp"] = True
    return d
