# folio

Build a cohesive, submission-ready **PDF packet** from a single manifest.

One `packet.yaml` describes your identity, your documents, and your work
samples. `folio build` produces an upload-ready folder:

- **Themed text documents** (statement, CV, etc.) from Markdown, each carrying a
  neo-brutalist banner and a running footer.
- A **designed Work Sample Index** with a score-page thumbnail, metadata, and
  filenames per work.
- **Score PDFs** stamped with a banner box on the cover, including an internal
  **jump-link** straight to the relevant page.
- A packaged **`Work_Samples/`** folder with clean, consistent filenames and
  your audio copied in.

Originals are never modified; everything is written under `out/`.

## Requirements

- **pandoc** (`brew install pandoc`)
- **Google Chrome** (or Chromium) — used headless to render PDFs
- **Python 3.11+** — the launcher bootstraps a local `.venv` (pyyaml, pypdf) on
  first run; nothing is installed globally
- A rasterizer for thumbnails: **`sips`** (built into macOS) or **`pdftoppm`**
- *(optional)* **ffmpeg/ffprobe** — auto-fills audio durations if omitted

## Install

Run-in-place. Clone/copy the repo and call `./folio`:

```bash
git clone <this-repo> ~/folio
~/folio/folio --help
```

Optionally add it to your PATH:

```bash
ln -s ~/folio/folio /usr/local/bin/folio
```

## Quickstart

```bash
folio init my-packet      # scaffold packet.yaml + content/ + src/
cd my-packet
# 1. edit packet.yaml (identity, docs, works)
# 2. drop score PDFs + audio into src/, write prose in content/
folio build               # -> out/<output>/  (ready to upload)
```

## `packet.yaml` reference

```yaml
output: "Lastname_Submission"   # name of the assembled folder under out/
suffix: "Lastname"              # appended to every file: NAME_Lastname.ext ("" to omit)
theme: classic                  # bundled theme (folio/src/folio/themes/)
accent: "#1d4eb8"               # banner accent + link colour

identity:                       # on every PDF
  kicker: "Submission · 2026"   # small uppercase banner line
  tag: "First\nLast"            # right-hand banner block (\n = line break)
  footer: "First Last · site.com · me@site.com"

docs:                           # built in order
  - source: content/statement.md
    out: "01_Statement_of_Interest"
    title: "01 · Statement of Interest"
  - index: true                 # auto-generated work-sample index
    out: "02_Work_Sample_Index"
    title: "02 · Work Sample Index"
    lede: "Optional intro sentence."

works:
  - title: "Work Title"
    subtitle: "for ensemble"    # optional
    year: "2024"
    medium: "Chamber ensemble"
    duration: "approx. 8 min"
    thumb_caption: "Opening (p.1)"
    statement: |
      Why this work is included. Inline <em>HTML</em> is fine.
    audio:
      source: src/work.mp3
      label: "Excerpt"
      # duration: "1:00"        # optional; auto-probed via ffprobe
    score:
      source: src/work.pdf
      relevant_page: 1          # physical page (1-based): thumbnail + jump target
      # page_label: "p.1"       # banner pill text; default "p.<relevant_page>"
      # detail: "..."           # banner main line; sensible default otherwise
      position: top             # top | bottom (banner box position on the cover)
    extra_scores:               # optional extra score files (e.g. rehearsal score)
      - source: src/work-rehearsal.pdf
        out_tag: "rehearsal-score"
        relevant_page: 7
        page_label: "mvmt 2"
```

### Notes

- **Filenames** are derived from each work's title and order (`01_Work_Title_…`),
  with `suffix` appended. Override any name with an explicit `out:`.
- **`relevant_page` is the physical page** in the source PDF (count from 1,
  including any title/blank pages). The `page_label` is just the text shown on
  the banner pill, so you can display the *printed* page number even when it
  differs from the physical one.
- **`position`** picks where the banner box sits on the cover (`top` for art
  covers with centred titles, `bottom` when the top is busy).
- A work without a `score.relevant_page` gets no thumbnail and no jump-link; a
  score with no jump shows a neutral "full work enclosed" banner.

## Themes

Bundled themes live in `src/folio/themes/<name>/theme.css`. Copy `classic` to a
new folder, edit the CSS, and set `theme:` to its name. The `accent` colour in
`packet.yaml` overrides the banner/jump-link colour without touching CSS.

## How it works

```
packet.yaml + content/*.md + src/*.pdf,*.mp3
        │
        ├─ pandoc → standalone HTML (+theme CSS) → headless Chrome → text PDFs
        ├─ pypdf + sips/pdftoppm → score-page thumbnails → generated index PDF
        ├─ Chrome-rendered banner → pypdf overlay + GoTo link → score PDFs
        └─ copy/rename audio
        ▼
out/<output>/   (01_…pdf, 02_…pdf, Work_Samples/…)
```

## Layout

```
folio              launcher (bootstraps .venv, runs the package)
src/folio/
  cli.py           init / build
  config.py        packet.yaml → typed config
  render.py        markdown/HTML → PDF (pandoc + Chrome)
  pdfops.py        rasterize, banner overlay, GoTo jump-links
  index.py         Work Sample Index generator
  build.py         orchestration
  themes/classic/  theme.css
  templates/       what `folio init` copies
```
