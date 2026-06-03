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

<script setup lang="ts">
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
