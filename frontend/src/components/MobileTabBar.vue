<script setup>
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'
import { computed } from 'vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isActive = (path) => route.path === path

const handlePublish = () => {
  if (!userStore.user) {
    router.push('/login')
    return
  }
  router.push('/publish')
}

const handleProfile = () => {
  if (!userStore.user) {
    router.push('/login')
    return
  }
  router.push('/profile')
}

const handleMessage = () => {
    if (!userStore.user) {
        router.push('/login')
        return
    }
    router.push('/messages')
}
</script>

<template>
  <div class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 px-6 py-2 pb-safe flex justify-between items-center z-50 md:hidden">
    <!-- Home -->
    <button class="flex flex-col items-center gap-1 min-w-[40px]" @click="router.push('/')">
      <svg xmlns="http://www.w3.org/2000/svg" :fill="isActive('/') ? 'currentColor' : 'none'" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 transition-colors" :class="isActive('/') ? 'text-gray-900' : 'text-gray-400'">
        <path stroke-linecap="round" stroke-linejoin="round" d="m2.25 12 8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
      </svg>
      <span class="text-[10px] font-medium" :class="isActive('/') ? 'text-gray-900' : 'text-gray-400'">首页</span>
    </button>

    <!-- Category -->
    <button class="flex flex-col items-center gap-1 min-w-[40px]" @click="router.push('/category')">
      <svg xmlns="http://www.w3.org/2000/svg" :fill="isActive('/category') ? 'currentColor' : 'none'" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 transition-colors" :class="isActive('/category') ? 'text-gray-900' : 'text-gray-400'">
        <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z" />
      </svg>
      <span class="text-[10px] font-medium" :class="isActive('/category') ? 'text-gray-900' : 'text-gray-400'">分区</span>
    </button>

    <!-- Publish (Center Big Button) -->
    <button class="flex flex-col items-center gap-1 bg-xhs-red text-white rounded-xl px-3 py-1 -mt-1 shadow-md shadow-red-100" @click="handlePublish">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-6 h-6">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
      </svg>
    </button>

    <!-- Messages -->
    <button class="flex flex-col items-center gap-1 min-w-[40px]" @click="handleMessage">
      <svg xmlns="http://www.w3.org/2000/svg" :fill="isActive('/messages') ? 'currentColor' : 'none'" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 transition-colors" :class="isActive('/messages') ? 'text-gray-900' : 'text-gray-400'">
        <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
      </svg>
      <span class="text-[10px] font-medium" :class="isActive('/messages') ? 'text-gray-900' : 'text-gray-400'">消息</span>
    </button>

    <!-- Me -->
    <button class="flex flex-col items-center gap-1 min-w-[40px]" @click="handleProfile">
      <svg xmlns="http://www.w3.org/2000/svg" :fill="isActive('/profile') ? 'currentColor' : 'none'" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 transition-colors" :class="isActive('/profile') ? 'text-gray-900' : 'text-gray-400'">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
      </svg>
      <span class="text-[10px] font-medium" :class="isActive('/profile') ? 'text-gray-900' : 'text-gray-400'">我</span>
    </button>
  </div>
</template>

<style scoped>
.pb-safe {
  padding-bottom: env(safe-area-inset-bottom, 20px);
}
</style>

