# OCR Markdown 格式梳理 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 清理 `site/` 下 34 个 OCR markdown 文件中由 PDF 分页和 OCR 引入的格式与排版问题（A/B/C 三类），由大模型基于语义判断修改，不使用脚本/正则。

**Architecture:** 两阶段推进 — 先试点 3 个文件（覆盖 A/B/C 三类问题）定规则，验收后按相同语义判断方式处理剩余 31 个文件。每文件单独 commit，进度可追溯。

**Tech Stack:** Markdown + VitePress + Vue 组件（`PageDivider.vue`、`ScanViewer.vue`）。验证手段：`Read`/`Edit` 工具 + `npm run docs:dev` 本地预览 + git diff 人工 review。

**Spec:** `docs/superpowers/specs/2026-06-17-ocr-markdown-cleanup-design.md`

---

## File Structure

### 直接修改（共 34 个 markdown）

| 范围 | 文件 | 主要问题 |
|---|---|---|
| 试点 | `site/ch01/index.md` | A + B |
| 试点 | `site/ch13/index.md` | A + C（26 处 table） |
| 试点 | `site/appendix-a.md` | A + B（B 类重灾区，777 行） |
| 全量 | `site/ch02/index.md` ~ `site/ch12/index.md`（11 个）| 混合 |
| 全量 | `site/ch14/index.md` ~ `site/ch20/index.md`（7 个）| 混合（部分表格密集） |
| 全量 | `site/ch21/index.md` ~ `site/ch31/index.md`（11 个）| 混合 |
| 全量 | `site/appendix-b.md`、`site/index.md` | 混合 |

### 条件性修改

- `site/.vitepress/theme/PageDivider.vue`：仅当试点 Task 4 验证 `<div>` 内联渲染异常时，改为 `<span>`

### 新增（规则备忘录）

- `docs/superpowers/specs/2026-06-17-ocr-markdown-cleanup-design.md` 末尾追加 "规则备忘录" 章节

---

## 标准文件处理流程（SOP）

**每个文件都严格走以下 6 步，不得跳过任何一步。**

- [ ] **SOP-S1: 通读** — 用 `Read` 工具完整读取整个文件（不要只读片段），建立上下文。若文件超过 2000 行，分段读完后再继续。

- [ ] **SOP-S2: 诊断** — 在文件外的回复消息里列出候选清单，每条包含：
  - 行号
  - 问题类别（A/B/C）
  - 当前文本片段（不超过 2 行）
  - 拟改方案（合并/降级标题层级/`<br>` 替换等）
  - 不确定的标注 `[需确认]`

- [ ] **SOP-S3: 用户确认** — 等待用户对清单确认或调整后再动手。**绝不擅自修改。**

- [ ] **SOP-S4: 逐项 Edit** — 每个候选项用一个独立的 `Edit` 工具调用。若一个文件改动超过 15 处，分批 Edit（每批 5-8 处），每批之间用 `Read` 复核一次。

- [ ] **SOP-S5: 自检** — 改完用 `Read` 重读整个文件，确认：
  - frontmatter 完好
  - 所有 `![...](/pages/crops/...)` 路径未变
  - 所有 `<PageDivider pdf-page="N" />` 的 N 值未变
  - 表格 `<table>...</table>` 结构未破坏（标签配对）
  - 内联放法的 PageDivider 周围已无空行
  - 块级放法的 PageDivider 周围仍有空行

- [ ] **SOP-S6: 提交** —
  ```bash
  git add site/<file>
  git commit -m "docs: cleanup OCR formatting in site/<file>"
  ```
  提交信息中的路径与实际文件路径一致。

**三类问题判定要点（语义驱动，非正则）**：

- **A 类**：PageDivider 前后两段若属同一自然段（前段结尾非完整句号、话题紧密延续）→ **内联放法**（去掉周围空行，让两段合并为一个 `<p>`）；否则维持块级。
- **B 类**：编号子项 `## N. xxx` 若父节层级更深 → 降到对应层级；若实质是列表项而非独立小节 → 降为 `**N. xxx**` 加粗段落；拿不准标 `[需确认]`。
- **C 类**：`<td>` 内字面 `\n` → `<br>`；若是空格误识别为 `\n` → 直接删除；若单元格需要更复杂结构 → 标 `[需确认]`。

**内容修改红线**：不擅自动原文文字。OCR 错字、标点全半角不一致、数字单位疑似错误 → 列入"内容修改清单"，全部改完后单独问用户。

---

## Task 1: Pilot — `site/ch01/index.md`（A + B 类）

**Files:**
- Modify: `site/ch01/index.md`（400 行）

- [ ] **Step 1: 通读** — `Read` 整个 `site/ch01/index.md`。

- [ ] **Step 2: 诊断** — 列出候选清单。**已知样本**（参考 spec §3.1、§3.2）：
  - L27-30：跨页段落（"…不涉及电力" / PageDivider / "实物商品的交割…"）→ A 类，内联合并
  - L46-49：跨页段落（"…市场电能量" / divider / "供应充裕性的机制"）→ A 类
  - L65-68：跨页段落（"…市场交" / divider / "易者抵消输电阻塞成本…"）→ A 类
  - L95-98：跨页段落（"…交易合" / divider / "同管理范畴"）→ A 类
  - 其他 A 类候选（约 19 处 PageDivider，逐处判断）
  - B 类：通读后识别是否有 `## N. xxx` 出现在更深的父节之下

- [ ] **Step 3: 用户确认** — 把完整清单贴给用户，等待确认/调整。

- [ ] **Step 4: 逐项 Edit** — 按确认后的清单改。示例 Edit（L27-30 合并）：
  - `old_string`：
    ```
    …电能量金融市场合同通常不涉及电力

    <PageDivider pdf-page="21" />

    实物商品的交割…
    ```
  - `new_string`：
    ```
    …电能量金融市场合同通常不涉及电力
    <PageDivider pdf-page="21" />
    实物商品的交割…
    ```
  - 注意：`old_string`/`new_string` 用完整上下文片段以保证唯一。

- [ ] **Step 5: 自检** — `Read` 重读全文，按 SOP-S5 清单逐项核验。

- [ ] **Step 6: 本地预览** —
  ```bash
  cd site && npm run docs:dev
  ```
  在浏览器打开 ch01 页面，重点验证：
  - 内联合并的段落渲染为连续文本（无视觉断行）
  - 右侧 ScanViewer 滚动时扫描图仍按 pdf-page 切换
  - 若内联处渲染异常（如出现多余空白、段落被截断）→ 记录现象，触发 Task 4 的 PageDivider.vue 调整
  - 预览结束后 `Ctrl+C` 停掉 dev server

- [ ] **Step 7: 提交** —
  ```bash
  git add site/ch01/index.md
  git commit -m "docs: cleanup OCR formatting in site/ch01/index.md"
  ```

---

## Task 2: Pilot — `site/ch13/index.md`（A + C 类）

**Files:**
- Modify: `site/ch13/index.md`（约 330 行，含 26 处 table 标签）

- [ ] **Step 1: 通读** — `Read` 整个文件。

- [ ] **Step 2: 诊断** — 列出候选清单，**重点关注 C 类**：
  - L14：表格 `<td>` 内含字面 `\n`（如 "(1) 接入 500kV 电网…\n(2) 部分 30 万 kW…"）→ 改 `<br>`
  - L131、L140、…（26 处 `<div class="table-container">` 中的 table）逐处检查 `<td>` 内是否有 `\n`
  - A 类：ch13 的 PageDivider 逐处判断
  - B 类：ch13 是否有 `## N. xxx` 错位标题

- [ ] **Step 3: 用户确认** — 贴清单等待确认。

- [ ] **Step 4: 逐项 Edit** — 示例（L14 表格 `\n` → `<br>`）：
  - `old_string`：
    ```
    <td>(1) 接入 500kV 电网的常规火电机组。\n(2) 部分 30 万 kW 常规火电机组</td>
    ```
  - `new_string`：
    ```
    <td>(1) 接入 500kV 电网的常规火电机组。<br>(2) 部分 30 万 kW 常规火电机组</td>
    ```
  - 注意：HTML 表格行很长，`old_string` 要包含足够上下文以保证唯一（如整段 `<tr>...</tr>`）。

- [ ] **Step 5: 自检** — `Read` 重读，重点核验所有 `<table>` 的 `<tr>`/`<td>` 标签仍然配对、`<div class="table-container">` 闭合正常。

- [ ] **Step 6: 本地预览** — `cd site && npm run docs:dev`，打开 ch13 页面：
  - 表格内多行内容现在正确换行
  - 段落合并未破坏排版
  - ScanViewer 滚动同步正常

- [ ] **Step 7: 提交** —
  ```bash
  git add site/ch13/index.md
  git commit -m "docs: cleanup OCR formatting in site/ch13/index.md"
  ```

---

## Task 3: Pilot — `site/appendix-a.md`（A + B 类，B 类重灾区）

**Files:**
- Modify: `site/appendix-a.md`（777 行）

- [ ] **Step 1: 通读** — `Read` 整个文件。

- [ ] **Step 2: 诊断** — 重点 B 类。**已知样本**：
  - L10：`## 1. 市场模式` 嵌在 `## A.2.1.2 市场概述`（H2）下 → 改 `### 1. 市场模式`
  - L14：`## 2. 价格机制` → `### 2. 价格机制`
  - L18、L22：`## 3.`、`## 4.` → `### 3.`、`### 4.`
  - L30、L34：`## 1. 市场准入与退出`、`## 2. 市场注册与注销`（在 `## A.2.1.3` 下）→ `###`
  - 类似模式贯穿全文，逐处判断
  - A 类：appendix-a 的 PageDivider 逐处判断
  - C 类：appendix-a 是否有表格（grep 显示无 `<table>`，但通读时仍需留意）

- [ ] **Step 3: 用户确认** — 贴清单等待确认。B 类降级若遇到拿不准是"小节"还是"列表项"的，标 `[需确认]`。

- [ ] **Step 4: 逐项 Edit** — 注意此文件改动较多（预计 30+ 处），分批 Edit，每批 5-8 处，每批间 `Read` 复核。

- [ ] **Step 5: 自检** — `Read` 重读全文，核验：
  - 标题层级连贯（H1 → H2 → H3 不跳级）
  - A 类合并未破坏
  - frontmatter 完好

- [ ] **Step 6: 本地预览** — `cd site && npm run docs:dev`，打开 appendix-a 页面：
  - 侧边栏大纲层级合理（不再出现深层节下突然跳出 H2）
  - 段落合并正常
  - ScanViewer 滚动同步正常

- [ ] **Step 7: 提交** —
  ```bash
  git add site/appendix-a.md
  git commit -m "docs: cleanup OCR formatting in site/appendix-a.md"
  ```

---

## Task 4: 试点复盘 + PageDivider.vue 决策

**Files:**
- Modify（条件性）: `site/.vitepress/theme/PageDivider.vue`

- [ ] **Step 1: 三个试点文件 diff 回顾** —
  ```bash
  git log --oneline -3
  git diff HEAD~3..HEAD -- site/ch01/index.md site/ch13/index.md site/appendix-a.md
  ```
  通读 diff，确认规则被一致应用。

- [ ] **Step 2: 评估 PageDivider 内联渲染** —
  - **若 Task 1/2/3 的本地预览中**，内联放法的 PageDivider 处**未出现**渲染异常（段落连续、无多余空白、ScanViewer 同步正常）→ **不改组件**，跳到 Step 4。
  - **若出现异常**（如段落被截断、出现多余 `<br>`、IntersectionObserver 不触发）→ 进入 Step 3。

- [ ] **Step 3（条件性）: 改 PageDivider.vue** — 把 `<div>` 改为 `<span>`：
  - `old_string`：
    ```
    <template>
      <div
        class="page-divider"
        :id="'page-div-' + pdfPage"
        :data-page="pdfPage"
      >
      </div>
    </template>
    ```
  - `new_string`：
    ```
    <template>
      <span
        class="page-divider"
        :id="'page-div-' + pdfPage"
        :data-page="pdfPage"
      >
      </span>
    </template>
    ```
  - 改完用 `cd site && npm run docs:dev` 验证三个试点页面渲染正常。

- [ ] **Step 4: 提交（若改了组件）** —
  ```bash
  git add site/.vitepress/theme/PageDivider.vue
  git commit -m "fix: PageDivider renders as span for inline placement"
  ```
  若未改组件，跳过此步。

- [ ] **Step 5: 请求用户验收试点** — 把三个试点文件的 git diff 链接或摘要交给用户，请用户逐文件过目并明确"通过"或"调整"。**未通过不进入全量阶段。**

---

## Task 4.5: D 类章节边界修复 — ch12 → ch13（试点）

**Files:**
- Modify: `site/ch12/index.md`（删除末尾 28 行 ch13 内容）
- Modify: `site/ch13/index.md`（在 frontmatter 后插入这 28 行）

**说明**：D 类问题在试点过程中发现（spec §3.4）。本任务用 ch12→ch13 边界跑通 D 类流程，作为试点的一部分。详见 spec §3.4 的错位边界清单。

**已知错位**：ch12 文件 L422-449 是 ch13 的开头内容，包括：
- `<PageDivider pdf-page="247" />` + `# 第三篇 国内实践篇`
- `<PageDivider pdf-page="248" />` + `## 我国电力现货市场的演进`（ch13 章标题）
- ch13 引言段、`## 13.1`、`### 13.1.1`、`#### 13.1.1.1`、`#### 13.1.1.2`
- 末行（ch12 L449）结束在 `…改为全电量竞争、两`（句子未完）

ch13 文件目前以 `<PageDivider pdf-page="250" />` 开头，第二行是 `部制电价模式并进入年度…`——**承接** ch12 L449 的 `两`。这种"半句跨页"形成 A 类场景，**留给 ch13 的 within-file 清理处理**，不在 D 阶段合并。

- [ ] **Step 1: 读取两文件确认剪切线** —
  - 读 `site/ch12/index.md`，确认 L420 是 `## 12.10 本章小结` 段落的最后一行（结尾 `…等特点。`），L421 为空行，L422 开始为 `<PageDivider pdf-page="247" />`。
  - 读 `site/ch13/index.md`，确认 L1-3 是 frontmatter，L4 为空行，L5 为 `<PageDivider pdf-page="250" />`。
  - 若实际行号与上述不符（例如 ch12 末尾还有意外内容），**停下来报告 NEEDS_CONTEXT**。

- [ ] **Step 2: 在 ch12 删除 L422 到 EOF** —
  - 用 `Edit` 工具：`old_string` 为 ch12 L420-449 的完整内容（从 `…等特点。` 到 `…改为全电量竞争、两`，含中间所有空行、PageDivider、标题、段落），`new_string` 为只保留 `…等特点。` + 一个换行。
  - 改完后 ch12 应结束于本章小结段落，总行数从 449 降到约 421。

- [ ] **Step 3: 在 ch13 frontmatter 后插入被剪切的块** —
  - 用 `Edit` 工具：`old_string` 为 ch13 当前 L1-5（frontmatter + 空行 + `<PageDivider pdf-page="250" />`），`new_string` 为 frontmatter + 空行 + 被剪切的 28 行 + 空行 + `<PageDivider pdf-page="250" />`。
  - 改完后 ch13 应在 frontmatter 后立即出现 `# 第三篇 国内实践篇`、ch13 章标题、引言、各小节，最后接到原本的 pdf-page 250 内容。

- [ ] **Step 4: 自检** —
  - 读 ch12 全文，确认：
    - 末尾是 `…等特点。`（本章小结段落）
    - 不再含任何 `13.`、`第三篇`、`我国电力现货市场的演进` 等 ch13 内容
    - frontmatter 完好
  - 读 ch13 全文，确认：
    - frontmatter 后第一个 H1 是 `# 第三篇 国内实践篇`
    - 紧跟着是 `## 我国电力现货市场的演进`、引言、`## 13.1` 等
    - 原 ch13 内容（pdf-page 250 起）完整保留
    - 所有 PageDivider 的 pdf-page 数值未变（247/248/249/250/...）
    - 所有图片路径未变

- [ ] **Step 5: 本地预览** —
  ```bash
  cd site && npm run docs:dev
  ```
  - 打开 ch12 页面：末尾应是 "本章小结" 内容，不再出现 ch13 的开头
  - 打开 ch13 页面：开头应是 "第三篇 国内实践篇" + ch13 章标题 + 引言 + 13.1...
  - ScanViewer 滚动同步在两章都正常

- [ ] **Step 6: 提交** —
  ```bash
  git add site/ch12/index.md site/ch13/index.md
  git commit -m "fix: move ch13 opening content from ch12 tail (D-class boundary fix)"
  ```
  一个 commit 同时改两个文件。

- [ ] **Step 7: 用户验收** — 把 ch12 和 ch13 的 diff 摘要交给用户。这是 D 类流程的试点验收点。

---

## Task 4.6: D 类边界修复 — 其余 4 处（ch14/15、ch15/16、ch19/20、ch20/21）

**Files:**
- Modify: 8 个文件（4 对边界）

**说明**：D 类流程在 Task 4.5 验收通过后，对剩余 4 处错位边界批量执行。每对边界一个 commit。**先做 D 类再做 within-file 清理**（避免内容搬移破坏已有的 PageDivider 内联）。

- [ ] **Step 1: ch14 → ch15** — 按 Task 4.5 的流程执行。ch14 末尾的 ch15 内容：ch15 章标题、15.1、15.1.1、15.1.1.1。剪切后插入 ch13 文件 frontmatter 之后。
  - 自检 + 提交：`fix: move ch15 opening content from ch14 tail (D-class)`

- [ ] **Step 2: ch15 → ch16** — ch15 末尾的 ch16 内容：16.1.1.2/16.1.1.3/16.1.2/16.1.3。剪切后插入 ch16 文件 frontmatter 之后。
  - 提交：`fix: move ch16 opening content from ch15 tail (D-class)`

- [ ] **Step 3: ch19 → ch20** — ch19 末尾的 ch20 内容：ch20 章标题、20.1、20.1.1、20.1.1.1、20.1.1.2。剪切后插入 ch20 文件 frontmatter 之后。
  - 提交：`fix: move ch20 opening content from ch19 tail (D-class)`

- [ ] **Step 4: ch20 → ch21** — ch20 末尾的 ch21 内容：`# 第四篇 技术支持系统篇`、ch21 章标题、21.1、21.1.1。剪切后插入 ch21 文件 frontmatter 之后。
  - 提交：`fix: move ch21 opening content from ch20 tail (D-class)`

- [ ] **Step 5: 整体验收** — 用户抽检 2 个边界的渲染效果。

---

## Task 5: 规则备忘录写入 spec

**Files:**
- Modify: `docs/superpowers/specs/2026-06-17-ocr-markdown-cleanup-design.md`（追加 "规则备忘录" 章节）

- [ ] **Step 1: 起草备忘录** — 基于试点经验，在 spec 末尾追加一节，固化以下规则：
  - A 类内联合并的具体判定边界（哪些标点算"句子未完"，哪些算"完整结束"）
  - B 类降级的目标层级映射表（父节 HN → 子项 HN+1）
  - C 类 `\n` 替换 `<br>` 的所有变体（含删除场景）
  - PageDivider 最终放法决策（内联 vs 块级的明确判定）
  - 已确认的"内容修改清单"处理结果

- [ ] **Step 2: 提交** —
  ```bash
  git add docs/superpowers/specs/2026-06-17-ocr-markdown-cleanup-design.md
  git commit -m "docs: append rule memo to OCR cleanup spec after pilot"
  ```

---

## Task 6: 全量阶段 — `site/ch02/index.md` ~ `site/ch12/index.md`（11 个文件）

**Files:**
- Modify: `site/ch02/index.md`, `site/ch03/index.md`, `site/ch04/index.md`, `site/ch05/index.md`, `site/ch06/index.md`, `site/ch07/index.md`, `site/ch08/index.md`, `site/ch09/index.md`, `site/ch10/index.md`, `site/ch11/index.md`, `site/ch12/index.md`

**说明：** 这 11 个文件覆盖理论篇（ch02-ch06）和国外实践篇（ch07-ch12）。每个文件**严格走 SOP（S1-S6）**，不得因为是"全量阶段"而省略用户确认（S3）。

- [ ] **Step 1: ch02 处理** — 按 SOP 处理 `site/ch02/index.md`。已知 ch02 含 19 处 PageDivider。诊断时重点关注 ch02 是否有 B 类错位标题。

- [ ] **Step 2: ch03 处理** — 按 SOP 处理 `site/ch03/index.md`（21 处 PageDivider）。

- [ ] **Step 3: ch04 处理** — 按 SOP 处理 `site/ch04/index.md`（6 处 PageDivider，较短）。

- [ ] **Step 4: ch05 处理** — 按 SOP 处理 `site/ch05/index.md`（15 处 PageDivider，含 2 处 table）。

- [ ] **Step 5: ch06 处理** — 按 SOP 处理 `site/ch06/index.md`（8 处 PageDivider，含 4 处 table）。

- [ ] **Step 6: ch07 处理** — 按 SOP 处理 `site/ch07/index.md`（31 处 PageDivider，含 12 处 table，规模较大，分批 Edit）。

- [ ] **Step 7: ch08 处理** — 按 SOP 处理 `site/ch08/index.md`（26 处 PageDivider，含 14 处 table）。

- [ ] **Step 8: ch09 处理** — 按 SOP 处理 `site/ch09/index.md`（19 处 PageDivider，含 14 处 table）。

- [ ] **Step 9: ch10 处理** — 按 SOP 处理 `site/ch10/index.md`（19 处 PageDivider，含 12 处 table，**表格密集，C 类重点**）。

- [ ] **Step 10: ch11 处理** — 按 SOP 处理 `site/ch11/index.md`（22 处 PageDivider，含 16 处 table，**表格密集，C 类重点**）。

- [ ] **Step 11: ch12 处理** — 按 SOP 处理 `site/ch12/index.md`（16 处 PageDivider，含 16 处 table）。

- [ ] **Step 12: 批次验收** — 11 个文件全部改完 commit 后，请用户抽检 2-3 个文件的 diff。若发现问题，回到对应文件修正。

---

## Task 7: 全量阶段 — `site/ch14/index.md` ~ `site/ch20/index.md`（7 个文件）

**Files:**
- Modify: `site/ch14/index.md` ~ `site/ch20/index.md`

**说明：** 国内实践篇。每个文件按 SOP 处理。

- [ ] **Step 1: ch14 处理** — SOP。18 处 PageDivider，6 处 table。

- [ ] **Step 2: ch15 处理** — SOP。34 处 PageDivider（**本批次最多**），10 处 table。**已知 B 类样本**：L81 `## 1. 发电侧上网电价` 在 `#### 15.1.4.1` 下 → 改 `##### 1.`。类似可能有 L97 `## 2. 新能源补贴及核定原则`。规模大，分批 Edit。

- [ ] **Step 3: ch16 处理** — SOP。28 处 PageDivider，2 处 table。

- [ ] **Step 4: ch17 处理** — SOP。26 处 PageDivider，8 处 table。

- [ ] **Step 5: ch18 处理** — SOP。24 处 PageDivider，10 处 table。

- [ ] **Step 6: ch19 处理** — SOP。26 处 PageDivider，12 处 table。

- [ ] **Step 7: ch20 处理** — SOP。36 处 PageDivider（**全站最多之一**），10 处 table。规模大，分批 Edit。

- [ ] **Step 8: 批次验收** — 用户抽检。

---

## Task 8: 全量阶段 — `site/ch21/index.md` ~ `site/ch31/index.md`（11 个文件）

**Files:**
- Modify: `site/ch21/index.md` ~ `site/ch31/index.md`

**说明：** 技术支持系统篇（ch21-ch30）+ 展望篇（ch31）。每个文件按 SOP 处理。

- [ ] **Step 1: ch21 处理** — SOP。7 处 PageDivider，4 处 table。

- [ ] **Step 2: ch22 处理** — SOP。7 处 PageDivider，7 处 table。

- [ ] **Step 3: ch23 处理** — SOP。22 处 PageDivider，22 处 table。

- [ ] **Step 4: ch24 处理** — SOP。10 处 PageDivider，22 处 table（**C 类重点**）。

- [ ] **Step 5: ch25 处理** — SOP。4 处 PageDivider，4 处 table。

- [ ] **Step 6: ch26 处理** — SOP。22 处 PageDivider，22 处 table（**C 类重点**）。

- [ ] **Step 7: ch27 处理** — SOP。12 处 PageDivider，4 处 table。

- [ ] **Step 8: ch28 处理** — SOP。17 处 PageDivider，22 处 table（**C 类重点**）。

- [ ] **Step 9: ch29 处理** — SOP。7 处 PageDivider，4 处 table。

- [ ] **Step 10: ch30 处理** — SOP。7 处 PageDivider，163 行（较短）。

- [ ] **Step 11: ch31 处理** — SOP。18 处 PageDivider，265 行（展望篇，规模适中）。

- [ ] **Step 12: 批次验收** — 用户抽检。

---

## Task 9: 全量阶段 — `site/appendix-b.md` + `site/index.md`

**Files:**
- Modify: `site/appendix-b.md`、`site/index.md`

- [ ] **Step 1: appendix-b 处理** — 按 SOP。23 处 PageDivider，18 处 table。

- [ ] **Step 2: index.md 处理** — 按 SOP。7 处 PageDivider。`site/index.md` 是前言与序言，注意封面图、CIP 数据等特殊内容的格式不要误改。

- [ ] **Step 3: 批次验收** — 用户过目。

---

## Task 10: 全站最终验证

**Files:**
- 全部 34 个文件 + `PageDivider.vue`（若改了）

- [ ] **Step 1: 全站本地预览** —
  ```bash
  cd site && npm run docs:dev
  ```
  逐章快速翻阅（不需要精读），重点：
  - 每章侧边栏大纲层级合理
  - 表格内多行内容正确换行
  - 段落无明显被 PageDivider 切断的痕迹
  - ScanViewer 滚动同步在每章都工作

- [ ] **Step 2: 全量构建检查** —
  ```bash
  cd site && npm run docs:build
  ```
  确认 VitePress 构建无 error。若有 warning（如非法 HTML 嵌套），回到对应文件修正。

- [ ] **Step 3: git log 检查** —
  ```bash
  git log --oneline | head -40
  ```
  确认每文件独立 commit，信息格式一致。

- [ ] **Step 4: 用户最终验收** — 请用户在 GitHub（或本地）查看整体 diff，明确"全站通过"。若有问题，回到对应 Task 修正。

- [ ] **Step 5: 推送到远程** —
  ```bash
  git push origin main
  ```
  （此步需用户明确授权后执行）

---

## 内容修改清单的处理

整个执行过程中遇到的 **OCR 错字 / 标点全半角 / 数字单位疑似错误**，不擅自修改，统一收集到一个清单（可以临时记在内存里或回复消息中）。全站完成后（Task 10 之后），把清单交给用户一次性确认，再单独一个 commit 修内容：
```bash
git commit -m "docs: fix OCR text errors across site (user-confirmed)"
```

---

## 范围与非目标（重申）

- 不重新跑 OCR、不改转换脚本
- 不改原文文字（除非用户在内容修改清单中确认）
- 不动 ScanViewer 组件、VitePress 配置
- 不做性能优化、SEO、移动端适配
- 不扩大到 A/B/C 之外的问题类型（如发现新类型，先问用户）
