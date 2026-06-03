<template>
  <div
    class="page-divider"
    :id="'page-div-' + pdfPage"
    :data-page="pdfPage"
  >
    <span class="page-number-badge">{{ badge }}</span>
  </div>
</template>

<script setup lang="ts">
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
