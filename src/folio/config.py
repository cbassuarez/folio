"""Load and validate packet.yaml into typed config objects."""
from __future__ import annotations
import os
import re
from dataclasses import dataclass, field
from typing import Optional

import yaml


def slug(text: str) -> str:
    """A filename-safe slug that preserves words (Title Case -> Title_Case)."""
    text = re.sub(r"[^\w\s-]", "", text)          # drop punctuation
    text = re.sub(r"\s+", "_", text.strip())
    return text


class ConfigError(Exception):
    pass


@dataclass
class Identity:
    kicker: str = ""
    tag: str = ""
    footer: str = ""


@dataclass
class Doc:
    out: str                       # base output filename (no extension/suffix)
    title: str                     # banner title line (or cover title)
    source: Optional[str] = None   # content markdown path (relative to packet dir)
    is_index: bool = False
    lede: str = ""
    cover: bool = False            # render a full title page instead of the banner
    toc: bool = False              # render a table of contents (h2 sections)
    subtitle: str = ""             # cover-page subtitle
    compact: bool = False          # denser type/spacing (for résumés, dense docs)


@dataclass
class ScoreFile:
    source: str
    out: str
    relevant_page: Optional[int]   # physical page (1-based); None -> no jump/thumb
    page_label: str                # banner pill text
    detail: str                    # banner main line
    kicker: str = ""               # banner small uppercase line
    position: str = "top"          # top | bottom
    is_primary: bool = True        # primary score (gets the index thumbnail)


@dataclass
class AudioFile:
    source: str
    out: str
    label: str = "Excerpt"
    duration: str = ""             # display string; auto-probed if empty


@dataclass
class Work:
    n: int
    title: str
    subtitle: str
    year: str
    medium: str
    duration: str
    statement: str
    thumb_caption: str
    audio: Optional[AudioFile]
    scores: list[ScoreFile]        # primary first, then extras


@dataclass
class Packet:
    root: str                      # packet directory (absolute)
    output: str                    # output folder name
    suffix: str                    # appended to every filename (e.g. "Lastname")
    theme: str
    accent: str
    identity: Identity
    docs: list[Doc]
    works: list[Work]

    def fname(self, base: str, ext: str) -> str:
        s = f"_{self.suffix}" if self.suffix else ""
        return f"{base}{s}.{ext}"


def _req(d: dict, key: str, ctx: str):
    if key not in d:
        raise ConfigError(f"missing required key '{key}' in {ctx}")
    return d[key]


def load(packet_dir: str) -> Packet:
    path = os.path.join(packet_dir, "packet.yaml")
    if not os.path.exists(path):
        raise ConfigError(f"no packet.yaml found in {packet_dir}")
    with open(path) as f:
        raw = yaml.safe_load(f) or {}

    root = os.path.abspath(packet_dir)
    output = _req(raw, "output", "packet.yaml")
    suffix = raw.get("suffix", "")
    theme = raw.get("theme", "classic")
    accent = raw.get("accent", "#1d4eb8")

    idd = raw.get("identity", {}) or {}
    identity = Identity(kicker=idd.get("kicker", ""),
                        tag=idd.get("tag", ""),
                        footer=idd.get("footer", ""))

    docs: list[Doc] = []
    for d in raw.get("docs", []) or []:
        if d.get("index"):
            docs.append(Doc(out=_req(d, "out", "docs[index]"),
                            title=d.get("title", "Work Sample Index"),
                            is_index=True, lede=d.get("lede", "")))
        else:
            docs.append(Doc(out=_req(d, "out", "docs[]"),
                            title=d.get("title", d["out"]),
                            source=_req(d, "source", "docs[]"),
                            cover=d.get("cover", False),
                            toc=d.get("toc", False),
                            subtitle=d.get("subtitle", ""),
                            compact=d.get("compact", False)))

    works: list[Work] = []
    for i, w in enumerate(raw.get("works", []) or [], start=1):
        title = _req(w, "title", f"works[{i}]")
        base = w.get("slug") or slug(title)
        nn = f"{i:02d}"

        audio = None
        if w.get("audio"):
            a = w["audio"]
            audio = AudioFile(
                source=_req(a, "source", f"works[{i}].audio"),
                out=a.get("out", f"{nn}_{base}_audio-excerpt"),
                label=a.get("label", "Excerpt"),
                duration=a.get("duration", ""))

        yr = f" ({w.get('year')})" if w.get("year") else ""
        kbase = f"Work Sample {i} · {title}{yr}"

        scores: list[ScoreFile] = []
        if w.get("score"):
            s = w["score"]
            rp = s.get("relevant_page")
            scores.append(ScoreFile(
                source=_req(s, "source", f"works[{i}].score"),
                out=s.get("out", f"{nn}_{base}_score"),
                relevant_page=rp,
                page_label=s.get("page_label", f"p.{rp}" if rp else ""),
                detail=s.get("detail", _default_detail(audio, rp)),
                kicker=s.get("kicker", kbase),
                position=s.get("position", "top"),
                is_primary=True))
        for j, s in enumerate(w.get("extra_scores", []) or []):
            tag = s.get("out_tag", "score")
            rp = s.get("relevant_page")
            letter = chr(ord("a") + j)
            scores.append(ScoreFile(
                source=_req(s, "source", f"works[{i}].extra_scores[{j}]"),
                out=s.get("out", f"{nn}{letter}_{base}_{tag}"),
                relevant_page=rp,
                page_label=s.get("page_label", f"p.{rp}" if rp else ""),
                detail=s.get("detail", _default_detail(audio, rp)),
                kicker=s.get("kicker", f"Work Sample {i} · {title} · {tag.replace('-', ' ')}"),
                position=s.get("position", "top"),
                is_primary=False))

        works.append(Work(
            n=i, title=title, subtitle=w.get("subtitle", ""),
            year=str(w.get("year", "")), medium=w.get("medium", ""),
            duration=w.get("duration", ""), statement=w.get("statement", "").strip(),
            thumb_caption=w.get("thumb_caption", ""),
            audio=audio, scores=scores))

    return Packet(root=root, output=output, suffix=suffix, theme=theme,
                  accent=accent, identity=identity, docs=docs, works=works)


def _default_detail(audio: Optional[AudioFile], rp) -> str:
    bits = []
    if audio and audio.duration:
        bits.append(f"Audio excerpt ({audio.duration})")
    elif audio:
        bits.append("Audio excerpt")
    if rp:
        bits.append(f"see p.{rp}")
    return " - ".join(bits) if bits else "Work sample"
