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
from PIL import Image
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
    name = slugify(os.path.splitext(os.path.basename(src))[0])
    out_rel = f"/images/projects/opt/{name}-{max_w}.webp"
    out = os.path.join(ROOT, out_rel.lstrip("/"))
    try:
        im = Image.open(src).convert("RGB")
        if im.width > max_w:
            im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
        im.save(out, "WEBP", quality=82, method=6)
        return out_rel
    except Exception as e:
        print(f"  ! image skipped ({src_rel}): {e}")
        return src_rel


def gallery_section(images, alt):
    blocks, i = [], 0
    while i < len(images):
        if i + 1 < len(images):
            blocks.append(
                '<div class="gallery-grid gallery-2-col">\n'
                f'            <img src="{images[i]}" alt="{alt}" loading="lazy">\n'
                f'            <img src="{images[i+1]}" alt="{alt}" loading="lazy">\n'
                "        </div>"
            )
            i += 2
        else:
            blocks.append(
                '<div class="gallery-grid gallery-1-col">\n'
                f'            <img src="{images[i]}" alt="{alt}" loading="lazy">\n'
                "        </div>"
            )
            i += 1
    return ('<section class="project-gallery-section reveal">\n        '
            + "\n        ".join(blocks) + "\n    </section>")


def sort_key(d):
    order = d.get("order")
    order = order if isinstance(order, (int, float)) else 9999
    year = int(re.sub(r"\D", "", str(d.get("year", "0"))) or 0)
    return (order, -year)



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
            out = out.replace("{{T:" + k + "}}", html.escape(str(v), quote=False))
            out = out.replace("{{I:" + k + "}}", str(v))
        open(os.path.join(ROOT, f"{page}.html"), "w", encoding="utf-8").write(out)
        print(f"  rendered {page}.html")


def main():
    render_pages()
    entries = []
    for path in sorted(glob.glob(os.path.join(PROJ_DIR, "*.md"))):
        d = parse(path)
        d["_slug"] = slugify(os.path.splitext(os.path.basename(path))[0])
        missing = [k for k in REQUIRED if not d.get(k)]
        if missing:
            print(f"SKIP {os.path.basename(path)} -> missing required: {', '.join(missing)}")
            continue
        entries.append(d)

    entries.sort(key=sort_key)
    if not entries:
        print("No valid entries. Leaving gallery empty.")

    # detail pages
    for idx, d in enumerate(entries):
        alt = f"{d['title']} interior design in {d['location']}"
        d["_cover_opt"] = optimize(d["cover"], 1000)
        hero_opt = optimize(d["cover"], 1800)
        imgs = []
        for g in (d.get("gallery") or []):
            src = g.get("image") if isinstance(g, dict) else g
            if src:
                imgs.append(optimize(src, 1600))
        if not imgs:
            imgs = [d["_cover_opt"]]
        nxt = (f"project-{entries[(idx+1) % len(entries)]['_slug']}.html"
               if len(entries) > 1 else "projects.html")
        canonical = f"{BASE}/project-{d['_slug']}.html"
        ogimage = f"{BASE}{hero_opt}"
        page = (TEMPLATE
                .replace("{{TITLE}}", esc(d["title"]))
                .replace("{{SERVICE}}", esc(d["service"]))
                .replace("{{LOCATION}}", esc(d["location"]))
                .replace("{{SUMMARY}}", esc(d["summary"]))
                .replace("{{METADESC}}", esc(" ".join(str(d["summary"]).split())[:155]))
                .replace("{{GALLERY}}", gallery_section(imgs, esc(alt)))
                .replace("{{HERO}}", hero_opt)
                .replace("{{CANONICAL}}", canonical)
                .replace("{{OGIMAGE}}", ogimage)
                .replace("{{NEXT}}", nxt))
        open(os.path.join(ROOT, f"project-{d['_slug']}.html"), "w", encoding="utf-8").write(page)
        print(f"  built project-{d['_slug']}.html")

    # gallery grid -> projects.html (only the marked region is touched)
    cards = []
    for d in entries:
        cards.append(
            f'<a href="project-{d["_slug"]}.html" class="portfolio-item">'
            f'<img src="{d["_cover_opt"]}" alt="{esc(d["title"])}" loading="lazy">'
            f'<div class="portfolio-overlay">'
            f'<div class="portfolio-project-name">{esc(d["title"])}</div>'
            f'<div class="portfolio-location">{esc(d["location"])}</div>'
            f'<span class="portfolio-view">View Project</span></div></a>'
        )
    grid = "\n            ".join(cards) if cards else ""
    pg = open(os.path.join(ROOT, "projects.html"), encoding="utf-8").read()
    pg = re.sub(
        r"(<!-- PROJECTS:START -->).*?(<!-- PROJECTS:END -->)",
        lambda m: f"{m.group(1)}\n            {grid}\n            {m.group(2)}",
        pg, flags=re.S,
    )
    open(os.path.join(ROOT, "projects.html"), "w", encoding="utf-8").write(pg)

    # sitemap.xml (regenerated each build so new projects are included)
    from datetime import date
    today = date.today().isoformat()
    locs = ["/", "/about.html", "/services.html", "/projects.html", "/contact.html"]
    locs += [f"/project-{d['_slug']}.html" for d in entries]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc in locs:
        sm.append(f"  <url><loc>{BASE}{loc}</loc><lastmod>{today}</lastmod></url>")
    sm.append("</urlset>")
    open(os.path.join(ROOT, "sitemap.xml"), "w").write("\n".join(sm) + "\n")
    print(f"sitemap.xml written ({len(locs)} URLs)")

    print(f"Done. {len(entries)} project(s) live in the portfolio.")


if __name__ == "__main__":
    main()
