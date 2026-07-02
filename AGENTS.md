# Power Trading — 电力现货市场实务

本项目将《电力现货市场实务》一书部署为 GitHub Pages 电子书。

- **框架**: VitePress，源文件在 `site/` 目录下
- **内容**: 31 章 + 2 个附录（`site/ch01/` ~ `site/ch31/`，`site/appendix-a.md`，`site/appendix-b.md`）
- **部署**: GitHub Actions 推送到 GitHub Pages
- **构建**: `cd site && npm run docs:dev`（本地预览）、`npm run docs:build`（构建）

## Skills

- **guided-learning** — 用于学习 `site/` 下的文档内容。当用户想学习、复习或深入理解某个章节/概念时，使用此 skill。定义文件位于 `.skills/guided-learning/SKILL.md`。

## 学习进度管理

学习进度文件（`learning/`、`concepts/`、`research/glossary.md`、`SKILLS/guided-learning/logs/`）每次更新后，必须提交到 git 并推送到远程仓库，确保进度不丢失。提交信息格式：`docs: update learning progress - [章节/简述]`。
