"""Generate the website's _data/publications.yml and _data/talks.yml from cv.tex.

Usage: python3 -I cv2data.py CV_TEX OUT_DIR
The CV is the single source of truth; rerun this after every CV update.
"""
import re
import sys

ACCENTS = {"'": "\u0301", "`": "\u0300", '"': "\u0308", "~": "\u0303", "^": "\u0302"}
import unicodedata

SELECTED = {"2610.37617", "2511.16648", "2509.03607", "2508.19208", "2407.02460",
            "2404.02522", "2304.08046", "2104.09339", "1908.06050", "2006.12611"}


def read_group(s, i):
    """Return (content, end) for the brace group starting at s[i] == '{'."""
    assert s[i] == "{", s[i:i + 30]
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
    raise ValueError("unbalanced braces")


def skip_ws(s, i):
    while i < len(s) and s[i] in " \t\n%":
        if s[i] == "%":
            while i < len(s) and s[i] != "\n":
                i += 1
        i += 1
    return i


def args(s, i, n, optional=False):
    opt = None
    i = skip_ws(s, i)
    if optional and s[i] == "[":
        j = s.index("]", i)
        opt, i = s[i + 1:j], j + 1
    out = []
    for _ in range(n):
        i = skip_ws(s, i)
        g, i = read_group(s, i)
        out.append(g)
    return opt, out, i


def tex2html(t):
    t = t.strip()
    t = re.sub(r"\$M_\{?\\odot\}?\$", "M<sub>⊙</sub>", t)
    t = re.sub(r"\$H_0\$", "H<sub>0</sub>", t)
    t = re.sub(r"\$\\mathbf\{H_0\}\$", "H<sub>0</sub>", t)
    t = re.sub(r"\\texttt\{([^{}]*)\}", r"<code>\1</code>", t)
    t = re.sub(r"\\(?:textbf|emph|textit|textnormal)\{([^{}]*)\}", r"\1", t)
    t = re.sub(r"\{\\textbf\{([^{}]*)\}\}", r"\1", t)

    def acc(m):
        return unicodedata.normalize("NFC", m.group(2) + ACCENTS[m.group(1)])
    t = re.sub(r"\\(['`\"~^])\{?([A-Za-z])\}?", acc, t)
    t = t.replace("---", "—").replace("--", "–").replace("\\%", "%").replace("~", "\u00a0")
    t = t.replace("\\&", "&amp;").replace("{", "").replace("}", "")
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def year_of(venue, arxiv):
    m = re.search(r"\((\d{4})\)", venue or "")
    if m:
        return int(m.group(1))
    return 2000 + int(arxiv[:2])


def parse_pubs(tex):
    groups = {"First/Second Author Publications": "first-author",
              "Student-Led Publications": "student-led",
              "Other Publications": "coauthored",
              "LIGO--Virgo Collaboration Papers with Major Personal Contributions": "collaboration",
              "Papers in Preparation": "in-prep"}
    heads = [(m.start(), groups[m.group(1)]) for m in
             re.finditer(r"\\resheading(?:Author)?\{([^{}]*)\}", tex) if m.group(1) in groups]
    pubs = []
    for m in re.finditer(r"\\publication(Arxiv|Journal|LVK|Prep)(?![A-Za-z])", tex):
        if tex[m.start() - 1:m.start()] == "{" or tex[m.end():m.end() + 1] == "}":
            continue  # the \newcommand definitions
        kind, i = m.group(1), m.end()
        group = [g for pos, g in heads if pos < m.start()][-1]
        if kind == "Arxiv":
            _, (title, authors, url, label, cites), i = args(tex, i, 5, optional=True)
            venue, note = None, None
        elif kind == "Journal":
            _, (title, authors, venue, url, label, cites), i = args(tex, i, 6)
            note = None
        elif kind == "Prep":
            _, (title, authors, status), i = args(tex, i, 3)
            # In-prep papers: no year, arXiv number or citations; drop the CV's parenthetical
            pubs.append({"group": group, "title": tex2html(title), "authors": tex2html(authors),
                         "status": tex2html(status).split(" (")[0]})
            continue
        else:
            _, (title, authors, venue, url, label, cites, note), i = args(tex, i, 7)
        rest = tex[i:i + 80]
        sm = re.match(r"\s*\\emph\{([^{}]*)\}", rest)
        status = sm.group(1) if sm else None
        arxiv = label.replace("arXiv:", "").strip()
        p = {"group": group}
        if arxiv in SELECTED:
            p["selected"] = True
        p["title"] = tex2html(title)
        p["authors"] = tex2html(authors)
        p["year"] = year_of(venue, arxiv)
        if venue:
            p["venue"] = tex2html(venue)
        if status:
            p["status"] = tex2html(status)
        p["arxiv"] = arxiv
        p["cites"] = int(cites)
        if note:
            p["note"] = tex2html(note)
        pubs.append(p)
    return pubs


def parse_talks(tex):
    sections = {"Invited Seminars": "seminars", "Contributed Talks": "conferences",
                "Other Workshops": "schools"}
    out = {v: [] for v in sections.values()}
    for name, key in sections.items():
        i = tex.index("\\resheading{%s}" % name)
        j = tex.index("\\end{enumerate}", i)
        block = re.sub(r"(?m)^\s*%.*$", "", tex[i:j])
        for m in re.finditer(r"\\presentation(?![A-Za-z])", block):
            _, (venue, date, title), _ = args(block, m.end(), 3)
            item = {"venue": tex2html(venue), "date": tex2html(date)}
            item["host" if key == "schools" else "title"] = tex2html(title)
            out[key].append(item)
    return out


def q(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main():
    tex = open(sys.argv[1], encoding="utf-8").read()
    out = sys.argv[2]
    pubs = parse_pubs(tex)
    titles = {"first-author": "First & second author", "student-led": "Led by students I mentor",
              "coauthored": "Co-authored", "collaboration": "LIGO–Virgo papers with major personal contributions",
              "in-prep": "In preparation"}
    lines = ["# ---------------------------------------------------------------------------",
             "#  Publications, generated from cv.tex by cv2data.py (do not edit by hand).",
             "#  `me` defaults to \"I. Magaña Hernandez\" (bolded in author lists).",
             "#  group: first-author | student-led | coauthored | collaboration | in-prep",
             "#  selected: true  -> also featured on the home page",
             "#  Full record: https://inspirehep.net/authors/1902658",
             "# ---------------------------------------------------------------------------"]
    last = None
    for p in pubs:
        if p["group"] != last:
            lines += ["", "# ===== %s =====" % titles[p["group"]]]
            last = p["group"]
        first = True
        for k, v in p.items():
            lines.append(("- " if first else "  ") + "%s: %s" % (k, q(v)))
            first = False
        lines.append("")
    open(out + "/publications.yml", "w", encoding="utf-8").write("\n".join(lines).rstrip() + "\n")

    talks = parse_talks(tex)
    tl = ["# Talks, generated from cv.tex by cv2data.py (do not edit by hand); reverse-chronological."]
    for key in ("seminars", "conferences", "schools"):
        tl.append("%s:" % key)
        for t in talks[key]:
            first = True
            for k, v in t.items():
                tl.append(("  - " if first else "    ") + "%s: %s" % (k, q(v)))
                first = False
    open(out + "/talks.yml", "w", encoding="utf-8").write("\n".join(tl) + "\n")
    counts = {g: sum(p["group"] == g for p in pubs) for g in titles}
    print("pubs", len(pubs), counts, "| talks", {k: len(v) for k, v in talks.items()})


if __name__ == "__main__":
    main()
