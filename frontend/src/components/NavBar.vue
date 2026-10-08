<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '../stores/user'
import { useRouter } from 'vue-router'
import { getImageUrl, getUnreadCount } from '../api'
import { ElMessageBox } from 'element-plus'

const userStore = useUserStore()
const router = useRouter()
const search = ref('')
const unreadCount = ref(0)
const pollInterval = ref(null)

const handleLogout = () => {
  ElMessageBox.confirm(
    '确定要退出登录吗？',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      center: true,
      showIcon: false,
      customClass: 'logout-confirm-dialog'
    }
  ).then(() => {
    userStore.logout()
    router.push('/login')
  }).catch(() => {
    // cancel
  })
}

const handleSearch = () => {
  router.push({
    path: '/',
    query: { q: search.value }
  })
}

const fetchUnread = async () => {
  if (userStore.user) {
    try {
      const res = await getUnreadCount(userStore.user.id)
      unreadCount.value = res.data.count
    } catch (e) {
      // silent error
    }
  }
}

onMounted(() => {
  fetchUnread()
  pollInterval.value = setInterval(fetchUnread, 5000)
})

onUnmounted(() => {
  if (pollInterval.value) clearInterval(pollInterval.value)
})
</script>

<template>
  <nav class="sticky top-0 left-0 right-0 h-14 bg-white border-b border-gray-100 z-50 px-4 flex items-center justify-between relative">
    <!-- Logo -->
    <div class="flex items-center cursor-pointer" @click="router.push('/')">
      <img src="/logo2.png" alt="小红书" class="h-8 object-contain" />
    </div>

    <!-- Search (Centered on desktop, expanded on mobile) -->
    <div class="flex-1 mx-4 max-w-md md:absolute md:left-1/2 md:top-1/2 md:transform md:-translate-x-1/2 md:-translate-y-1/2 md:w-full">
      <div class="relative group">
        <input 
          v-model="search"
          type="text" 
          placeholder="探索更多内容" 
          class="w-full h-9 md:h-10 pl-8 md:pl-4 pr-8 md:pr-10 bg-gray-50 rounded-full border border-transparent focus:bg-white focus:border-gray-300 focus:outline-none text-sm transition-all"
          @keyup.enter="handleSearch"
        >
        <!-- Mobile Search Icon (Left) -->
        <div class="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 md:hidden">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
            <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
          </svg>
        </div>
        <!-- Desktop Search Icon (Right) -->
        <div class="absolute right-3 top-2.5 text-gray-400 cursor-pointer hidden md:block" @click="handleSearch">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
            <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
          </svg>
        </div>
      </div>
    </div>

    <!-- Actions (Desktop Only) -->
    <div class="hidden md:flex items-center gap-6">
      <template v-if="userStore.user">
        <button class="flex items-center gap-1.5 bg-xhs-red text-white px-4 py-1.5 rounded-full text-sm font-medium hover:bg-red-600 transition-colors" @click="router.push('/publish')">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          <span>发布</span>
        </button>

        <button class="text-gray-600 hover:text-gray-900 relative" title="通知" @click="router.push('/messages')">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
            <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
          </svg>
          <div v-if="unreadCount > 0" class="absolute -top-1 -right-1 w-4 h-4 bg-xhs-red text-white text-[10px] flex items-center justify-center rounded-full border border-white">
            {{ unreadCount > 99 ? '99+' : unreadCount }}
          </div>
        </button>

        <div class="flex items-center gap-2 cursor-pointer" @click="router.push('/profile')" title="个人主页">
          <img :src="getImageUrl(userStore.user.avatar_url) || 'https://via.placeholder.com/32'" class="w-9 h-9 rounded-full object-cover border border-gray-100">
        </div>
        
        <button @click="handleLogout" class="text-gray-400 hover:text-xhs-red transition-colors" title="退出登录">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15m3 0 3-3m0 0-3-3m3 3H9" />
          </svg>
        </button>
      </template>
      <template v-else>
        <button @click="router.push('/login')" class="px-6 py-1.5 bg-xhs-red text-white rounded-full text-sm font-medium hover:bg-red-600 transition-colors">
          登录
        </button>
      </template>
    </div>
  </nav>
</template>

<style>
.logout-confirm-dialog .el-message-box__header {
  text-align: center;
}
.logout-confirm-dialog .el-message-box__title {
  justify-content: center;
}
</style>
