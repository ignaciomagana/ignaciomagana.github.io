# ignaciomagana.github.io

Personal academic website for **Ignacio Magaña Hernandez** — a light, minimal,
custom [Jekyll](https://jekyllrb.com/) site with a blog, designed for GitHub
Pages. No external theme; everything here is editable and self-contained.

---

## Quick start (edit content — no code)

Almost everything is driven by data files in [`_data/`](_data/):

| File | Controls |
|------|----------|
| `_data/publications.yml` | Every paper, **generated from the CV** (see below). `group:` is `first-author`, `student-led`, `coauthored`, or `collaboration`; `selected: true` features a paper on the home page (set in `tools/cv2data.py`). |
| `_data/talks.yml` | Seminars, contributed talks, and workshops & schools, **generated from the CV**. |
| `_data/research.yml` | The five research themes (title, blurb, tags, and arXiv refs shown on /research/). |
| `_data/research_intro.yml` | Title and lead paragraph of /research/. |
| `_data/social.yml` | Profile links (email, GitHub, ORCID, INSPIRE, X). Set `hidden: true` on any entry to hide it. |

Prose lives in the page files: `index.html` (about/bio), `research.html`,
`publications.html`, `talks.html`, `cv.html`, `blog.html`. Blog posts are
Markdown files in `_posts/` named `YYYY-MM-DD-title.md`.

Site-wide settings (name, tagline, URL, metrics) are in `_config.yml`.

---

## Run locally

Requires Ruby ≥ 2.7 (the repo's build node has 2.5, which is too old — build on
a newer machine or just let GitHub Pages build it for you).

```bash
bundle install
bundle exec jekyll serve --livereload
# → http://127.0.0.1:4000
```

On the cluster (Ruby 2.5, no Jekyll), `tools/minijekyll.rb` builds a static preview
with the same Liquid 4, kramdown and Ruby Sass 3.7.4 engines GitHub Pages uses:

```bash
ruby -I tools/shim -I ~/.gem/ruby/gems/sass-3.7.4/lib tools/minijekyll.rb . /tmp/site --preview
```

---

## Deploy to GitHub Pages

**As your user site** (recommended — serves at `https://ignaciomagana.github.io`):

1. Create/enter a repo named exactly `ignaciomagana.github.io`.
2. Copy the contents of this folder into it and push to `main`.
3. In **Settings → Pages**, set *Source* to **Deploy from a branch**, branch
   `main` / `/ (root)`. GitHub builds it automatically in ~1 minute.

`_config.yml` is already set for this (`url: https://ignaciomagana.github.io`,
`baseurl: ""`).

**As a project repo** (e.g. served at `…github.io/ignacio-website`): set
`baseurl: "/ignacio-website"` in `_config.yml`. All internal links already use
`relative_url`, so nothing else needs to change.

---

## Updating the CV

The PDF at [`assets/cv.pdf`](assets/cv.pdf) is the compiled LaTeX CV. To refresh
it after editing the source (kept in the sibling `ignaciocv-master/` repo):

```bash
pdflatex cv.tex && pdflatex cv.tex          # run twice for cross-refs
cp cv.pdf /path/to/ignaciomagana.github.io/assets/cv.pdf
```

Then regenerate the publication and talk lists from the same `cv.tex`, so the
site and the CV never disagree:

```bash
python3 tools/cv2data.py ../ignaciocv-master/cv.tex _data
```

The metric numbers shown on the site (Papers / Citations / h-index) are
hard-coded in `index.html` and `publications.html`; update them there when the
CV's Publication Summary changes.

---

## Common tweaks

- **Add a headshot to the hero.** Drop a square photo at
  `assets/img/headshot.jpg`, then in `index.html` replace the `<div class="hero__art">…</div>`
  SVG emblem with `<img class="hero__portrait" src="{{ '/assets/img/headshot.jpg' | relative_url }}" alt="Ignacio Magaña Hernandez">`
  (the `.hero__portrait` style already exists).
- **Remove X/Twitter.** Set `hidden: true` on the Twitter entry in
  `_data/social.yml` (and delete the `twitter:`/`x.com` lines in `_config.yml`).
- **Change the accent color / fonts.** Edit the CSS custom properties at the top
  of `_sass/_variables.scss`. The rosewood accent (#9E3B57) and Latin Modern
  match the CV and the research proposal.
- **Regenerate favicon / social image / web fonts.** `python3 tools/make_assets.py .`
  rewrites `assets/img/favicon.svg`, `favicon.png`, `og-image.png`, the chirp in
  `_includes/chirp.html`, and the Latin Modern WOFF2 files in `assets/fonts/`.

---

## Structure

```
_config.yml            site settings, plugins, SEO
_data/                 publications, talks, research, social  ← edit these
_layouts/              default, home, page, post
_includes/             head, header, footer, social, icon, pub, binary, chirp
_sass/                 _variables, _fonts, _base, _layout, _components
assets/css/main.scss   imports the Sass partials
assets/fonts/          Latin Modern (WOFF2, GUST Font License)
assets/img/            favicon + OG image
tools/                 cv2data.py, make_assets.py, minijekyll.rb (not published)
assets/cv.pdf          compiled CV
index.html research.html publications.html talks.html cv.html blog.html
_posts/                blog posts (Markdown)
```

Built with Jekyll · plugins: `jekyll-feed`, `jekyll-seo-tag`, `jekyll-sitemap`.
