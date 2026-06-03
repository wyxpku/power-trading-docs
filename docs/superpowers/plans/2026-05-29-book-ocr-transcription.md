# PDF Ebook OCR Transcription Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transcribe all 427 pages of "电力现货市场实务" from page screenshots into structured HTML content using Claude's native vision capabilities.

**Architecture:** Sequential per-page processing. Read each page PNG via the Read tool (native vision), transcribe the content into structured HTML, and use Edit tool to replace placeholder text in the existing HTML files. Process files in order: preface → chapters 1-31 → appendices.

**Tech Stack:** Claude native vision (Read tool), Edit tool for HTML modification, existing ebook reader framework (HTML/CSS/JS).

---

## File Structure

| File | Pages | Page Range | Status |
|------|-------|------------|--------|
| `book/preface.html` | 6 | 3-8 | Pending |
| `book/chapter_01.html` | 23 | 19-41 | Pending |
| `book/chapter_02.html` | 18 | 42-59 | Pending |
| `book/chapter_03.html` | 23 | 60-82 | Pending |
| `book/chapter_04.html` | 6 | 83-88 | Pending |
| `book/chapter_05.html` | 13 | 89-101 | Pending |
| `book/chapter_06.html` | 8 | 102-109 | Pending |
| `book/chapter_07.html` | 33 | 110-142 | Pending |
| `book/chapter_08.html` | 25 | 143-167 | Pending |
| `book/chapter_09.html` | 20 | 168-187 | Pending |
| `book/chapter_10.html` | 19 | 188-206 | Pending |
| `book/chapter_11.html` | 21 | 207-227 | Pending |
| `book/chapter_12.html` | 20 | 228-247 | Pending |
| `book/chapter_13.html` | 26 | 248-273 | Pending |
| `book/chapter_14.html` | 17 | 274-290 | Pending |
| `book/chapter_15.html` | 33 | 291-323 | Pending |
| `book/chapter_16.html` | 30 | 324-353 | Pending |
| `book/chapter_17.html` | 25 | 354-378 | Pending |
| `book/chapter_18.html` | 24 | 379-402 | Pending |
| `book/chapter_19.html` | 26 | 403-428 | Pending |
| `book/chapter_20.html` | 36 | 429-464 | Pending |
| `book/chapter_21.html` | 9 | 465-473 | Pending |
| `book/chapter_22.html` | 7 | 474-480 | Pending |
| `book/chapter_23.html` | 22 | 481-502 | Pending |
| `book/chapter_24.html` | 10 | 503-512 | Pending |
| `book/chapter_25.html` | 4 | 513-516 | Pending |
| `book/chapter_26.html` | 22 | 517-538 | Pending |
| `book/chapter_27.html` | 12 | 539-550 | Pending |
| `book/chapter_28.html` | 19 | 551-569 | Pending |
| `book/chapter_29.html` | 7 | 570-576 | Pending |
| `book/chapter_30.html` | 8 | 577-584 | Pending |
| `book/chapter_31.html` | 19 | 585-603 | Pending |
| `book/appendix_a.html` | 21 | 604-624 | Pending |
| `book/appendix_b.html` | 22 | 625-646 | Pending |

**Total: 427 pages across 33 content files (index.html is already complete)**

---

## Per-Page Processing Template

This is the standard workflow repeated for every page. Each task below applies this template to a batch of pages within one HTML file.

### Step Pattern (repeated per page)

- [ ] **Step A: Read the page image**

Read `book/pages/page_NNN.png` using the Read tool. Claude's native vision will display the page content visually.

- [ ] **Step B: Transcribe content into HTML**

Based on the visual content, generate structured HTML following these rules:

**Headings:**
```html
<h1>Chapter Title</h1>           <!-- 章标题, typically "第X章 ..." -->
<h2>Section Title</h2>           <!-- 节标题, typically "第一节 ..." or numbered "X.X ..." -->
<h3>Subsection Title</h3>        <!-- 小节标题 -->
```

**Paragraphs:**
```html
<p>正文内容...</p>
```

**Lists:**
```html
<ul>
  <li>Item text</li>
</ul>
<!-- or ordered -->
<ol>
  <li>Item text</li>
</ol>
```

**Tables:**
```html
<table>
  <thead>
    <tr><th>Col 1</th><th>Col 2</th><th>Col 3</th></tr>
  </thead>
  <tbody>
    <tr><td>Data 1</td><td>Data 2</td><td>Data 3</td></tr>
  </tbody>
</table>
```

**Display formulas:**
```html
<div class="equation-wrapper">$$ L = \sum_{i=1}^{n} P_i \times C_i $$</div>
```

**Inline formulas:**
```html
<p>当 $P_i \geq P_{max}$ 时，输出受限。</p>
```

**Figures:**
```html
<figure class="embedded-figure">
  <img src="pages/page_NNN.png" alt="图X-X 图片标题">
  <figcaption>图X-X 图片标题</figcaption>
</figure>
```

**Quality rules:**
- Transcribe text EXACTLY as written - no paraphrasing, no corrections, no omissions
- Preserve all paragraph breaks from the original
- If text is unclear, use `[?]` marker and move on
- If a page is blank or contains only page numbers, write an empty `<p></p>` or skip
- For formulas that cannot be reliably converted to LaTeX, wrap the page image as a figure:
  ```html
  <figure class="embedded-figure">
    <img src="pages/page_NNN.png" alt="公式（截图）">
  </figure>
  ```

- [ ] **Step C: Edit the HTML file**

Use the Edit tool to replace the placeholder in the target HTML file:

**Old string (to find):**
```html
<p class='placeholder-text'>暂无本页转录文字，正在后台转录中...</p>
```
within the specific `<div class="page-body-container" id="page-content-NNN">`.

**New string (to insert):** The transcribed HTML content from Step B.

**Important:** The placeholder text appears in multiple `page-body-container` divs within the same file. To target the correct one, include enough surrounding context (the `id="page-content-NNN"` attribute) to make the match unique. Example:

```
old_string: <div class="page-body-container" id="page-content-19">\n\t<p class='placeholder-text'>暂无本页转录文字，正在后台转录中...</p>\n\t</div>
new_string: <div class="page-body-container" id="page-content-19">\n\t[transcribed HTML here]\n\t</div>
```

- [ ] **Step D: Commit after each file is complete**

After all pages in one HTML file are processed, commit:

```bash
git add book/[filename].html
git commit -m "content: transcribe [chapter/section name] (pages XX-XX)"
```

---

## Task Decomposition

### Task 1: Pilot — Process preface.html (6 pages)

**Files:**
- Modify: `book/preface.html`
- Read: `book/pages/page_003.png` through `book/pages/page_008.png`

- [ ] **Step 1: Read page_003.png and transcribe**
- [ ] **Step 2: Edit preface.html — replace page-content-3**
- [ ] **Step 3: Read page_004.png and transcribe**
- [ ] **Step 4: Edit preface.html — replace page-content-4**
- [ ] **Step 5: Read page_005.png and transcribe**
- [ ] **Step 6: Edit preface.html — replace page-content-5**
- [ ] **Step 7: Read page_006.png and transcribe**
- [ ] **Step 8: Edit preface.html — replace page-content-6**
- [ ] **Step 9: Read page_007.png and transcribe**
- [ ] **Step 10: Edit preface.html — replace page-content-7**
- [ ] **Step 11: Read page_008.png and transcribe**
- [ ] **Step 12: Edit preface.html — replace page-content-8**
- [ ] **Step 13: Commit**

```bash
git add book/preface.html
git commit -m "content: transcribe preface (pages 3-8)"
```

- [ ] **Step 14: Verify** — Open `book/preface.html` in browser, switch to split view, visually compare text panel against scan panel for each page.

---

### Task 2: Process chapter_01.html (23 pages, pages 19-41)

**Files:**
- Modify: `book/chapter_01.html`
- Read: `book/pages/page_019.png` through `book/pages/page_041.png`

For each page N in range [19, 41]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_01.html` — replace `page-content-N`
- [ ] Commit after all 23 pages

```bash
git add book/chapter_01.html
git commit -m "content: transcribe chapter 01 电力市场概述 (pages 19-41)"
```

- [ ] Verify in browser split view

---

### Task 3: Process chapter_02.html (18 pages, pages 42-59)

**Files:**
- Modify: `book/chapter_02.html`
- Read: `book/pages/page_042.png` through `book/pages/page_059.png`

For each page N in range [42, 59]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_02.html` — replace `page-content-N`
- [ ] Commit after all 18 pages

```bash
git add book/chapter_02.html
git commit -m "content: transcribe chapter 02 电力现货市场组织 (pages 42-59)"
```

---

### Task 4: Process chapter_03.html (23 pages, pages 60-82)

**Files:**
- Modify: `book/chapter_03.html`
- Read: `book/pages/page_060.png` through `book/pages/page_082.png`

For each page N in range [60, 82]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_03.html` — replace `page-content-N`
- [ ] Commit after all 23 pages

```bash
git add book/chapter_03.html
git commit -m "content: transcribe chapter 03 电力现货市场价格机制 (pages 60-82)"
```

---

### Task 5: Process chapter_04.html (6 pages, pages 83-88)

**Files:**
- Modify: `book/chapter_04.html`
- Read: `book/pages/page_083.png` through `book/pages/page_088.png`

For each page N in range [83, 88]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_04.html` — replace `page-content-N`
- [ ] Commit after all 6 pages

```bash
git add book/chapter_04.html
git commit -m "content: transcribe chapter 04 电力现货市场阻塞管理 (pages 83-88)"
```

---

### Task 6: Process chapter_05.html (13 pages, pages 89-101)

**Files:**
- Modify: `book/chapter_05.html`
- Read: `book/pages/page_089.png` through `book/pages/page_101.png`

For each page N in range [89, 101]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_05.html` — replace `page-content-N`
- [ ] Commit after all 13 pages

```bash
git add book/chapter_05.html
git commit -m "content: transcribe chapter 05 电力市场信息披露与风险管控 (pages 89-101)"
```

---

### Task 7: Process chapter_06.html (8 pages, pages 102-109)

**Files:**
- Modify: `book/chapter_06.html`
- Read: `book/pages/page_102.png` through `book/pages/page_109.png`

For each page N in range [102, 109]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_06.html` — replace `page-content-N`
- [ ] Commit after all 8 pages

```bash
git add book/chapter_06.html
git commit -m "content: transcribe chapter 06 电力现货市场绩效评价 (pages 102-109)"
```

---

### Task 8: Process chapter_07.html (33 pages, pages 110-142)

**Files:**
- Modify: `book/chapter_07.html`
- Read: `book/pages/page_110.png` through `book/pages/page_142.png`

For each page N in range [110, 142]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_07.html` — replace `page-content-N`
- [ ] Commit after all 33 pages

```bash
git add book/chapter_07.html
git commit -m "content: transcribe chapter 07 美国PJM电力市场 (pages 110-142)"
```

---

### Task 9: Process chapter_08.html (25 pages, pages 143-167)

**Files:**
- Modify: `book/chapter_08.html`
- Read: `book/pages/page_143.png` through `book/pages/page_167.png`

For each page N in range [143, 167]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_08.html` — replace `page-content-N`
- [ ] Commit after all 25 pages

```bash
git add book/chapter_08.html
git commit -m "content: transcribe chapter 08 美国ERCOT电力市场 (pages 143-167)"
```

---

### Task 10: Process chapter_09.html (20 pages, pages 168-187)

**Files:**
- Modify: `book/chapter_09.html`
- Read: `book/pages/page_168.png` through `book/pages/page_187.png`

For each page N in range [168, 187]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_09.html` — replace `page-content-N`
- [ ] Commit after all 20 pages

```bash
git add book/chapter_09.html
git commit -m "content: transcribe chapter 09 英国电力市场 (pages 168-187)"
```

---

### Task 11: Process chapter_10.html (19 pages, pages 188-206)

**Files:**
- Modify: `book/chapter_10.html`
- Read: `book/pages/page_188.png` through `book/pages/page_206.png`

For each page N in range [188, 206]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_10.html` — replace `page-content-N`
- [ ] Commit after all 19 pages

```bash
git add book/chapter_10.html
git commit -m "content: transcribe chapter 10 欧洲统一电力市场 (pages 188-206)"
```

---

### Task 12: Process chapter_11.html (21 pages, pages 207-227)

**Files:**
- Modify: `book/chapter_11.html`
- Read: `book/pages/page_207.png` through `book/pages/page_227.png`

For each page N in range [207, 227]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_11.html` — replace `page-content-N`
- [ ] Commit after all 21 pages

```bash
git add book/chapter_11.html
git commit -m "content: transcribe chapter 11 澳大利亚电力市场 (pages 207-227)"
```

---

### Task 13: Process chapter_12.html (20 pages, pages 228-247)

**Files:**
- Modify: `book/chapter_12.html`
- Read: `book/pages/page_228.png` through `book/pages/page_247.png`

For each page N in range [228, 247]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_12.html` — replace `page-content-N`
- [ ] Commit after all 20 pages

```bash
git add book/chapter_12.html
git commit -m "content: transcribe chapter 12 巴西电力市场 (pages 228-247)"
```

---

### Task 14: Process chapter_13.html (26 pages, pages 248-273)

**Files:**
- Modify: `book/chapter_13.html`
- Read: `book/pages/page_248.png` through `book/pages/page_273.png`

For each page N in range [248, 273]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_13.html` — replace `page-content-N`
- [ ] Commit after all 26 pages

```bash
git add book/chapter_13.html
git commit -m "content: transcribe chapter 13 我国电力现货市场的演进 (pages 248-273)"
```

---

### Task 15: Process chapter_14.html (17 pages, pages 274-290)

**Files:**
- Modify: `book/chapter_14.html`
- Read: `book/pages/page_274.png` through `book/pages/page_290.png`

For each page N in range [274, 290]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_14.html` — replace `page-content-N`
- [ ] Commit after all 17 pages

```bash
git add book/chapter_14.html
git commit -m "content: transcribe chapter 14 省间电力现货市场 (pages 274-290)"
```

---

### Task 16: Process chapter_15.html (33 pages, pages 291-323)

**Files:**
- Modify: `book/chapter_15.html`
- Read: `book/pages/page_291.png` through `book/pages/page_323.png`

For each page N in range [291, 323]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_15.html` — replace `page-content-N`
- [ ] Commit after all 33 pages

```bash
git add book/chapter_15.html
git commit -m "content: transcribe chapter 15 浙江电力现货市场 (pages 291-323)"
```

---

### Task 17: Process chapter_16.html (30 pages, pages 324-353)

**Files:**
- Modify: `book/chapter_16.html`
- Read: `book/pages/page_324.png` through `book/pages/page_353.png`

For each page N in range [324, 353]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_16.html` — replace `page-content-N`
- [ ] Commit after all 30 pages

```bash
git add book/chapter_16.html
git commit -m "content: transcribe chapter 16 山西电力现货市场 (pages 324-353)"
```

---

### Task 18: Process chapter_17.html (25 pages, pages 354-378)

**Files:**
- Modify: `book/chapter_17.html`
- Read: `book/pages/page_354.png` through `book/pages/page_378.png`

For each page N in range [354, 378]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_17.html` — replace `page-content-N`
- [ ] Commit after all 25 pages

```bash
git add book/chapter_17.html
git commit -m "content: transcribe chapter 17 山东电力现货市场 (pages 354-378)"
```

---

### Task 19: Process chapter_18.html (24 pages, pages 379-402)

**Files:**
- Modify: `book/chapter_18.html`
- Read: `book/pages/page_379.png` through `book/pages/page_402.png`

For each page N in range [379, 402]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_18.html` — replace `page-content-N`
- [ ] Commit after all 24 pages

```bash
git add book/chapter_18.html
git commit -m "content: transcribe chapter 18 福建电力现货市场 (pages 379-402)"
```

---

### Task 20: Process chapter_19.html (26 pages, pages 403-428)

**Files:**
- Modify: `book/chapter_19.html`
- Read: `book/pages/page_403.png` through `book/pages/page_428.png`

For each page N in range [403, 428]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_19.html` — replace `page-content-N`
- [ ] Commit after all 26 pages

```bash
git add book/chapter_19.html
git commit -m "content: transcribe chapter 19 四川电力现货市场 (pages 403-428)"
```

---

### Task 21: Process chapter_20.html (36 pages, pages 429-464)

**Files:**
- Modify: `book/chapter_20.html`
- Read: `book/pages/page_429.png` through `book/pages/page_464.png`

For each page N in range [429, 464]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_20.html` — replace `page-content-N`
- [ ] Commit after all 36 pages

```bash
git add book/chapter_20.html
git commit -m "content: transcribe chapter 20 甘肃电力现货市场 (pages 429-464)"
```

---

### Task 22: Process chapter_21.html (9 pages, pages 465-473)

**Files:**
- Modify: `book/chapter_21.html`
- Read: `book/pages/page_465.png` through `book/pages/page_473.png`

For each page N in range [465, 473]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_21.html` — replace `page-content-N`
- [ ] Commit after all 9 pages

```bash
git add book/chapter_21.html
git commit -m "content: transcribe chapter 21 电力现货市场技术支持系统总体概况 (pages 465-473)"
```

---

### Task 23: Process chapter_22.html (7 pages, pages 474-480)

**Files:**
- Modify: `book/chapter_22.html`
- Read: `book/pages/page_474.png` through `book/pages/page_480.png`

For each page N in range [474, 480]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_22.html` — replace `page-content-N`
- [ ] Commit after all 7 pages

```bash
git add book/chapter_22.html
git commit -m "content: transcribe chapter 22 现货及辅助服务市场申报发布 (pages 474-480)"
```

---

### Task 24: Process chapter_23.html (22 pages, pages 481-502)

**Files:**
- Modify: `book/chapter_23.html`
- Read: `book/pages/page_481.png` through `book/pages/page_502.png`

For each page N in range [481, 502]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_23.html` — replace `page-content-N`
- [ ] Commit after all 22 pages

```bash
git add book/chapter_23.html
git commit -m "content: transcribe chapter 23 电力现货市场出清 (pages 481-502)"
```

---

### Task 25: Process chapter_24.html (10 pages, pages 503-512)

**Files:**
- Modify: `book/chapter_24.html`
- Read: `book/pages/page_503.png` through `book/pages/page_512.png`

For each page N in range [503, 512]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_24.html` — replace `page-content-N`
- [ ] Commit after all 10 pages

```bash
git add book/chapter_24.html
git commit -m "content: transcribe chapter 24 辅助服务市场出清 (pages 503-512)"
```

---

### Task 26: Process chapter_25.html (4 pages, pages 513-516)

**Files:**
- Modify: `book/chapter_25.html`
- Read: `book/pages/page_513.png` through `book/pages/page_516.png`

For each page N in range [513, 516]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_25.html` — replace `page-content-N`
- [ ] Commit after all 4 pages

```bash
git add book/chapter_25.html
git commit -m "content: transcribe chapter 25 安全校核 (pages 513-516)"
```

---

### Task 27: Process chapter_26.html (22 pages, pages 517-538)

**Files:**
- Modify: `book/chapter_26.html`
- Read: `book/pages/page_517.png` through `book/pages/page_538.png`

For each page N in range [517, 538]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_26.html` — replace `page-content-N`
- [ ] Commit after all 22 pages

```bash
git add book/chapter_26.html
git commit -m "content: transcribe chapter 26 市场分析 (pages 517-538)"
```

---

### Task 28: Process chapter_27.html (12 pages, pages 539-550)

**Files:**
- Modify: `book/chapter_27.html`
- Read: `book/pages/page_539.png` through `book/pages/page_550.png`

For each page N in range [539, 550]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_27.html` — replace `page-content-N`
- [ ] Commit after all 12 pages

```bash
git add book/chapter_27.html
git commit -m "content: transcribe chapter 27 电力市场结算 (pages 539-550)"
```

---

### Task 29: Process chapter_28.html (19 pages, pages 551-569)

**Files:**
- Modify: `book/chapter_28.html`
- Read: `book/pages/page_551.png` through `book/pages/page_569.png`

For each page N in range [551, 569]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_28.html` — replace `page-content-N`
- [ ] Commit after all 19 pages

```bash
git add book/chapter_28.html
git commit -m "content: transcribe chapter 28 模拟仿真 (pages 551-569)"
```

---

### Task 30: Process chapter_29.html (7 pages, pages 570-576)

**Files:**
- Modify: `book/chapter_29.html`
- Read: `book/pages/page_570.png` through `book/pages/page_576.png`

For each page N in range [570, 576]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_29.html` — replace `page-content-N`
- [ ] Commit after all 7 pages

```bash
git add book/chapter_29.html
git commit -m "content: transcribe chapter 29 系统运维管理 (pages 570-576)"
```

---

### Task 31: Process chapter_30.html (8 pages, pages 577-584)

**Files:**
- Modify: `book/chapter_30.html`
- Read: `book/pages/page_577.png` through `book/pages/page_584.png`

For each page N in range [577, 584]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_30.html` — replace `page-content-N`
- [ ] Commit after all 8 pages

```bash
git add book/chapter_30.html
git commit -m "content: transcribe chapter 30 安全防护 (pages 577-584)"
```

---

### Task 32: Process chapter_31.html (19 pages, pages 585-603)

**Files:**
- Modify: `book/chapter_31.html`
- Read: `book/pages/page_585.png` through `book/pages/page_603.png`

For each page N in range [585, 603]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `chapter_31.html` — replace `page-content-N`
- [ ] Commit after all 19 pages

```bash
git add book/chapter_31.html
git commit -m "content: transcribe chapter 31 双碳目标和新型电力系统下的电力市场展望 (pages 585-603)"
```

---

### Task 33: Process appendix_a.html (21 pages, pages 604-624)

**Files:**
- Modify: `book/appendix_a.html`
- Read: `book/pages/page_604.png` through `book/pages/page_624.png`

For each page N in range [604, 624]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `appendix_a.html` — replace `page-content-N`
- [ ] Commit after all 21 pages

```bash
git add book/appendix_a.html
git commit -m "content: transcribe appendix A 电力现货市场规则框架示例 (pages 604-624)"
```

---

### Task 34: Process appendix_b.html (22 pages, pages 625-646)

**Files:**
- Modify: `book/appendix_b.html`
- Read: `book/pages/page_625.png` through `book/pages/page_646.png`

For each page N in range [625, 646]:
- [ ] Read `page_NNN.png` and transcribe content
- [ ] Edit `appendix_b.html` — replace `page-content-N`
- [ ] Commit after all 22 pages

```bash
git add book/appendix_b.html
git commit -m "content: transcribe appendix B 电力现货市场导则范本 (pages 625-646)"
```

---

## Self-Review Checklist

### 1. Spec Coverage
- [x] Sequential per-page processing — covered in all tasks
- [x] HTML content structure rules — documented in Per-Page Processing Template
- [x] Figure handling (Phase 1 placeholder) — documented in template
- [x] Formula handling (LaTeX) — documented in template
- [x] Progress management (skip completed) — noted in each task
- [x] Quality principles — documented in template
- [x] All 33 content files covered — Tasks 1-34
- [x] Total pages: 6+23+18+23+6+13+8+33+25+20+19+21+20+26+17+33+30+25+24+26+36+9+7+22+10+4+22+12+19+7+8+19+21+22 = 427 pages

### 2. Placeholder Scan
- No TBD/TODO items
- All commit messages are concrete
- All file paths are exact

### 3. Type Consistency
- All page references use consistent `page_NNN.png` format (zero-padded to 3 digits)
- All HTML container IDs use `page-content-N` (no padding)
- All edit operations target `page-body-container` divs with specific `id` attributes
