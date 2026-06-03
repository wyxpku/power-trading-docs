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
