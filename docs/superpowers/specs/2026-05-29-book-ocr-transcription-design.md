# PDF Ebook OCR Transcription Design

## Overview

Convert the book "电力现货市场实务" (Electric Power Spot Market Practice) from page screenshots to structured HTML content, using vision MCP tools for OCR.

## Current State

- 34 HTML files with full ebook reader framework (sidebar, themes, split view)
- 427 page screenshots in `book/pages/` (page_001.png - page_427.png)
- All `page-body-container` divs contain placeholder text
- Page mapping is correct (data-page attributes match PNG filenames)

## Approach: Sequential Per-Page Processing

For each HTML file, for each `page-body-container`:
1. Read the corresponding page_NNN.png screenshot
2. Call vision MCP (`extract_text_from_screenshot`) to identify content
3. Generate structured HTML from the OCR result
4. Replace the placeholder `<p class='placeholder-text'>` with actual content

Processing order: preface.html → chapter_01.html → ... → chapter_31.html → appendix_a.html → appendix_b.html

## HTML Content Structure Rules

Content goes inside `<div class="page-body-container">`:

| Element | HTML Tag | Notes |
|---------|----------|-------|
| Paragraphs | `<p>` | Keep paragraph indentation |
| Chapter titles | `<h1>` | Chapter-level heading |
| Section titles | `<h2>` | Section-level heading |
| Subsection titles | `<h3>` | Subsection-level heading |
| Lists | `<ul>/<ol>` + `<li>` | Ordered or unordered |
| Tables | `<table>` + `<thead>/<tbody>` | Full table structure |
| Formulas | `$$...$$` LaTeX | LaTeX notation for KaTeX rendering |
| Figures | `<figure class="embedded-figure">` | With `<img>` and `<figcaption>` |

## Figure Handling Strategy

**Phase 1 (this task):** Text transcription. When encountering a figure:
- Insert `<figure class="embedded-figure">` with a placeholder `<img>` pointing to the original page image
- Add `<figcaption>` with the figure title from the original text
- The figure's `src` will reference the full page image temporarily

**Phase 2 (future):** Crop individual figures from page screenshots and replace placeholders.

## Formula Handling

- Mathematical formulas are converted to LaTeX notation (`$$...$$` for display, `$...$` for inline)
- The CSS already has `.equation-wrapper` styling
- Formulas wrapped in: `<div class="equation-wrapper">$$ ... $$</div>`
- If OCR cannot reliably identify a formula, use the page screenshot as a fallback image

## Progress Management

- Skip pages where placeholder text has already been replaced
- Process files in order: preface → chapters → appendices
- Each page is an independent unit - failure on one page doesn't block others

## Quality Principles

1. **Accuracy over speed**: Strict adherence to original content, no guessing or embellishing
2. **Structural fidelity**: Preserve heading hierarchy, paragraph breaks, list structures from original
3. **Table precision**: Row-by-row transcription, correct column alignment
4. **Formula care**: Convert to LaTeX where clear, use image fallback where ambiguous

## Scope

- 427 pages across 34 HTML files
- Approximately 600+ pages of technical content including:
  - Text-heavy theoretical chapters (Part 1: Theory)
  - International market case studies (Part 2: International Practice)
  - Domestic market implementations (Part 3: Domestic Practice)
  - Technical system descriptions (Part 4: Technical Support Systems)
  - Future outlook (Part 5: Outlook)
  - Appendices with regulatory frameworks

## File Structure

```
book/
├── css/style.css          # Styling (complete)
├── pages/page_001-427.png # Page screenshots (complete)
├── index.html             # Cover page (complete)
├── preface.html           # Pages 3-8
├── chapter_01.html        # Pages 19-41
├── chapter_02.html        # Pages 42-...
├── ...                    # More chapters
├── chapter_31.html        # Pages ...
├── appendix_a.html        # Pages 604-624
└── appendix_b.html        # Pages 625-...
```
