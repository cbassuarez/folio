"""Generate the Work Sample Index markdown (designed mini-portfolio)."""
from __future__ import annotations
import html

from .config import Packet, Doc


def banner_block(kicker: str, title: str, tag: str) -> str:
    tag_html = html.escape(tag).replace("\n", "<br>")
    return (
        '<div class="banner">\n'
        '<div class="banner-left">\n'
        f'<div class="banner-kicker">{html.escape(kicker)}</div>\n'
        f'<div class="banner-title">{html.escape(title)}</div>\n'
        '</div>\n'
        f'<div class="banner-right">{tag_html}</div>\n'
        '</div>\n')


CARD = """
<div class="work">
<h2><span class="num">{n}</span>&nbsp; {title}{subtitle} <span class="yr">{year}</span></h2>
<div class="work-head">
{thumb}
<div class="work-meta">
<table>
{rows}
</table>
<div class="files">
{files}
</div>
</div>
</div>
<p class="work-statement">{statement}</p>
</div>
"""


def _rows(work) -> str:
    r = []
    if work.medium:
        r.append(f"<tr><td>Medium</td><td>{html.escape(work.medium)}</td></tr>")
    if work.duration:
        r.append(f"<tr><td>Duration</td><td>{html.escape(work.duration)}</td></tr>")
    if work.audio:
        dur = f" · {work.audio.duration}" if work.audio.duration else ""
        r.append(f"<tr><td>Audio</td><td>{html.escape(work.audio.label)}{dur}</td></tr>")
    primary = next((s for s in work.scores if s.is_primary and s.relevant_page), None)
    if primary and primary.page_label:
        r.append(f'<tr><td>Relevant page</td><td><span class="rel">{html.escape(primary.page_label)} → linked</span></td></tr>')
    return "\n".join(r)


def _files(packet: Packet, work) -> str:
    lines = []
    if work.audio:
        lines.append(f'<span class="lbl">audio</span> {packet.fname(work.audio.out, _ext(work.audio.source))}')
    for s in work.scores:
        lines.append(f'<span class="lbl">score</span> {packet.fname(s.out, "pdf")}')
    return "<br>\n".join(lines)


def _ext(path: str) -> str:
    return path.rsplit(".", 1)[-1].lower()


def render_index_md(packet: Packet, doc: Doc, thumbs: dict) -> str:
    out = ['---\ntitle: "Work Sample Index"\n---\n']
    out.append(banner_block(packet.identity.kicker, doc.title, packet.identity.tag))
    if doc.lede:
        out.append(f'\n<p class="lede">{doc.lede}</p>\n')
    for w in packet.works:
        sub = f" {w.subtitle}" if w.subtitle else ""
        thumb_name = thumbs.get(w.n)
        if thumb_name:
            cap = f'<figcaption class="cap">{html.escape(w.thumb_caption)}</figcaption>' if w.thumb_caption else ""
            thumb = (f'<figure class="work-thumb">\n'
                     f'<img src="media/{thumb_name}" alt="{html.escape(w.title)} excerpt" />\n'
                     f'{cap}\n</figure>')
        else:
            thumb = ""
        out.append(CARD.format(
            n=w.n, title=html.escape(w.title), subtitle=html.escape(sub),
            year=html.escape(w.year), thumb=thumb, rows=_rows(w),
            files=_files(packet, w), statement=w.statement))
    if packet.identity.footer:
        out.append(f'\n<div class="runfoot">{html.escape(packet.identity.footer)}</div>\n')
    return "\n".join(out)
