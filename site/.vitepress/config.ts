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
          { text: '前言与序言', link: '/' },
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
    outline: {
      level: [2, 4],
      label: '本章节导航',
    },
  },
})
