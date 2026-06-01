"""PDF operations: rasterize a page to PNG, stamp a banner box with an internal
GoTo jump-link, count pages."""
from __future__ import annotations
import html
import os
import shutil
import subprocess
import tempfile

from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import (ArrayObject, DictionaryObject, FloatObject,
                           NameObject, NumberObject)

from . import render

PT = 72.0

# banner box geometry (inches)
BOX_W = 5.25
BOX_H = 0.62
LEFT = 0.7
TOP = 0.5
BOTTOM = 0.7

_BANNER_HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size: {w_in}in {h_in}in; margin: 0; }}
html, body {{ margin: 0; padding: 0; }}
.box {{
  box-sizing: border-box;
  position: absolute; left: {left}in; {vpos}: {voff}in;
  width: {bw}in; height: {bh}in;
  display: flex; align-items: center; justify-content: space-between; gap: 11pt;
  border: 1.7pt solid #111; background: #fff; box-shadow: 5pt 5pt 0 {accent};
  padding: 4pt 11pt;
  font-family: -apple-system, "SF Pro Text", "Helvetica Neue", Helvetica, sans-serif;
}}
.kicker {{ font-size: 6.8pt; font-weight: 600; letter-spacing: 0.12em;
  text-transform: uppercase; color: {accent}; }}
.detail {{ font-size: 9.4pt; font-weight: 600; color: #111; margin-top: 2pt; line-height: 1.1; }}
.pill {{ flex: 0 0 auto; font-size: 8.6pt; font-weight: 700; letter-spacing: 0.03em;
  color: #fff; background: {accent}; border: 1.4pt solid #111; border-radius: 2pt;
  padding: 3.5pt 8pt; white-space: nowrap; }}
.note {{ flex: 0 0 auto; font-size: 7.2pt; font-weight: 600; letter-spacing: 0.07em;
  text-transform: uppercase; color: #8a8a8a; white-space: nowrap; }}
</style></head><body>
<div class="box">
<div><div class="kicker">{kicker}</div><div class="detail">{detail}</div></div>
{right}
</div></body></html>"""


def page_count(pdf_path: str) -> int:
    return len(PdfReader(pdf_path).pages)


def rasterize(pdf_path: str, phys_page: int, out_png: str, max_px: int = 1600):
    """Render a 1-based physical page to PNG. Uses pdftoppm if present, else sips."""
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    writer.add_page(reader.pages[phys_page - 1])
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    writer.write(tmp)
    tmp.close()
    try:
        if shutil.which("pdftoppm"):
            base = out_png[:-4] if out_png.endswith(".png") else out_png
            subprocess.run(["pdftoppm", "-png", "-singlefile", "-scale-to", str(max_px),
                            tmp.name, base], check=True, capture_output=True)
        elif shutil.which("sips"):
            subprocess.run(["sips", "-s", "format", "png", "-Z", str(max_px),
                            tmp.name, "--out", out_png], check=True, capture_output=True)
        else:
            raise RuntimeError("No rasterizer found (need pdftoppm or sips).")
    finally:
        os.unlink(tmp.name)


def _render_banner(w_pt, h_pt, kicker, detail, pill, position, accent):
    w_in, h_in = w_pt / PT, h_pt / PT
    bw = min(BOX_W, w_in - 2 * LEFT)
    vpos, voff = ("top", TOP) if position == "top" else ("bottom", BOTTOM)
    right = (f'<div class="pill">{html.escape(pill)} &nbsp;&#x2193;</div>'
             if pill else '<div class="note">full work enclosed</div>')
    doc = _BANNER_HTML.format(
        w_in=f"{w_in:.4f}", h_in=f"{h_in:.4f}", left=f"{LEFT:.4f}",
        vpos=vpos, voff=f"{voff:.4f}", bw=f"{bw:.4f}", bh=f"{BOX_H:.4f}",
        accent=accent, kicker=html.escape(kicker), detail=html.escape(detail), right=right)
    td = tempfile.mkdtemp(prefix="folio_banner_")
    hp, pp = os.path.join(td, "b.html"), os.path.join(td, "b.pdf")
    with open(hp, "w") as f:
        f.write(doc)
    render.html_to_pdf(hp, pp)
    return PdfReader(pp).pages[0], bw


def _add_goto_link(writer, src_page_index, target_page_index, rect):
    target_ref = writer.pages[target_page_index].indirect_reference
    annot = DictionaryObject({
        NameObject("/Type"): NameObject("/Annot"),
        NameObject("/Subtype"): NameObject("/Link"),
        NameObject("/Rect"): ArrayObject([FloatObject(v) for v in rect]),
        NameObject("/Border"): ArrayObject([NumberObject(0), NumberObject(0), NumberObject(0)]),
        NameObject("/Dest"): ArrayObject([target_ref, NameObject("/Fit")]),
    })
    ref = writer._add_object(annot)
    page = writer.pages[src_page_index]
    if "/Annots" in page:
        page[NameObject("/Annots")].append(ref)
    else:
        page[NameObject("/Annots")] = ArrayObject([ref])


def stamp_banner(src_pdf: str, out_pdf: str, kicker: str, detail: str,
                 pill: str, jump_page, position: str, accent: str):
    """Copy src_pdf, stamp a banner box on page 1, add a GoTo link to jump_page
    (1-based physical page) if given. No page content is scaled."""
    writer = PdfWriter()
    writer.append(src_pdf)
    p1 = writer.pages[0]
    mb = p1.mediabox
    w, h = float(mb.width), float(mb.height)

    banner, bw = _render_banner(w, h, kicker, detail, pill, position, accent)
    p1.merge_page(banner)

    if jump_page:
        x0 = LEFT * PT
        x1 = x0 + bw * PT
        if position == "top":
            y1 = h - TOP * PT
            y0 = y1 - BOX_H * PT
        else:
            y0 = BOTTOM * PT
            y1 = y0 + BOX_H * PT
        _add_goto_link(writer, 0, jump_page - 1, (x0, y0, x1, y1))

    os.makedirs(os.path.dirname(out_pdf), exist_ok=True)
    with open(out_pdf, "wb") as f:
        writer.write(f)
