#!/usr/bin/env python3
"""
ONE-TIME setup: converts index/about/services/contact into editable templates.

Rule for foolproofness:
  - Any element whose visible content is PLAIN TEXT (no inline tags) becomes an
    editable field. Photos become image fields.
  - Any heading with inline styling (italic accents <em>, line breaks <br>) is
    LEFT FIXED in the template, so Bonnie can never break the typographic design.

Output:
  _templates/<page>.html   tokenized template (head/nav/footer preserved verbatim)
  content/<page>.json      current values (what the CMS edits)
  _pages_config.yml        the CMS field definitions to paste into admin/config.yml
"""
import os, re, json, html

PAGES = ["index", "about", "services", "contact"]
LABELS = {"index": "Home Page", "about": "About Page",
          "services": "Services Page", "contact": "Contact Page"}
os.makedirs("_templates", exist_ok=True)
os.makedirs("content", exist_ok=True)

# (regex, friendly type) - order matters; specific spans before generic <p>
TEXT_PATTERNS = [
    (r'<span class="eyebrow">(\s*)(.*?)(\s*)</span>', "Eyebrow"),
    (r'<span class="pillar-number">(\s*)(.*?)(\s*)</span>', "Number"),
    (r'<span class="service-number">(\s*)(.*?)(\s*)</span>', "Number"),
    (r'<span class="service-includes-label">(\s*)(.*?)(\s*)</span>', "Label"),
    (r'<span class="contact-detail-label">(\s*)(.*?)(\s*)</span>', "Label"),
    (r'<span class="definition-word">(\s*)(.*?)(\s*)</span>', "Word"),
    (r'<span class="definition-phonetic">(\s*)(.*?)(\s*)</span>', "Pronunciation"),
    (r'<h1[^>]*>(\s*)(.*?)(\s*)</h1>', "Heading"),
    (r'<h2[^>]*>(\s*)(.*?)(\s*)</h2>', "Heading"),
    (r'<h3[^>]*>(\s*)(.*?)(\s*)</h3>', "Subheading"),
    (r'<h4[^>]*>(\s*)(.*?)(\s*)</h4>', "Subheading"),
    (r'<blockquote[^>]*>(\s*)(.*?)(\s*)</blockquote>', "Quote"),
    (r'<li[^>]*>(\s*)(.*?)(\s*)</li>', "List item"),
    (r'<a [^>]*class="[^"]*btn[^"]*"[^>]*>(\s*)(.*?)(\s*)</a>', "Button"),
    (r'<label[^>]*>(\s*)(.*?)(\s*)</label>', "Form label"),
    (r'<option[^>]*>(\s*)(.*?)(\s*)</option>', "Dropdown option"),
    (r'<button[^>]*>(\s*)(.*?)(\s*)</button>', "Button"),
    (r'<p[^>]*>(\s*)(.*?)(\s*)</p>', "Text"),
]
IMG_PATTERN = r'(<img [^>]*src=")([^"]+)("[^>]*>)'

config_files = []

for page in PAGES:
    raw = open(f"{page}.html").read()
    # operate only on main content (between </nav> and <footer>); head/nav/footer untouched
    nav_end = raw.index("</nav>") + len("</nav>")
    foot_start = raw.index("<footer")
    head, main, foot = raw[:nav_end], raw[nav_end:foot_start], raw[foot_start:]

    values, fields = {}, []
    counters = {}

    def add_field(tagkey, friendly, value, widget):
        counters[tagkey] = counters.get(tagkey, 0) + 1
        key = f"{page}_{tagkey}{counters[tagkey]}"
        values[key] = value
        preview = re.sub(r"\s+", " ", html.unescape(re.sub("<[^>]+>", "", str(value)))).strip()
        label = f"{friendly}: {preview[:45]}" + ("..." if len(preview) > 45 else "")
        f = {"label": label, "name": key, "widget": widget, "required": False}
        if widget != "image":
            f["hint"] = f"Currently: {preview[:140]}"
        fields.append(f)
        return key

    # --- images ---
    def img_sub(m):
        src = m.group(2)
        if src.startswith("data:"):
            return m.group(0)
        key = add_field("photo", "Photo", src, "image")
        return f"{m.group(1)}{{{{I:{key}}}}}{m.group(3)}"
    main = re.sub(IMG_PATTERN, img_sub, main)

    # --- text ---
    for pattern, friendly in TEXT_PATTERNS:
        def text_sub(m, friendly=friendly):
            lead, inner, trail = m.group(1), m.group(2), m.group(3)
            if "<" in inner or inner.strip() == "":
                return m.group(0)            # has inline markup or empty -> leave fixed
            value = html.unescape(inner)
            widget = "text" if len(value) > 70 else "string"
            key = add_field(friendly.split()[0].lower(), friendly, value, widget)
            full = m.group(0)
            return full.replace(f"{lead}{inner}{trail}", f"{lead}{{{{T:{key}}}}}{trail}", 1)
        main = re.sub(pattern, text_sub, main, flags=re.S)

    open(f"_templates/{page}.html", "w").write(head + main + foot)
    json.dump(values, open(f"content/{page}.json", "w"), indent=2, ensure_ascii=False)
    config_files.append((page, LABELS[page], fields))
    print(f"{page}: {len(fields)} editable fields "
          f"({sum(1 for f in fields if f['widget']=='image')} photos, "
          f"{sum(1 for f in fields if f['widget']!='image')} text)")

# emit CMS config fragment
lines = ['  - name: "pages"', '    label: "Website Pages"',
         '    label_singular: "Page"', '    editor: { preview: false }', '    files:']
for page, label, fields in config_files:
    lines += [f'      - name: "{page}"', f'        label: "{label}"',
              f'        file: "content/{page}.json"', '        fields:']
    for f in fields:
        lines.append(f'          - label: {json.dumps(f["label"])}')
        lines.append(f'            name: "{f["name"]}"')
        lines.append(f'            widget: "{f["widget"]}"')
        lines.append('            required: false')
        if "hint" in f:
            lines.append(f'            hint: {json.dumps(f["hint"])}')
open("_pages_config.yml", "w").write("\n".join(lines) + "\n")
print("\nWrote _pages_config.yml")
