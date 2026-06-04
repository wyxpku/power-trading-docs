<template>
  <div
    class="page-divider"
    :id="'page-div-' + pdfPage"
    :data-page="pdfPage"
  >
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  pdfPage: number
}>()
</script>

<style scoped>
.page-divider {
  position: relative;
}
</style>
