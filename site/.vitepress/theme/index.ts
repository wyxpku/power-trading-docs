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
