<script setup>
import { RouterLink, RouterView, useRoute } from 'vue-router'
import NavBar from './components/NavBar.vue'
import MobileTabBar from './components/MobileTabBar.vue'
import { computed } from 'vue'

const route = useRoute()

const containerClass = computed(() => {
  // 如果隐藏了底部导航栏，使用固定高度而不是 min-h
  if (route.meta.hideTabBar) {
    return 'h-screen bg-xhs-bg md:pb-0'
  }
  return 'min-h-screen bg-xhs-bg pb-16 md:pb-0'
})
</script>

<template>
  <NavBar v-if="!route.meta.hideNavBar" />
  <div :class="containerClass">
    <RouterView />
  </div>
  <MobileTabBar v-if="!route.meta.hideTabBar" />
</template>

<style scoped>
</style>



