# PDF 图表裁剪与 SVG 重绘设计

## 概述

将 HTML 中引用整页 PNG 的图表替换为裁剪后的局部图片或 SVG 重绘，使电子书中的图表只保留原始图片区域，去除周围的文字和空白。

## 背景

当前流程：PDF → 每页 PNG（`page_NNN.png`）→ OCR 转 HTML。HTML 中图表用 `<figure class="embedded-figure">` 包裹，但 `<img src>` 指向整页 PNG。`pages/crops/` 下已有 151 张裁剪图需全部重做。

## 方案：逐页 AI 识别 + 裁剪

### 整体流程

**第一步：回溯已 OCR 的页面（存量）**
- 扫描所有 HTML 文件，收集所有 `<figure class="embedded-figure">` 元素
- 提取每个 figure 的页码（从父级 `page-body-container` 或 `page-divider` 的 `data-page` 属性获取）
- 提取 figcaption 文字（如果有）作为定位线索
- 去重：同一页只需分析一次

**第二步：新页面同步裁剪（增量）**
- OCR 转录过程中识别到图片时，立即执行裁剪
- 裁剪结果保存后直接在 HTML 中引用

**单页裁剪流程：**
1. 将页面 PNG 传给 AI 视觉 MCP（`analyze_image`），识别所有图表区域的矩形坐标（像素级：x, y, width, height）
2. AI 同时判断每个图表是否适合 SVG 重绘
3. 适合重绘的 → 提取数据，生成内联 SVG
4. 不适合重绘的 → 用 `sips` 按坐标裁剪，保存到 `pages/crops/page_NNN_figX.png`
5. 更新 HTML 中 `<img>` 的 `src`

### AI 视觉识别策略

**Prompt 要求：**
- 识别页面中所有独立的图表、示意图、照片、流程图等视觉元素（排除纯文字）
- 对每个区域返回：序号、边界坐标（x, y, width, height，像素单位）、图表类型描述
- 提供 figcaption 标题文字作为辅助定位线索
- 忽略页眉、页脚、页码

**坐标精度：** 裁剪时每个方向加 2-5px padding。裁剪区域与页面面积比超过 90% 时视为误判，保留原图。

**多图页面：** AI 一次返回所有图片坐标，按从上到下、从左到右编号为 fig1, fig2, fig3...。通过 figcaption 标题匹配或位置顺序与 HTML 中的 `<figure>` 一一对应。

### SVG 重绘策略

**适合重绘的图表类型：** 折线图、柱状图、饼状图、散点图、简单表格图等数据可视化类图表。

**不适合重绘的：** 架构图、流程图、照片、复杂示意图、包含大量中文标注的图。

**重绘流程：**
1. AI 提取图表中的数据点、标签、坐标轴信息
2. 生成内联 SVG 直接嵌入 HTML
3. SVG 样式使用 CSS 变量保持风格一致

**降级策略：** 数据提取不完整或重绘失败时，退回裁剪原图方案，不丢失信息。

**输出格式：**
- SVG 重绘：`<figure class="embedded-figure"><div class="svg-chart">...</div><figcaption>...</figcaption></figure>`
- 裁剪原图：`<figure class="embedded-figure"><img src="pages/crops/page_NNN_figX.png"><figcaption>...</figcaption></figure>`

### 错误处理

| 情况 | 处理 |
|------|------|
| AI 无法识别图片区域 | 保留原图引用 |
| 裁剪区域 > 页面面积 90% | 疑似误判，保留原图 |
| 坐标超出页面尺寸 | 忽略该坐标，保留原图 |
| SVG 数据提取不完整 | 降级为裁剪原图 |

### 进度管理

- 已处理标记：`pages/crops/page_NNN_figX.png` 存在且 HTML `src` 已指向它
- 重新运行时自动跳过已完成页面（除非强制重做）
- 处理日志记录每页结果（成功/跳过/失败）

### 文件组织

- 裁剪图：`book/pages/crops/page_NNN_figX.png`
- 旧裁剪图全部清除后重新生成
- SVG 图表内联在 HTML 中，不产生额外文件
