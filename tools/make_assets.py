"""Build the rosewood site assets: chirp SVG include, binary favicon (SVG/PNG),
social card, and renamed WOFF2 copies of Latin Modern Roman.

Usage: python3 -I make_assets.py SITE_DIR
"""
import math
import os
import sys

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROSE = (158, 59, 87)
ROSE_HEX = "#9E3B57"
LM = "/usr/share/texlive/texmf-dist/fonts/opentype/public/lm/"
FONTS = {  # source file -> renamed web file (GUST license asks for new names)
    "lmroman10-regular.otf": "lmweb-regular.woff2",
    "lmroman10-italic.otf": "lmweb-italic.woff2",
    "lmroman10-bold.otf": "lmweb-bold.woff2",
    "lmroman10-bolditalic.otf": "lmweb-bolditalic.woff2",
    "lmromancaps10-regular.otf": "lmweb-caps.woff2",
}


def chirp_points(n_insp=900, n_ring=160):
    """Same waveform as the CV header rule: x in [0, 1], y in units of the peak."""
    cycles, xm, fr = 17, 0.899, 95
    amp = lambda x: 0.95 * (0.904 - x) ** -0.25
    phase = lambda x: 2 * math.pi * cycles * (1 - ((0.9 - x) / 0.9) ** 0.625)
    peak = amp(xm)
    pts = [(xm * k / n_insp, amp(xm * k / n_insp) * math.sin(phase(xm * k / n_insp)) / peak)
           for k in range(n_insp + 1)]
    phim = phase(xm)
    for k in range(1, n_ring + 1):
        x = xm + (0.99 - xm) * k / n_ring
        pts.append((x, math.exp(-(x - xm) / 0.012) * math.sin(phim + 2 * math.pi * fr * (x - xm))))
    pts.append((1.0, 0.0))
    return pts


def chirp_svg():
    w, h = 1000, 40
    d = "M" + " L".join("%.1f %.2f" % (x * w, h / 2 - 0.45 * h * y) for x, y in chirp_points())
    return ('<svg class="chirp" viewBox="0 0 %d %d" preserveAspectRatio="none" aria-hidden="true" focusable="false">'
            '<path d="%s" fill="none" stroke="currentColor" stroke-width="1.2" '
            'vector-effect="non-scaling-stroke" stroke-linejoin="round"/></svg>\n' % (w, h, d))


BINARY_SVG = ('<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">'
              '<ellipse cx="32" cy="32" rx="26" ry="11" fill="none" stroke="%s" stroke-opacity="0.4" stroke-width="2.5"/>'
              '<circle cx="18" cy="32" r="10" fill="%s"/>'
              '<circle cx="50" cy="32" r="6.5" fill="%s" fill-opacity="0.65"/></svg>\n') % ((ROSE_HEX,) * 3)


def favicon_png(path, size=180):
    s = 4  # supersample
    im = Image.new("RGBA", (size * s, size * s), (255, 255, 255, 0))
    d = ImageDraw.Draw(im)
    k = size * s / 64
    soft = ROSE + (102,)
    d.ellipse([(32 - 26) * k, (32 - 11) * k, (32 + 26) * k, (32 + 11) * k], outline=soft, width=int(2.5 * k))
    d.ellipse([(18 - 10) * k, (32 - 10) * k, (18 + 10) * k, (32 + 10) * k], fill=ROSE + (255,))
    d.ellipse([(50 - 6.5) * k, (32 - 6.5) * k, (50 + 6.5) * k, (32 + 6.5) * k], fill=ROSE + (166,))
    im.resize((size, size), Image.LANCZOS).save(path)


def og_image(path):
    W, H, s = 1200, 630, 2
    im = Image.new("RGB", (W * s, H * s), "white")
    d = ImageDraw.Draw(im)
    x0 = 90 * s
    size = 84
    while True:  # largest name size that fits the card
        bold = ImageFont.truetype(LM + "lmroman10-bold.otf", size * s)
        if d.textlength("Ignacio Magaña Hernandez", font=bold) <= W * s - 2 * x0:
            break
        size -= 2
    ital = ImageFont.truetype(LM + "lmroman10-italic.otf", 40 * s)
    caps = ImageFont.truetype(LM + "lmromancaps10-regular.otf", 34 * s)
    d.text((x0, 150 * s), "Research Physicist · Carnegie Mellon University", font=caps, fill=ROSE)
    d.text((x0, 210 * s), "Ignacio Magaña Hernandez", font=bold, fill=ROSE)
    d.text((x0, 320 * s), "Gravitational-wave astrophysics and cosmology", font=ital, fill=(97, 97, 97))
    pts = chirp_points()
    xw, yc, amp = (W - 180) * s, 440 * s, 26 * s
    d.line([(x0 + x * xw, yc - amp * y) for x, y in pts], fill=ROSE, width=3 * s, joint="curve")
    # binary glyph, top right
    cx, cy, k = (W - 150) * s, 110 * s, 1.6 * s
    d.ellipse([cx - 26 * k, cy - 11 * k, cx + 26 * k, cy + 11 * k], outline=(216, 177, 188), width=int(2.5 * k))
    d.ellipse([cx - 14 * k - 10 * k, cy - 10 * k, cx - 14 * k + 10 * k, cy + 10 * k], fill=ROSE)
    d.ellipse([cx + 18 * k - 6.5 * k, cy - 6.5 * k, cx + 18 * k + 6.5 * k, cy + 6.5 * k], fill=(197, 137, 154))
    im.resize((W, H), Image.LANCZOS).save(path, optimize=True)


def main():
    site = sys.argv[1]
    os.makedirs(site + "/assets/fonts", exist_ok=True)
    for src, dst in FONTS.items():
        f = TTFont(LM + src)
        f.flavor = "woff2"
        f.save(site + "/assets/fonts/" + dst)
    with open("/usr/share/texlive/texmf-dist/doc/fonts/lm/GUST-FONT-LICENSE.TXT") as fi:
        lic = fi.read()
    with open(site + "/assets/fonts/LICENSE-latin-modern.txt", "w") as fo:
        fo.write("The lmweb-*.woff2 files are WOFF2 conversions of Latin Modern Roman\n"
                 "(lmroman10-*.otf, lmromancaps10-regular.otf) by B. Jackowski and J. M. Nowacki,\n"
                 "GUST e-foundry, renamed as the license requests. Glyphs are unmodified.\n\n" + lic)
    with open(site + "/_includes/chirp.html", "w") as fo:
        fo.write(chirp_svg())
    with open(site + "/assets/img/favicon.svg", "w") as fo:
        fo.write(BINARY_SVG)
    favicon_png(site + "/assets/img/favicon.png")
    og_image(site + "/assets/img/og-image.png")
    print("assets written")


if __name__ == "__main__":
    main()
