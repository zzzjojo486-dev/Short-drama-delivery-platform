<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { getPosts } from '../api'
import WaterfallCard from '../components/WaterfallCard.vue'
import { useRouter, useRoute } from 'vue-router'
import { useTransitionStore } from '../stores/transition'

const router = useRouter()
const route = useRoute()
const transitionStore = useTransitionStore()
const posts = ref([])
const categories = ["推荐", "穿搭", "美食", "彩妆", "影视", "职场", "情感", "家居", "游戏", "旅行", "健身"]
const activeCategory = ref("推荐")

// Column Management
const columnCount = ref(2)
const updateColumnCount = () => {
  const width = window.innerWidth
  if (width >= 1280) columnCount.value = 5 // xl
  else if (width >= 1024) columnCount.value = 4 // lg
  else if (width >= 768) columnCount.value = 3 // md
  else columnCount.value = 2 // default
}

const waterfallPosts = computed(() => {
  if (!posts.value.length) return []
  const cols = Array.from({ length: columnCount.value }, () => [])
  posts.value.forEach((post, index) => {
    cols[index % columnCount.value].push(post)
  })
  return cols
})

const fetchPosts = async () => {
  try {
    const searchQuery = route.query.q || ''
    const res = await getPosts(20, 0, searchQuery, activeCategory.value)
    posts.value = res.data
  } catch (e) {
    console.error(e)
  }
}

watch(activeCategory, () => {
  fetchPosts()
})

watch(() => route.query.q, () => {
  fetchPosts()
})

watch(() => route.query.category, (newVal) => {
  activeCategory.value = newVal || "推荐"
})

onMounted(() => {
  if (route.query.category) {
    activeCategory.value = route.query.category
  }
  fetchPosts()
  updateColumnCount()
  window.addEventListener('resize', updateColumnCount)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateColumnCount)
})

const goToDetail = (id, event) => {
  // Get the image element from the click event
  const cardElement = event.currentTarget
  const imgElement = cardElement.querySelector('img')
  
  if (imgElement) {
    const rect = imgElement.getBoundingClientRect()
    transitionStore.setRect(rect, imgElement.src)
  }
  
  router.push(`/explore/${id}`)
}
</script>

<template>
  <!-- Category Tabs - Scroll with content under the nav bar -->
  <div class="hidden md:block bg-white border-b border-gray-100/50 shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
    <div class="flex items-center justify-center gap-1 py-2 overflow-x-auto no-scrollbar max-w-7xl mx-auto px-4">
      <button 
        v-for="cat in categories" 
        :key="cat"
        @click="activeCategory = cat"
        class="px-4 py-1.5 rounded-full text-[15px] whitespace-nowrap transition-all duration-200"
        :class="activeCategory === cat ? 'text-gray-900 font-bold bg-gray-100' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'"
      >
        {{ cat }}
      </button>
    </div>
  </div>

  <div class="container mx-auto px-2 md:px-4 max-w-7xl mt-2">
    <!-- Waterfall Grid (JS Calculated) -->
    <div class="flex gap-2 md:gap-4 items-start">
      <div v-for="(col, index) in waterfallPosts" :key="index" class="flex-1 space-y-2 md:space-y-4 flex flex-col">
        <WaterfallCard 
          v-for="post in col" 
          :key="post.id" 
          :post="post" 
          @click="goToDetail"
        />
      </div>
    </div>
    
    <div v-if="posts.length === 0" class="text-center py-20 text-gray-400">
      <p>暂无内容，快去发布第一篇笔记吧</p>
    </div>

    <!-- Modal Router View -->
    <router-view v-slot="{ Component }">
      <transition name="modal-fade">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<style>
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
