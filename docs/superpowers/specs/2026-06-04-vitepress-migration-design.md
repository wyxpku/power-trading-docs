# VitePress Migration Design Spec

**Goal:** Migrate the book reader from hand-crafted HTML to VitePress, adding a three-level collapsible sidebar tree (篇 > 章 > 节) and deploying to GitHub Pages while preserving the split-view OCR+scan reading experience.

**Repository:** `wyxpku/power-trading-docs` on GitHub

---

## 1. Architecture

### Current state

- 34 hand-crafted HTML files in `book/` (preface, 31 chapters, 2 appendices)
- Inline sidebar HTML duplicated in every file
- Custom CSS themes (light/cream/dark) in `book/css/style.css`
- Custom JS for scroll-synced scan panel and section navigation
- 647 page scan PNGs in `book/pages/`, 129 figure crops in `book/pages/crops/`
- OCR source data in `book/scripts/paddleocr_output/` (JSON per page)

### Target state

- VitePress site in `book-vitepress/` at repo root
- Content as Markdown files with embedded HTML for tables
- VitePress config drives the three-level sidebar
- Custom Vue component `<ScanViewer>` for split-view reading
- Custom Vue component `<PageDivider>` for page breaks
- GitHub Actions workflow for auto-deployment to GitHub Pages
- URL: `wyxpku.github.io/power-trading-docs/`

### File structure

```
book-vitepress/
├── .vitepress/
│   ├── config.ts              # Sidebar config, theme, nav
│   └── theme/
│       ├── index.ts           # Custom theme setup
│       ├── ScanViewer.vue     # Split-view scan panel component
│       └── PageDivider.vue    # Page break marker component
├── public/
│   └── pages/                 # Symlink or copy from book/pages/
│       ├── page_001.png
│       │   ...
│       └── crops/
├── index.md                   # Landing/home page
├── preface.md
├── ch01/
│   └── index.md
├── ch02/
│   └── index.md
├── ...                        # ch03 through ch31
├── ch31/
│   └── index.md
├── appendix-a.md
└── appendix-b.md
```

---

## 2. Sidebar (Three-Level Tree)

### Structure

VitePress sidebar config supports collapsible groups natively. The config will be:

```
Level 1 (collapsible group): 序篇, 第一篇 理论篇, 第二篇 国外实践篇, ...
Level 2 (link per chapter):  第1章 电力市场概述, 第2章 电力现货市场组织, ...
Level 3 (auto-generated):    Section headings (1.1, 1.2, 1.2.1) via VitePress outline
```

### Accordion behavior

- Only the group containing the current chapter is expanded; all others are collapsed
- VitePress supports this via the `collapsed` property on sidebar groups — when a group has `collapsed: false` it's open, `collapsed: true` it's shut
- A small JS snippet in `.vitepress/theme/index.ts` enforces accordion: on route change, expand the active group, collapse all others

### Chapter mapping (from chapter_mapping.json)

| Group | Chapters | Pages |
|-------|----------|-------|
| 序篇 | preface | 3-18 |
| 第一篇 理论篇 | ch01-ch06 | 19-111 |
| 第二篇 国外实践篇 | ch07-ch12 | 112-249 |
| 第三篇 国内实践篇 | ch13-ch20 | 250-465 |
| 第四篇 技术支持系统篇 | ch21-ch30 | 466-585 |
| 第五篇 展望篇 | ch31 | 586-603 |
| 附录 | appendix-a, appendix-b | 604-646 |

---

## 3. Split-View Reading (ScanViewer)

### Component: `<ScanViewer>`

A Vue component embedded in each chapter's layout that provides:

1. **Scan image panel**: Fixed-position panel on the right showing the original page scan PNG
2. **Scroll sync**: Uses `IntersectionObserver` on `<PageDivider>` elements to update the scan image as the reader scrolls
3. **Toggle button**: Switch between "text only" and "split view" modes
4. **State persistence**: View mode saved to `localStorage`

### Component: `<PageDivider>`

A lightweight component rendered at each page boundary:

```html
<PageDivider :pdf-page="19" :book-page="2" />
```

Renders as a thin horizontal divider with a page number badge. Acts as the `IntersectionObserver` sentinel.

### Integration approach

Register these as global components in `.vitepress/theme/index.ts` so they're available in all Markdown files without imports. The `<ScanViewer>` wraps the entire page content via VitePress layout slots.

---

## 4. Content Conversion

### Source data

Per-page JSON files in `book/scripts/paddleocr_output/page_XXXX/*.json` with `parsing_res_list` blocks.

### Conversion rules

| OCR block label | VitePress output |
|-----------------|------------------|
| `doc_title` | `# Title` (h1) |
| `paragraph_title` matching `N.N ` | `## Title` (h2) |
| `paragraph_title` matching `N.N.N ` | `### Title` (h3) |
| `paragraph_title` matching `N.N.N.N` | `#### Title` (h4) |
| `text` | Plain paragraph text |
| `image` | `![caption](/pages/crops/xxx.png)` |
| `figure_title` | `*caption*` (italic, below figure) |
| `table` | Raw HTML `<table>...</table>` (VitePress supports inline HTML) |
| `header`, `header_image`, `number` | Skipped (running headers/footers) |

### Conversion script

A new Python script `book/scripts/convert_to_vitepress.py` that:
1. Reads `chapter_mapping.json` for page ranges
2. For each chapter, reads per-page JSON and converts blocks to Markdown
3. Inserts `<PageDivider>` components between pages
4. Writes output to `book-vitepress/chXX/index.md`

### Markdown frontmatter

Each chapter file gets frontmatter for VitePress:

```yaml
---
title: 第1章 电力市场概述
---
```

---

## 5. Theme and Styling

### VitePress default theme with customizations

- Use VitePress default theme as base (already has dark/light mode toggle)
- Add a "cream" theme option via CSS custom properties override
- Port the glassmorphism sidebar styles from existing `style.css`
- Port table container styles for OCR tables
- Port figure/embedded-figure styles for crops

### Color themes

Map existing three themes to VitePress:
- Light → VitePress light (with CSS overrides for cream tint if needed)
- Cream → Custom CSS variable set activated via body class
- Dark → VitePress built-in dark mode

---

## 6. GitHub Pages Deployment

### GitHub Actions workflow

File: `.github/workflows/deploy.yml`

```yaml
name: Deploy VitePress site to Pages
on:
  push:
    branches: [main]
    paths: ['book-vitepress/**', '.github/workflows/deploy.yml']
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
        working-directory: book-vitepress
      - run: npm run docs:build
        working-directory: book-vitepress
      - uses: actions/upload-pages-artifact@v3
        with:
          path: book-vitepress/.vitepress/dist
  deploy:
    needs: build
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
    steps:
      - uses: actions/deploy-pages@v4
```

### VitePress config for subdirectory

In `config.ts`:
```ts
export default defineConfig({
  base: '/power-trading-docs/',
  // ...
})
```

### Static assets (page scans)

Page scans (647 PNGs, ~284 MB) are too large for the repo. Options:

1. **Git LFS** — store scans in LFS, GitHub Actions checks them out for build
2. **Symlink + .gitignore** — scans stay in `book/pages/`, build script copies them to `book-vitepress/public/pages/` before build (not committed)
3. **External hosting** — upload scans to GitHub Releases or CDN, reference by URL

**Recommended: Option 1 (Git LFS)** for simplicity. The scans are already tracked in git. Adding LFS retroactively keeps everything in one place.

---

## 7. Migration Steps (High-Level)

1. Initialize VitePress project in `book-vitepress/`
2. Configure sidebar with three-level tree (hand-edit config.ts)
3. Write conversion script `convert_to_vitepress.py` and run it
4. Implement `<ScanViewer>` and `<PageDivider>` Vue components
5. Port theme customizations (cream mode, glassmorphism sidebar, table/figure styles)
6. Add GitHub Actions workflow for deployment
7. Test locally with `npm run docs:dev`
8. Push and verify GitHub Pages deployment

---

## 8. Scope and Non-Goals

### In scope

- VitePress project setup and configuration
- Three-level collapsible sidebar with accordion behavior
- Content conversion (OCR JSON → Markdown)
- Split-view scan reader (Vue components)
- Theme customization (light/cream/dark)
- GitHub Pages deployment via Actions

### Out of scope

- Full-text search (VitePress has built-in search, no extra work needed)
- Mobile responsive design beyond what VitePress provides by default
- Re-running OCR or modifying OCR content
- PDF export or offline reading
- User accounts or analytics
