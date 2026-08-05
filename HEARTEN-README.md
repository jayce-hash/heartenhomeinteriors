# Hearten Home — Site Guide

Everything is edited in GitHub. Push a change and Netlify rebuilds the site automatically.
You never edit the finished `.html` files at the root — those are generated. You edit the
`content/` files, the `projects/` folders, and drop images into the `images/` folders.

---

## Where every image goes

```
images/
  team/        Bonnie, Tripp, McKlane O'Neal photos
                 bonnie.webp
                 tripp-1.jpg
                 tripp-2.jpg
                 mcklane.jpg
  services/    The three service photos (Services page)
                 renovation.jpg
                 design.jpg
                 styling.jpg
  site/        Brand assets — rarely change
                 logo-monogram-navy.png
                 logo-wordmark-footer.png
                 logo-wordmark-navy.png
                 logo-monogram-white.png
                 share-default.jpg   (social share preview)
  projects/
    opt/       AUTO-GENERATED optimized photos. Never touch this folder.

favicon.ico / favicon-16.png / favicon-32.png / apple-touch-icon.png
                 Live at the repo root (browser requirement). Set-and-forget.
```

**To replace a photo:** drop a new file into the right folder using the **same filename**
and push. That's it. (e.g. swap `images/team/tripp-1.jpg` with the real Tripp photo.)

---

## How to add a portfolio project (the reusable format)

Each project is one self-contained folder inside `projects/`.

1. **Copy** the `projects/_TEMPLATE/` folder and **rename** the copy to your project's
   web name, lowercase with dashes. Example: `projects/lakeside-family-kitchen/`
   (this name becomes the page URL).
2. Open `project.md` in that folder and fill in the details:
   ```
   ---
   title: A Kitchen Built for Sunday Mornings
   service: Turn-Key Renovation
   location: Southlake, TX
   year: "2024"
   summary: "One or two warm sentences about the project."
   order: 1
   ---
   ```
   - `order` controls position in the grid (1 shows first).
3. Replace **`cover.jpg`** with the main photo (this is the grid thumbnail + the big
   hero image on the project page). It can be .jpg, .png, or .webp — just name it `cover`.
4. Put any additional photos in the **`gallery/`** folder, named `01.jpg`, `02.jpg`,
   `03.jpg`… They appear on the project page in that order.
5. Push. The new project page and the portfolio grid build automatically.

**To remove a project:** delete its folder and push.

That's the whole system — a project = a folder with `project.md`, a `cover`, and a
`gallery/`. No paths to wire up, no filenames to match anywhere else.

---

## Where page text lives

```
content/
  index.json      Home page text
  about.json      About page text (Bonnie/Tripp story, team names & roles)
  services.json   Services page text
  contact.json    Contact page text
```

Two formatting tricks that work in the big **headline** fields (not body paragraphs):
- Wrap a word in `*asterisks*` to make it slanted/italic — e.g. `Turn-Key *Renovations*`.
- Press Enter for a line break inside a headline.

Photo fields in these files point at the `images/…` paths above — leave the paths alone,
just replace the actual image files.
