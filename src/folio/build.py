"""Orchestrate a full packet build from packet.yaml."""
from __future__ import annotations
import html
import os
import shutil
import subprocess

from . import config, index, pdfops, render, themes


def _ext(path: str) -> str:
    return path.rsplit(".", 1)[-1].lower()


def _probe_duration(path: str) -> str:
    if not shutil.which("ffprobe"):
        return ""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", path], check=True, capture_output=True, text=True)
        secs = float(out.stdout.strip())
        return f"{int(secs)//60}:{int(secs)%60:02d}"
    except Exception:
        return ""


def _banner_html(kicker: str, title: str, tag: str) -> str:
    return index.banner_block(kicker, title, tag)


def _inject(src_md: str, packet: config.Packet, title: str) -> str:
    """Insert the banner after YAML front matter and append the footer."""
    txt = open(src_md).read()
    banner = _banner_html(packet.identity.kicker, title, packet.identity.tag)
    footer = (f'\n\n<div class="runfoot">{html.escape(packet.identity.footer)}</div>\n'
              if packet.identity.footer else "")
    if txt.startswith("---"):
        _, fm, body = txt.split("---", 2)
        return f"---{fm}---\n\n{banner}\n{body.lstrip()}{footer}"
    return f"{banner}\n{txt}{footer}"


def build(packet_dir: str) -> str:
    pk = config.load(packet_dir)
    theme_css = themes.theme_css(pk.theme)

    out_root = os.path.join(pk.root, "out", pk.output)
    ws = os.path.join(out_root, "Work_Samples")
    work = os.path.join(pk.root, ".folio-work")
    media = os.path.join(work, "media")
    for d in (out_root, work):
        shutil.rmtree(d, ignore_errors=True)
    os.makedirs(ws, exist_ok=True)
    os.makedirs(media, exist_ok=True)

    # 1. thumbnails + audio durations
    thumbs: dict[int, str] = {}
    for w in pk.works:
        if w.audio and not w.audio.duration:
            w.audio.duration = _probe_duration(os.path.join(pk.root, w.audio.source))
        primary = next((s for s in w.scores if s.is_primary and s.relevant_page), None)
        if primary:
            name = f"thumb_{w.n:02d}.png"
            pdfops.rasterize(os.path.join(pk.root, primary.source),
                             primary.relevant_page, os.path.join(media, name))
            thumbs[w.n] = name

    # 2. text documents (+ generated index)
    print("Documents:")
    for doc in pk.docs:
        out_pdf = os.path.join(out_root, pk.fname(doc.out, "pdf"))
        if doc.is_index:
            md = index.render_index_md(pk, doc, thumbs)
            md_path = os.path.join(work, "_index.md")
            open(md_path, "w").write(md)
            render.md_to_pdf(md_path, out_pdf, [theme_css], [work, pk.root], work)
        else:
            src = os.path.join(pk.root, doc.source)
            md_path = os.path.join(work, f"_{doc.out}.md")
            open(md_path, "w").write(_inject(src, pk, doc.title))
            render.md_to_pdf(md_path, out_pdf, [theme_css],
                             [pk.root, os.path.dirname(src), work], work)
        print(f"  {pk.fname(doc.out, 'pdf')}")

    # 3. score banners + audio
    print("Work samples:")
    for w in pk.works:
        for s in w.scores:
            out_pdf = os.path.join(ws, pk.fname(s.out, "pdf"))
            pdfops.stamp_banner(
                os.path.join(pk.root, s.source), out_pdf,
                kicker=s.kicker, detail=s.detail, pill=s.page_label,
                jump_page=s.relevant_page, position=s.position, accent=pk.accent)
            n = pdfops.page_count(out_pdf)
            print(f"  {pk.fname(s.out, 'pdf')}  ({n}pp, jump→{s.relevant_page})")
        if w.audio:
            dst = os.path.join(ws, pk.fname(w.audio.out, _ext(w.audio.source)))
            shutil.copyfile(os.path.join(pk.root, w.audio.source), dst)
            print(f"  {os.path.basename(dst)}")

    return out_root
