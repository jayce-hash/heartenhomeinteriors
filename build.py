#!/usr/bin/env python3
"""
Hearten Home Interiors - portfolio build step.

Runs automatically on every Netlify deploy. Reads each project entry that Bonnie
creates in the CMS (projects/*.md), compresses its photos, and generates:
  - one pre-rendered detail page per project  (project-<slug>.html)
  - the portfolio gallery grid                (injected into projects.html)

Design goal: a malformed entry is skipped with a warning, never crashes the
build, so the live site is never taken down by a bad entry.
"""
import os, re, glob, html
from PIL import Image, ImageOps
import yaml

ROOT     = os.path.dirname(os.path.abspath(__file__))
PROJ_DIR = os.path.join(ROOT, "projects")
OPT_DIR  = os.path.join(ROOT, "images", "projects", "opt")
TEMPLATE = open(os.path.join(ROOT, "_project_template.html"), encoding="utf-8").read()
REQUIRED = ["title", "service", "location", "cover", "summary"]
BASE = "https://heartenhome.com"

os.makedirs(OPT_DIR, exist_ok=True)


def esc(s):
    return html.escape(str(s), quote=True)


def title_forms(t):
    """Return (plain, display). Plain collapses whitespace for meta/alt/<title>.
    Display keeps line breaks as <br> so a title can wrap where the user intends."""
    plain = " ".join(str(t).split())
    disp = esc(t).replace("\r\n", "<br>").replace("\n", "<br>")
    return plain, disp


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")


def parse(path):
    raw = open(path, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", raw, re.S)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except Exception as e:
        print(f"  ! could not read {os.path.basename(path)}: {e}")
        return {}


def optimize(src_rel, max_w):
    """Resize + convert to WebP. Returns web path, or original on failure."""
    src = os.path.join(ROOT, src_rel.lstrip("/"))
    name = slugify(os.path.splitext(os.path.relpath(src, ROOT))[0])
    out_rel = f"/images/projects/opt/{name}-{max_w}.webp"
    out = os.path.join(ROOT, out_rel.lstrip("/"))
    try:
        im = Image.open(src)
        im = ImageOps.exif_transpose(im).convert("RGB")
        if im.width > max_w:
            im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
        im.save(out, "WEBP", quality=90, method=6)
        return out_rel
    except Exception as e:
        print(f"  ! image skipped ({src_rel}): {e}")
        return src_rel


def img_size(web_rel):
    """(width, height) of a built image, or (None, None) if it cannot be read."""
    try:
        with Image.open(os.path.join(ROOT, web_rel.lstrip("/"))) as im:
            return im.size
    except Exception:
        return (None, None)


def dim_attrs(web_rel):
    w, h = img_size(web_rel)
    return f' width="{w}" height="{h}"' if w and h else ""


def gallery_section(images, title_plain, location):
    """Each photo gets its own alt so the set is not 15 identical strings."""
    figs = []
    for i, src in enumerate(images):
        alt = (f"{title_plain} interior design in {location}" if i == 0
               else f"{title_plain}, {location} interior design detail {i + 1}")
        figs.append(f'<figure><img src="{src}" alt="{esc(alt)}"'
                    f'{dim_attrs(src)} loading="lazy" decoding="async"></figure>')
    return ('<section class="project-gallery-section reveal">\n'
            '        <div class="gallery-masonry">\n            '
            + "\n            ".join(figs) + "\n        </div>\n    </section>")


def project_schema(d, title_plain, canonical, hero_opt, imgs):
    """BreadcrumbList + ImageGallery so each project can win image and rich results."""
    import json as _json
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Projects",
             "item": BASE + "/projects.html"},
            {"@type": "ListItem", "position": 3, "name": title_plain,
             "item": canonical},
        ],
    }
    def _img(src, i):
        w, h = img_size(src)
        o = {"@type": "ImageObject", "contentUrl": BASE + src,
             "representativeOfPage": i == 0,
             "caption": f"{title_plain}, {d['location']} interior design"}
        if w and h:
            o["width"], o["height"] = w, h
        return o
    gallery = {
        "@context": "https://schema.org",
        "@type": "ImageGallery",
        "@id": canonical,
        "url": canonical,
        "name": title_plain,
        "headline": title_plain,
        "description": " ".join(str(d["summary"]).split()),
        "isPartOf": {"@id": BASE + "/#website"},
        "primaryImageOfPage": {"@type": "ImageObject", "contentUrl": BASE + hero_opt},
        "image": [_img(s, i) for i, s in enumerate(imgs)],
        "about": {
            "@type": "Service",
            "name": str(d["service"]),
            "provider": {"@id": BASE + "/#studio"},
            "areaServed": {"@type": "City", "name": str(d["location"])},
        },
        "creator": {"@id": BASE + "/#studio"},
        "contentLocation": {"@type": "Place", "name": str(d["location"])},
    }
    if d.get("year"):
        gallery["dateCreated"] = str(d["year"])
    return "\n    ".join(
        '<script type="application/ld+json">\n'
        + _json.dumps(o, indent=2) + "\n</script>" for o in (crumbs, gallery))


def sort_key(d):
    order = d.get("order")
    order = order if isinstance(order, (int, float)) else 9999
    year = int(re.sub(r"\D", "", str(d.get("year", "0"))) or 0)
    return (order, -year)



def _rich(s):
    """Editable text -> safe HTML: escape, newline to <br>, *word* to <em>word</em>."""
    s = html.escape(str(s), quote=False)
    s = s.replace("\r\n", "<br>").replace("\n", "<br>")
    s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
    return s


def render_pages():
    """Render index/about/services/contact from their editable content + templates."""
    import json as _json
    for page in ["index", "about", "services", "contact"]:
        cpath = os.path.join(ROOT, "content", f"{page}.json")
        tpath = os.path.join(ROOT, "_templates", f"{page}.html")
        if not (os.path.exists(cpath) and os.path.exists(tpath)):
            continue
        data = _json.load(open(cpath, encoding="utf-8"))
        out = open(tpath, encoding="utf-8").read()
        for k, v in data.items():
            if isinstance(v, list):
                continue
            out = out.replace("{{T:" + k + "}}", _rich(v))
            out = out.replace("{{I:" + k + "}}", str(v))
        if page == "index":
            reviews = data.get("reviews") or []
            def _card(r):
                q = '<blockquote class="review-quote">' + _rich(r.get("quote", "")) + '</blockquote>'
                nm = (r.get("name") or "").strip()
                fc = '<figcaption class="review-name">' + _rich(nm) + '</figcaption>' if nm else ''
                return '<figure class="review-card">' + q + fc + '</figure>'
            cards = "".join(_card(r) for r in reviews if r.get("quote"))
            out = out.replace("{{REVIEWS}}", cards)
        open(os.path.join(ROOT, f"{page}.html"), "w", encoding="utf-8").write(out)
        print(f"  rendered {page}.html")


def analytics_snippet():
    """GA4 tag, injected at build time.

    The measurement ID lives in the Netlify environment variable
    GA_MEASUREMENT_ID, not in this repo, so it is never committed and can be
    changed without a code deploy. If the variable is unset (local builds,
    previews) nothing is injected at all.
    """
    gid = os.environ.get("GA_MEASUREMENT_ID", "").strip()
    if not gid:
        return ""
    return (
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>\n'
        '    <script>\n'
        '      window.dataLayer = window.dataLayer || [];\n'
        '      function gtag(){dataLayer.push(arguments);}\n'
        "      gtag('js', new Date());\n"
        f"      gtag('config', '{gid}');\n"
        '    </script>\n'
    )


def stamp_analytics():
    """Put the tag on every page the site actually serves. Runs last so it
    catches the generated pages too."""
    tag = analytics_snippet()
    if not tag:
        print("  GA_MEASUREMENT_ID not set, skipping analytics tag")
        return
    n = 0
    for path in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
        if os.path.basename(path).startswith("_"):
            continue                      # _project_template.html is not served
        s = open(path, encoding="utf-8").read()
        if "googletagmanager.com/gtag" in s:
            continue
        s = s.replace("</head>", "    " + tag + "</head>", 1)
        open(path, "w", encoding="utf-8").write(s)
        n += 1
    print(f"  analytics tag added to {n} page(s)")


def main():
    render_pages()
    entries = []
    placeholders = []          # "coming soon" holder tiles: shown in grid, no page
    for md in sorted(glob.glob(os.path.join(PROJ_DIR, "*", "project.md"))):
        pdir = os.path.dirname(md)
        slug = os.path.basename(pdir)
        if slug.startswith("_"):        # skip projects/_TEMPLATE
            continue
        d = parse(md)
        d["_slug"] = slug
        # A coming-soon holder fills a grid slot but has no photos and no page.
        if d.get("coming_soon"):
            placeholders.append(d)
            print(f"  placeholder tile: {slug}")
            continue
        covers = sorted(glob.glob(os.path.join(pdir, "cover.*")))
        d["cover"] = ("/" + os.path.relpath(covers[0], ROOT)) if covers else None
        # Optional wide hero image for the project page banner. Falls back to cover.
        heroes = sorted(glob.glob(os.path.join(pdir, "hero.*")))
        d["hero"] = ("/" + os.path.relpath(heroes[0], ROOT)) if heroes else None
        gfiles = [g for g in sorted(glob.glob(os.path.join(pdir, "gallery", "*")))
                  if g.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
        d["gallery"] = ["/" + os.path.relpath(g, ROOT) for g in gfiles]
        missing = [k for k in REQUIRED if not d.get(k)]
        if missing:
            print(f"SKIP {slug} -> missing required: {', '.join(missing)}")
            continue
        entries.append(d)

    entries.sort(key=sort_key)
    if not entries:
        print("No valid entries. Leaving gallery empty.")

    # detail pages
    for idx, d in enumerate(entries):
        title_plain, title_display = title_forms(d["title"])
        alt = f"{title_plain} interior design in {d['location']}"
        d["_cover_opt"] = optimize(d["cover"], 1000)
        hero_opt = optimize(d["hero"] or d["cover"], 1800)
        imgs = []
        for g in (d.get("gallery") or []):
            src = g.get("image") if isinstance(g, dict) else g
            if src:
                imgs.append(optimize(src, 1600))
        if not imgs:
            imgs = [d["_cover_opt"]]
        d["_page_images"] = imgs
        nxt = (f"project-{entries[(idx+1) % len(entries)]['_slug']}.html"
               if len(entries) > 1 else "projects.html")
        canonical = f"{BASE}/project-{d['_slug']}.html"
        ogimage = f"{BASE}{hero_opt}"
        page = (TEMPLATE
                .replace("{{TITLE_DISPLAY}}", title_display)
                .replace("{{TITLE}}", esc(title_plain))
                .replace("{{SERVICE}}", esc(d["service"]))
                .replace("{{LOCATION}}", esc(d["location"]))
                .replace("{{SUMMARY}}", esc(d["summary"]))
                .replace("{{METADESC}}", esc(" ".join(str(d["summary"]).split())[:155]))
                .replace("{{GALLERY}}", gallery_section(imgs, title_plain, d["location"]))
                .replace("{{SCHEMA}}", project_schema(d, title_plain, canonical, hero_opt, imgs))
                .replace("{{HERO}}", hero_opt)
                .replace("{{HERO_FOCUS}}", esc(d.get("hero_focus") or "center"))
                .replace("{{CANONICAL}}", canonical)
                .replace("{{OGIMAGE}}", ogimage)
                .replace("{{NEXT}}", nxt))
        open(os.path.join(ROOT, f"project-{d['_slug']}.html"), "w", encoding="utf-8").write(page)
        print(f"  built project-{d['_slug']}.html")

    # gallery grid -> projects.html (only the marked region is touched)
    cards = []
    for d in entries:
        t_plain, t_disp = title_forms(d["title"])
        cards.append(
            f'<a href="project-{d["_slug"]}.html" class="portfolio-item">'
            f'<img src="{d["_cover_opt"]}" alt="{esc(t_plain)} interior design in {esc(d["location"])}"'
            f'{dim_attrs(d["_cover_opt"])} loading="lazy" decoding="async">'
            f'<div class="portfolio-overlay">'
            f'<div class="portfolio-project-name">{t_disp}</div>'
            f'<div class="portfolio-location">{esc(d["location"])}</div>'
            f'<span class="portfolio-view">View Project</span></div></a>'
        )
    for d in placeholders:                 # non-clickable holder tiles, appended last
        cards.append(
            '<div class="portfolio-item portfolio-coming-soon">'
            '<span class="cs-title">More projects loading soon...</span>'
            '<span class="cs-rule"></span></div>'
        )
    grid = "\n            ".join(cards) if cards else ""
    pg = open(os.path.join(ROOT, "projects.html"), encoding="utf-8").read()
    pg = re.sub(
        r"(<!-- PROJECTS:START -->).*?(<!-- PROJECTS:END -->)",
        lambda m: f"{m.group(1)}\n            {grid}\n            {m.group(2)}",
        pg, flags=re.S,
    )
    open(os.path.join(ROOT, "projects.html"), "w", encoding="utf-8").write(pg)

    # sitemap.xml (regenerated each build so new projects are included).
    # Includes the image extension: a portfolio site earns real traffic from
    # Google Images, and this is the only way those photos get declared.
    from datetime import date
    today = date.today().isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
          '        xmlns:image="http://www.google.com/schemas/sitemaps/image/1.1">']

    def add(loc, images=(), caption=None):
        sm.append("  <url>")
        sm.append(f"    <loc>{BASE}{loc}</loc>")
        sm.append(f"    <lastmod>{today}</lastmod>")
        for src in images:
            sm.append("    <image:image>")
            sm.append(f"      <image:loc>{BASE}{src}</image:loc>")
            if caption:
                sm.append(f"      <image:caption>{esc(caption)}</image:caption>")
            sm.append("    </image:image>")
        sm.append("  </url>")

    for loc in ["/", "/about.html", "/services.html", "/contact.html"]:
        add(loc)
    add("/projects.html", [d["_cover_opt"] for d in entries],
        "Hearten Home Interiors portfolio, Dallas Fort Worth")
    n_img = len(entries)
    for d in entries:
        t_plain, _ = title_forms(d["title"])
        imgs = d.get("_page_images") or [d["_cover_opt"]]
        n_img += len(imgs)
        add(f"/project-{d['_slug']}.html", imgs,
            f"{t_plain}, {d['location']} interior design by Hearten Home Interiors")

    sm.append("</urlset>")
    open(os.path.join(ROOT, "sitemap.xml"), "w").write("\n".join(sm) + "\n")
    print(f"sitemap.xml written ({len(entries) + 5} URLs, {n_img} images)")

    stamp_analytics()

    print(f"Done. {len(entries)} project(s) live in the portfolio.")


if __name__ == "__main__":
    main()
