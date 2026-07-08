# Setup Notes (for Jayce)

## What this is
A build-step portfolio system. Bonnie edits via Decap CMS at /admin; on each
publish, Netlify runs `build.py`, which compresses photos and regenerates the
project detail pages + the gallery grid in projects.html.

## Files
- `projects/*.md`         - one file per project (the CMS writes these)
- `build.py`              - the generator (image compression + page generation)
- `_project_template.html`- tokenized detail-page template (matches the site design)
- `admin/config.yml`      - CMS form definition, scoped to the projects collection only
- `admin/index.html`      - loads Decap CMS
- `netlify.toml`          - build command (`python3 build.py`)
- `images/projects/`      - uploaded originals; `images/projects/opt/` = generated WebP

## To turn on Bonnie's login (do during the domain pass)
1. Netlify dashboard -> the site -> **Identity** -> Enable Identity.
2. **Identity -> Registration -> Invite only.**
3. **Identity -> Services -> Git Gateway -> Enable.**
4. Add this snippet before `</body>` in `index.html` so the email invite link
   redirects to /admin/ after she sets her password:
   ```html
   <script src="https://identity.netlify.com/v1/netlify-identity-widget.js"></script>
   <script>
     if (window.netlifyIdentity) {
       window.netlifyIdentity.on("init", user => {
         if (!user) window.netlifyIdentity.on("login", () => { location.href = "/admin/"; });
       });
     }
   </script>
   ```
5. **Identity -> Invite users -> Bonnie's email.** She gets an email, sets a
   password, and is in. No GitHub account involved.
6. Update `site_url` in `admin/config.yml` to the real domain.

## Local testing
`pip install pyyaml Pillow && python3 build.py` regenerates everything. Open the
files directly to preview. (CMS auth needs the deployed site + Identity.)

## Optional later: swap Decap -> Sveltia CMS
Sveltia is the more modern, faster editor and reuses this exact config.yml.
Swap the script line in `admin/index.html` once you've confirmed its Git Gateway
login works for a non-GitHub user. Decap is the safe default for Bonnie today.

## Note
`projects/*.md`, `build.py`, and `_project_template.html` deploy publicly with
`publish = "."`. Harmless (no secrets), but if you'd rather hide them, move
sources outside the publish dir and adjust the build.

## Editable pages system (added)
- `setup_pages.py`  - one-time extractor (already run). Converted the 4 pages into
  editable templates. Re-run only if you change which elements are editable.
- `_templates/*.html` - tokenized page templates (head/nav/footer preserved verbatim).
- `content/*.json`    - the editable text/photo values the CMS writes.
- `build.py` `render_pages()` regenerates index/about/services/contact each deploy.
- Verified: with current content, rebuilt pages are byte-identical to the originals.
- Locked by design: headings containing inline styling (italic <em> accents, <br>
  line breaks) stay fixed in the templates so the typography can't be broken. All
  plain-text content and all photos are exposed as fields. To expose a locked
  heading later, edit the template + add it to `content/*.json` and `admin/config.yml`.
