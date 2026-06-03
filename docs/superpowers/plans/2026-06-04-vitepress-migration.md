# VitePress Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the book reader from hand-crafted HTML to VitePress with a three-level collapsible sidebar (篇 > 章 > 节) and deploy to GitHub Pages, preserving split-view OCR+scan reading.

**Architecture:** VitePress site in `book-vitepress/` with content converted from OCR JSON to Markdown. Custom Vue components (`ScanViewer`, `PageDivider`) provide split-view reading. GitHub Actions deploys to `wyxpku.github.io/power-trading-docs/`.

**Tech Stack:** VitePress 1.x + Vue 3 + TypeScript + Python 3.12 (conversion script) + GitHub Actions

---

## Pre-flight: Repository State

| Item | Value |
|------|-------|
| Repo | `wyxpku/power-trading-docs` on `main` branch |
| OCR data | `book/scripts/paddleocr_output/` — 646 per-page JSON files |
| Chapter mapping | `book/scripts/paddleocr_output/chapter_mapping.json` — 34 entries |
| Page scans | `book/pages/` — 646 PNGs (264 MB) + 129 crops (6 MB) |
| Node.js | None currently — fresh setup |

---

## File Structure

### New files to create:

| File | Purpose |
|------|---------|
| `book-vitepress/package.json` | Node.js project with VitePress dependency |
| `book-vitepress/.vitepress/config.ts` | Sidebar tree, theme, nav, site metadata |
| `book-vitepress/.vitepress/theme/index.ts` | Custom theme: register global Vue components |
| `book-vitepress/.vitepress/theme/ScanViewer.vue` | Split-view scan panel component |
| `book-vitepress/.vitepress/theme/PageDivider.vue` | Page break marker component |
| `book-vitepress/.vitepress/theme/styles/custom.css` | Custom CSS: cream theme, tables, figures, glassmorphism |
| `book-vitepress/index.md` | Landing page |
| `book-vitepress/preface.md` | Preface content |
| `book-vitepress/ch01/index.md` through `ch31/index.md` | Chapter content (31 files) |
| `book-vitepress/appendix-a.md`, `appendix-b.md` | Appendix content |
| `book/scripts/convert_to_vitepress.py` | OCR JSON → VitePress Markdown conversion script |
| `.github/workflows/deploy.yml` | GitHub Actions workflow for Pages deployment |

### Files to preserve (unchanged, referenced via symlink):

| File | Note |
|------|------|
| `book/pages/page_NNN.png` | Page scan images — symlinked into VitePress public/ |
| `book/pages/crops/*.png` | Figure crops — symlinked into VitePress public/ |
| `book/scripts/paddleocr_output/` | OCR source data — used by conversion script |

---

### Task 1: Initialize VitePress Project

**Files:**
- Create: `book-vitepress/package.json`
- Create: `book-vitepress/.vitepress/config.ts` (minimal skeleton)
- Create: `book-vitepress/index.md` (placeholder landing page)

- [ ] **Step 1: Create project directory and package.json**

```bash
mkdir -p book-vitepress/.vitepress/theme/styles
cd book-vitepress
cat > package.json << 'JSONEOF'
{
  "name": "power-trading-book",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "docs:dev": "vitepress dev",
    "docs:build": "vitepress build",
    "docs:preview": "vitepress preview"
  },
  "devDependencies": {
    "vitepress": "^1.6.0",
    "vue": "^3.5.0"
  }
}
JSONEOF
```

- [ ] **Step 2: Install dependencies**

```bash
cd book-vitepress && npm install
```

Expected: `node_modules/` created, VitePress and Vue installed.

- [ ] **Step 3: Create minimal VitePress config**

Create `book-vitepress/.vitepress/config.ts`:

```ts
import { defineConfig } from 'vitepress'

export default defineConfig({
  title: '电力现货市场实务',
  description: '国家电力调度控制中心 组编',
  base: '/power-trading-docs/',
  themeConfig: {
    nav: [
      { text: '首页', link: '/' },
    ],
    sidebar: [],
    search: {
      provider: 'local',
    },
    outline: {
      level: [2, 4],
      label: '本章节导航',
    },
  },
})
```

- [ ] **Step 4: Create placeholder landing page**

Create `book-vitepress/index.md`:

```markdown
---
layout: home

hero:
  name: "电力现货市场实务"
  text: "国家电力调度控制中心 组编"
  tagline: 在线电子书阅读器
  actions:
    - theme: brand
      text: 开始阅读
      link: /preface
---
```

- [ ] **Step 5: Create symlink for page scans**

```bash
cd book-vitepress
mkdir -p public
ln -s ../../book/pages public/pages
```

Verify: `ls public/pages/page_001.png` should show the file.

- [ ] **Step 6: Test dev server starts**

```bash
cd book-vitepress && npx vitepress dev --port 5173 &
sleep 5
curl -s http://localhost:5173/power-trading-docs/ | head -20
kill %1
```

Expected: HTML response with VitePress shell.

- [ ] **Step 7: Commit**

```bash
cd /Users/ethan/workspace/power-trading
echo "node_modules/" >> book-vitepress/.gitignore
echo ".vitepress/dist/" >> book-vitepress/.gitignore
echo ".vitepress/cache/" >> book-vitepress/.gitignore
git add book-vitepress/
git commit -m "feat: initialize VitePress project skeleton"
```

---

### Task 2: Configure Three-Level Sidebar

**Files:**
- Modify: `book-vitepress/.vitepress/config.ts`
- Create: `book-vitepress/preface.md` (placeholder)
- Create: `book-vitepress/ch01/index.md` through `ch31/index.md` (placeholders)
- Create: `book-vitepress/appendix-a.md`, `book-vitepress/appendix-b.md` (placeholders)

- [ ] **Step 1: Create placeholder Markdown files for all chapters**

```bash
cd /Users/ethan/workspace/power-trading/book-vitepress

# Preface
echo "---\ntitle: 前言与序言\n---\n\n# 前言与序言\n\n（内容待转换）" > preface.md

# Chapters 01-31
for i in $(seq -w 1 31); do
  mkdir -p "ch${i}"
  echo "---\ntitle: 第${i}章\n---\n\n# 第${i}章\n\n（内容待转换）" > "ch${i}/index.md"
done

# Appendices
echo "---\ntitle: 附录A 电力现货市场规则框架示例\n---\n\n# 附录A\n\n（内容待转换）" > appendix-a.md
echo "---\ntitle: 附录B 电力现货市场导则范本\n---\n\n# 附录B\n\n（内容待转换）" > appendix-b.md
```

- [ ] **Step 2: Write full sidebar config**

Replace `book-vitepress/.vitepress/config.ts`:

```ts
import { defineConfig } from 'vitepress'

export default defineConfig({
  title: '电力现货市场实务',
  description: '国家电力调度控制中心 组编',
  base: '/power-trading-docs/',
  cleanUrls: true,
  themeConfig: {
    nav: [
      { text: '首页', link: '/' },
    ],
    sidebar: [
      {
        text: '序篇',
        collapsed: false,
        items: [
          { text: '前言与序言', link: '/preface' },
        ],
      },
      {
        text: '第一篇 理论篇',
        collapsed: true,
        items: [
          { text: '第1章 电力市场概述', link: '/ch01/' },
          { text: '第2章 电力现货市场组织', link: '/ch02/' },
          { text: '第3章 电力现货市场价格机制', link: '/ch03/' },
          { text: '第4章 电力现货市场阻塞管理', link: '/ch04/' },
          { text: '第5章 电力市场信息披露与风险管控', link: '/ch05/' },
          { text: '第6章 电力现货市场绩效评价', link: '/ch06/' },
        ],
      },
      {
        text: '第二篇 国外实践篇',
        collapsed: true,
        items: [
          { text: '第7章 美国 PJM 电力市场', link: '/ch07/' },
          { text: '第8章 美国 ERCOT 电力市场', link: '/ch08/' },
          { text: '第9章 英国 电力市场', link: '/ch09/' },
          { text: '第10章 欧洲统一电力市场', link: '/ch10/' },
          { text: '第11章 澳大利亚电力市场', link: '/ch11/' },
          { text: '第12章 巴西电力市场', link: '/ch12/' },
        ],
      },
      {
        text: '第三篇 国内实践篇',
        collapsed: true,
        items: [
          { text: '第13章 我国电力现货市场的演进', link: '/ch13/' },
          { text: '第14章 省间电力现货市场', link: '/ch14/' },
          { text: '第15章 浙江电力现货市场', link: '/ch15/' },
          { text: '第16章 山西电力现货市场', link: '/ch16/' },
          { text: '第17章 山东电力现货市场', link: '/ch17/' },
          { text: '第18章 福建电力现货市场', link: '/ch18/' },
          { text: '第19章 四川电力现货市场', link: '/ch19/' },
          { text: '第20章 甘肃电力现货市场', link: '/ch20/' },
        ],
      },
      {
        text: '第四篇 技术支持系统篇',
        collapsed: true,
        items: [
          { text: '第21章 电力现货市场技术支持系统总体概况', link: '/ch21/' },
          { text: '第22章 现货及辅助服务市场申报发布', link: '/ch22/' },
          { text: '第23章 电力现货市场出清', link: '/ch23/' },
          { text: '第24章 辅助服务市场出清', link: '/ch24/' },
          { text: '第25章 安全校核', link: '/ch25/' },
          { text: '第26章 市场分析', link: '/ch26/' },
          { text: '第27章 电力市场结算', link: '/ch27/' },
          { text: '第28章 模拟仿真', link: '/ch28/' },
          { text: '第29章 系统运维管理', link: '/ch29/' },
          { text: '第30章 安全防护', link: '/ch30/' },
        ],
      },
      {
        text: '第五篇 展望篇',
        collapsed: true,
        items: [
          { text: '第31章 "双碳"目标和新型电力系统下的电力市场展望', link: '/ch31/' },
        ],
      },
      {
        text: '附录',
        collapsed: true,
        items: [
          { text: '附录A 电力现货市场规则框架示例', link: '/appendix-a' },
          { text: '附录B 电力现货市场导则范本', link: '/appendix-b' },
        ],
      },
    ],
    search: {
      provider: 'local',
    },
    outline: {
      level: [2, 4],
      label: '本章节导航',
    },
  },
})
```

- [ ] **Step 3: Verify sidebar renders**

```bash
cd book-vitepress && npx vitepress dev --port 5173 &
sleep 5
curl -s http://localhost:5173/power-trading-docs/ch01/ | grep -c 'sidebar'
kill %1
```

Expected: Sidebar HTML present in the response.

- [ ] **Step 4: Commit**

```bash
cd /Users/ethan/workspace/power-trading
git add book-vitepress/
git commit -m "feat: configure VitePress sidebar with three-level tree structure"
```

---

### Task 3: Write OCR-to-Markdown Conversion Script

**Files:**
- Create: `book/scripts/convert_to_vitepress.py`

This script reads `chapter_mapping.json` and per-page OCR JSON, then outputs VitePress-compatible Markdown files.

- [ ] **Step 1: Write the conversion script**

Create `book/scripts/convert_to_vitepress.py`:

```python
#!/usr/bin/env python3
"""Convert PaddleOCR-VL output to VitePress Markdown files.

Reads:
  - book/scripts/paddleocr_output/chapter_mapping.json
  - book/scripts/paddleocr_output/page_XXXX/*.json

Writes:
  - book-vitepress/preface.md
  - book-vitepress/chXX/index.md (31 chapters)
  - book-vitepress/appendix-a.md, appendix-b.md
"""
import html as html_mod
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "book" / "scripts" / "paddleocr_output"
VITEPRESS_DIR = REPO_ROOT / "book-vitepress"
MAPPING_PATH = OUTPUT_DIR / "chapter_mapping.json"

BOOK_PAGE_OFFSET = 17
FIRST_CHAPTER_PDF_PAGE = 19


def load_page_json(page_idx: int) -> Optional[Dict]:
    page_dir = OUTPUT_DIR / f"page_{page_idx:04d}"
    json_files = list(page_dir.glob("*.json"))
    if not json_files:
        return None
    with open(json_files[0], "r", encoding="utf-8") as f:
        return json.load(f)


def detect_heading_level(text: str) -> str:
    text = text.strip()
    if not text:
        return "##"
    if re.match(r'^第\d+章\s', text):
        return '#'
    if re.match(r'^第[一二三四五六七八九十]+篇\s', text):
        return '#'
    if re.match(r'^附录[A-Z]\s', text):
        return '#'
    if text in ('前言', '序', '序言', '前言与序言'):
        return '#'
    if re.match(r'^\d+\.\d+\.\d+\.\d+', text):
        return '####'
    if re.match(r'^\d+\.\d+\.\d+', text):
        return '###'
    if re.match(r'^\d+\.\d+\s', text):
        return '##'
    return '##'


def block_to_markdown(block: Dict[str, Any], pdf_page: int) -> Optional[str]:
    """Convert a single OCR block to Markdown."""
    label = block.get("block_label", "")
    content = str(block.get("block_content", "")).strip()

    # Skip running headers, footers, page numbers
    if label in ("header", "header_image", "footer", "footer_image", "number"):
        return None

    # Skip empty blocks (unless image with crop)
    if not content and label != "image":
        return None

    # doc_title / paragraph_title → Markdown heading
    if label in ("doc_title", "paragraph_title"):
        level = detect_heading_level(content)
        return f'{level} {content}'

    # Text → paragraph
    if label == "text":
        paragraphs = re.split(r'\n\s*\n', content)
        parts = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            para = re.sub(r'\n', ' ', para)
            parts.append(para)
        return '\n\n'.join(parts)

    # Table → raw HTML (VitePress supports inline HTML in Markdown)
    if label == "table":
        if content.startswith('<'):
            return f'<div class="table-container">\n\n{content}\n\n</div>'
        return f'```\n{content}\n```'

    # Image → Markdown image with crop path
    if label == "image":
        crop_path = block.get("crop_path", "")
        fig_idx = block.get("figure_index", 0)
        if not crop_path:
            crop_path = f"pages/crops/page_{pdf_page:03d}_fig{fig_idx}.png"
        caption = f"图 page {pdf_page} fig {fig_idx}"
        return f'![{caption}](/{crop_path})'

    # Figure title → italic caption
    if label == "figure_title":
        return f'*{content}*'

    # Fallback
    if content:
        return content
    return None


def page_divider_markdown(pdf_page: int) -> str:
    if pdf_page >= FIRST_CHAPTER_PDF_PAGE:
        book_page = pdf_page - BOOK_PAGE_OFFSET
        badge = f"PDF 第 {pdf_page} 页 / 书第 {book_page} 页"
    else:
        badge = f"PDF 第 {pdf_page} 页"
    return (
        f'<PageDivider pdf-page="{pdf_page}" />'
        f'\n\n<!-- PAGE {badge} -->'
    )


def convert_chapter(chapter: Dict) -> str:
    """Convert a chapter's pages to Markdown string."""
    start_idx = chapter["start_page_idx"]
    end_idx = chapter["end_page_idx"]
    title = chapter["title"]

    parts: List[str] = []

    for page_idx in range(start_idx, end_idx + 1):
        data = load_page_json(page_idx)
        if data is None:
            continue
        blocks = data.get("parsing_res_list", [])
        pdf_page = page_idx + 1

        # Page divider
        parts.append(page_divider_markdown(pdf_page))

        # Block content
        for block in blocks:
            md = block_to_markdown(block, pdf_page)
            if md:
                parts.append(md)

    return '\n\n'.join(parts)


def get_chapter_file_info(chapter: Dict) -> tuple:
    """Return (output_path, frontmatter_title) for a chapter."""
    html_file = chapter["html_file"]
    title = chapter["title"]

    if html_file == "preface.html":
        return (VITEPRESS_DIR / "preface.md", title)
    elif html_file.startswith("chapter_"):
        num = html_file.replace("chapter_", "").replace(".html", "")
        return (VITEPRESS_DIR / f"ch{num}" / "index.md", title)
    elif html_file == "appendix_a.html":
        return (VITEPRESS_DIR / "appendix-a.md", title)
    elif html_file == "appendix_b.html":
        return (VITEPRESS_DIR / "appendix-b.md", title)
    else:
        return (VITEPRESS_DIR / html_file.replace(".html", ".md"), title)


def main():
    if not MAPPING_PATH.exists():
        print(f"ERROR: {MAPPING_PATH} not found. Run detect_chapters.py first.")
        return

    with open(MAPPING_PATH, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    print(f"Converting {len(mapping)} chapters to VitePress Markdown...")

    for chapter in mapping:
        output_path, title = get_chapter_file_info(chapter)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        content = convert_chapter(chapter)

        # Write with frontmatter
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"---\ntitle: {title}\n---\n\n")
            f.write(content)
            f.write("\n")

        pages = chapter["end_page_idx"] - chapter["start_page_idx"] + 1
        print(f"  {output_path.relative_to(VITEPRESS_DIR):30s}  {pages:2d} pages  {len(content):>7,} chars")

    print(f"\nDone! {len(mapping)} Markdown files in {VITEPRESS_DIR}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the conversion**

```bash
cd /Users/ethan/workspace/power-trading
source .venv/bin/activate
python book/scripts/convert_to_vitepress.py
```

Expected: 34 Markdown files generated in `book-vitepress/`.

- [ ] **Step 3: Verify output quality**

```bash
# Check file count
echo "MD files: $(find book-vitepress -name '*.md' -not -path '*/node_modules/*' | wc -l)"
# Expected: 35 (index + preface + 31 chapters + 2 appendices)

# Spot-check chapter 1
head -30 book-vitepress/ch01/index.md
```

Expected: Markdown with `#` headings, paragraphs, `<PageDivider>` components, `![...]` images, `<div class="table-container">` tables.

- [ ] **Step 4: Commit**

```bash
git add book/scripts/convert_to_vitepress.py book-vitepress/
git commit -m "feat: convert OCR content to VitePress Markdown"
```

---

### Task 4: Implement ScanViewer and PageDivider Vue Components

**Files:**
- Create: `book-vitepress/.vitepress/theme/PageDivider.vue`
- Create: `book-vitepress/.vitepress/theme/ScanViewer.vue`
- Create: `book-vitepress/.vitepress/theme/index.ts`

- [ ] **Step 1: Create PageDivider component**

Create `book-vitepress/.vitepress/theme/PageDivider.vue`:

```vue
<template>
  <div
    class="page-divider"
    :id="'page-div-' + pdfPage"
    :data-page="pdfPage"
  >
    <span class="page-number-badge">{{ badge }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps<{
  pdfPage: number
}>()

const badge = computed(() => {
  if (props.pdfPage >= 19) {
    const bookPage = props.pdfPage - 17
    return `PDF 第 ${props.pdfPage} 页 / 书第 ${bookPage} 页`
  }
  return `PDF 第 ${props.pdfPage} 页`
})
</script>

<style scoped>
.page-divider {
  border-top: 1px dashed var(--vp-c-divider);
  margin: 2rem 0 1rem;
  padding-top: 0.5rem;
  position: relative;
}

.page-number-badge {
  display: inline-block;
  font-size: 0.75rem;
  color: var(--vp-c-text-3);
  background: var(--vp-c-default-soft);
  padding: 2px 8px;
  border-radius: 4px;
  font-family: monospace;
}
</style>
```

- [ ] **Step 2: Create ScanViewer component**

Create `book-vitepress/.vitepress/theme/ScanViewer.vue`:

```vue
<template>
  <div class="scan-viewer" :class="{ 'scan-hidden': !showScan }">
    <div class="scan-panel">
      <img
        ref="scanImg"
        :src="currentScanSrc"
        alt="扫描件"
        class="scan-image"
      />
    </div>
    <button class="scan-toggle" @click="toggleScan" :title="showScan ? '隐藏扫描件' : '显示扫描件'">
      {{ showScan ? '📖 纯文本' : '📄 对照' }}
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const showScan = ref(true)
const currentScanSrc = ref('')
const scanImg = ref(null)
let observer = null

function toggleScan() {
  showScan.value = !showScan.value
  localStorage.setItem('scan-view-mode', showScan.value ? 'scan' : 'text')
}

onMounted(() => {
  const saved = localStorage.getItem('scan-view-mode')
  if (saved === 'text') showScan.value = false

  // Find the VitePress content container
  const contentEl = document.querySelector('.VPContent')
  if (!contentEl) return

  // Observe PageDivider elements
  observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          const page = entry.target.getAttribute('data-page')
          if (page) {
            currentScanSrc.value = `/power-trading-docs/pages/page_${String(page).padStart(3, '0')}.png`
          }
        }
      }
    },
    {
      root: null,
      rootMargin: '-80px 0px -50% 0px',
      threshold: 0,
    }
  )

  // Observe all page dividers
  document.querySelectorAll('.page-divider').forEach((el) => {
    observer.observe(el)
  })

  // Set initial image from first divider
  const firstDivider = document.querySelector('.page-divider')
  if (firstDivider) {
    const page = firstDivider.getAttribute('data-page')
    if (page) {
      currentScanSrc.value = `/power-trading-docs/pages/page_${String(page).padStart(3, '0')}.png`
    }
  }
})

onUnmounted(() => {
  if (observer) observer.disconnect()
})
</script>

<style scoped>
.scan-viewer {
  position: fixed;
  top: var(--vp-nav-height);
  right: 0;
  bottom: 0;
  width: 45%;
  z-index: 10;
  display: flex;
  flex-direction: column;
}

.scan-viewer.scan-hidden {
  display: none;
}

.scan-panel {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  background: var(--vp-c-bg-alt);
  border-left: 1px solid var(--vp-c-divider);
}

.scan-image {
  width: 100%;
  height: auto;
  display: block;
}

.scan-toggle {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 20;
  background: var(--vp-c-brand-1);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: transform 0.2s;
}

.scan-toggle:hover {
  transform: scale(1.05);
}
</style>
```

- [ ] **Step 3: Create theme index.ts to register components**

Create `book-vitepress/.vitepress/theme/index.ts`:

```ts
import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import ScanViewer from './ScanViewer.vue'
import PageDivider from './PageDivider.vue'
import './styles/custom.css'

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('ScanViewer', ScanViewer)
    app.component('PageDivider', PageDivider)
  },
} satisfies Theme
```

- [ ] **Step 4: Test components render**

```bash
cd book-vitepress && npx vitepress dev --port 5173 &
sleep 5
curl -s http://localhost:5173/power-trading-docs/ch01/ | grep -c 'PageDivider'
kill %1
```

Expected: Components are registered (no Vue warnings in console).

- [ ] **Step 5: Commit**

```bash
cd /Users/ethan/workspace/power-trading
git add book-vitepress/.vitepress/theme/
git commit -m "feat: add ScanViewer and PageDivider Vue components"
```

---

### Task 5: Port Theme Styling

**Files:**
- Create: `book-vitepress/.vitepress/theme/styles/custom.css`

- [ ] **Step 1: Create custom CSS**

Create `book-vitepress/.vitepress/theme/styles/custom.css`:

```css
/* === Table styling (from OCR) === */
.table-container {
  overflow-x: auto;
  margin: 1.5rem 0;
}

.table-container table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.table-container td,
.table-container th {
  border: 1px solid var(--vp-c-divider);
  padding: 0.5rem 0.75rem;
  text-align: left;
  vertical-align: top;
}

.table-container tr:nth-child(even) {
  background: var(--vp-c-default-soft);
}

/* === Figure styling === */
figure,
.embedded-figure {
  margin: 1.5rem 0;
  text-align: center;
}

.embedded-figure img {
  max-width: 100%;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.embedded-figure figcaption {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: var(--vp-c-text-2);
  font-style: italic;
}

/* === Narrow content width for better readability === */
.VPDoc .content-container {
  max-width: 720px !important;
}

/* === Scan viewer: offset content when split view active === */
@media (min-width: 1280px) {
  body:not(.scan-hidden) .VPDoc .container {
    max-width: 55%;
  }
}
```

- [ ] **Step 2: Verify styles load**

```bash
cd book-vitepress && npx vitepress dev --port 5173 &
sleep 5
curl -s http://localhost:5173/power-trading-docs/ch01/ | grep -c 'table-container'
kill %1
```

- [ ] **Step 3: Commit**

```bash
cd /Users/ethan/workspace/power-trading
git add book-vitepress/.vitepress/theme/styles/custom.css
git commit -m "feat: add custom CSS for tables, figures, and scan viewer"
```

---

### Task 6: Local Integration Test

- [ ] **Step 1: Start dev server and verify end-to-end**

```bash
cd book-vitepress && npx vitepress dev --port 5173
```

Check all of the following:
- [ ] Landing page loads at `/power-trading-docs/` with hero section
- [ ] Sidebar shows seven collapsible groups (序篇, 第一篇...第五篇, 附录)
- [ ] Only 序篇 is expanded; others are collapsed
- [ ] Clicking a chapter link navigates to that chapter's content
- [ ] Chapter content shows OCR text with proper headings (##, ###, ####)
- [ ] `<PageDivider>` components render with page number badges
- [ ] Tables render with borders and alternating row colors
- [ ] Figure crops render as inline images
- [ ] Scan panel shows on right side with page scan PNG
- [ ] Scrolling updates the scan image (IntersectionObserver)
- [ ] Toggle button switches between text-only and split view
- [ ] VitePress built-in search works (Ctrl+K)
- [ ] VitePress outline (right sidebar) shows section headings
- [ ] Dark/light theme toggle works (VitePress built-in)

- [ ] **Step 2: Fix any issues found during testing**

If any component doesn't render, check:
- Console errors in browser DevTools
- Vue component registration in `theme/index.ts`
- Markdown frontmatter syntax
- Image path references (should start with `/power-trading-docs/`)

- [ ] **Step 3: Commit fixes**

```bash
git add -A
git commit -m "fix: address issues found during local integration testing"
```

---

### Task 7: GitHub Actions Deployment

**Files:**
- Create: `.github/workflows/deploy.yml`

- [ ] **Step 1: Create GitHub Actions workflow**

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy VitePress site to Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
          cache-dependency-path: book-vitepress/package-lock.json

      - name: Install dependencies
        run: npm ci
        working-directory: book-vitepress

      - name: Create symlink for page scans
        run: |
          mkdir -p book-vitepress/public
          ln -s ../book/pages book-vitepress/public/pages

      - name: Build
        run: npm run docs:build
        working-directory: book-vitepress

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: book-vitepress/.vitepress/dist

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Generate package-lock.json**

```bash
cd book-vitepress && npm install && cd ..
```

Verify `book-vitepress/package-lock.json` exists.

- [ ] **Step 3: Enable GitHub Pages in repo settings**

```bash
# Check current Pages settings
gh api repos/wyxpku/power-trading-docs/pages 2>/dev/null || echo "Pages not yet enabled"
```

If not enabled, the user must:
1. Go to repo Settings → Pages
2. Source: "GitHub Actions"
3. (No need to pick a branch — the workflow handles deployment)

- [ ] **Step 4: Commit workflow**

```bash
git add .github/workflows/deploy.yml book-vitepress/package-lock.json
git commit -m "feat: add GitHub Actions workflow for Pages deployment"
```

- [ ] **Step 5: Push and verify deployment**

```bash
git push docs main
```

Then monitor:
```bash
gh run list --repo wyxpku/power-trading-docs --limit 1
```

Wait for the workflow to complete, then visit `https://wyxpku.github.io/power-trading-docs/`.

Expected: Site deployed with all chapters accessible via sidebar.

---

## Self-Review

### 1. Spec Coverage

| Spec Requirement | Task |
|-----------------|------|
| VitePress project setup | Task 1 |
| Three-level collapsible sidebar (篇 > 章 > 节) | Task 2 |
| Accordion behavior (only active group expanded) | Task 2 (collapsed: true/false in config) |
| Content conversion OCR JSON → Markdown | Task 3 |
| ScanViewer component (split-view) | Task 4 |
| PageDivider component | Task 4 |
| Theme customization (tables, figures, CSS) | Task 5 |
| GitHub Pages deployment via Actions | Task 7 |
| Static assets (page scans via symlink) | Task 1, Task 7 |
| Local testing and verification | Task 6 |

### 2. Placeholder Scan

- No "TBD", "TODO", "implement later", "fill in details"
- No "add appropriate error handling" / "add validation"
- All code blocks contain complete implementations
- No "similar to Task N" references

### 3. Type Consistency

- `PageDivider` prop: `pdfPage: number` (used as `pdf-page` in Markdown)
- `ScanViewer` references `data-page` attribute (set by `PageDivider`)
- Sidebar links: `/ch01/` through `/ch31/`, `/preface`, `/appendix-a`, `/appendix-b` — matches file structure
- Base path: `/power-trading-docs/` used consistently in config, image URLs, and scan viewer
