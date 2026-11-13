<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getCreatorOrders } from '../../api'
import { ORDER_STATUS, ORDER_STATUS_CLASS, formatTime } from './meta'

const router = useRouter()
const list = ref([])
const loading = ref(false)
const loadError = ref('')
const total = ref(0)
const page = ref(1)
const pageSize = 10
const search = ref('')
const statusFilter = ref('')

const STATUS_TABS = [
  { value: '', label: '全部' },
  { value: 3, label: '已上线' },
  { value: 4, label: '进行中' },
  { value: 5, label: '已完成' },
  { value: 6, label: '已关闭' },
]

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const params = { page: page.value, page_size: pageSize }
    if (statusFilter.value !== '') params.status = statusFilter.value
    if (search.value.trim()) params.search = search.value.trim()
    const res = await getCreatorOrders(params)
    list.value = res.data.data.results || []
    total.value = res.data.data.count || 0
  } catch (e) {
    loadError.value = e.response?.data?.message || '加载失败，请重试'
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.value = 1
  load()
}

function setStatus(value) {
  statusFilter.value = value
  page.value = 1
  load()
}

function changePage(delta) {
  page.value += delta
  load()
}

function relationBadge(o) {
  if (o.is_selected) return { label: '已入选', cls: 'bg-emerald-500 text-white' }
  if (o.is_applied) return { label: '已报名', cls: 'bg-blue-500 text-white' }
  return { label: '未报名', cls: 'bg-gray-100 text-gray-500' }
}

const totalPages = () => Math.max(1, Math.ceil(total.value / pageSize))

onMounted(load)
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 py-6">
    <!-- 页头 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">商单大厅</h1>
      <p class="text-sm text-gray-400 mt-1">浏览短剧交付商单，报名入选后提交视频或外链交付</p>
    </div>

    <!-- 筛选 -->
    <div class="flex flex-col md:flex-row md:items-center gap-3 mb-5">
      <div class="flex items-center gap-2 flex-wrap">
        <button
          v-for="tab in STATUS_TABS"
          :key="tab.label"
          class="px-4 py-1.5 rounded-full text-sm font-medium transition-colors"
          :class="statusFilter === tab.value ? 'bg-xhs-red text-white shadow-sm' : 'bg-white text-gray-500 border border-gray-100 hover:text-gray-800'"
          @click="setStatus(tab.value)"
        >
          {{ tab.label }}
        </button>
      </div>
      <div class="relative md:ml-auto md:w-64">
        <input
          v-model="search"
          type="text"
          placeholder="搜索商单标题"
          class="w-full h-9 pl-4 pr-9 bg-white rounded-full border border-gray-100 focus:border-xhs-red focus:outline-none text-sm transition-colors"
          @keyup.enter="onSearch"
        >
        <button class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-xhs-red" @click="onSearch">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
            <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
          </svg>
        </button>
      </div>
    </div>

    <!-- 失败态 -->
    <div v-if="loadError && !loading" class="bg-white rounded-2xl border border-red-100 p-8 text-center">
      <p class="text-sm text-xhs-red mb-4">{{ loadError }}</p>
      <button class="px-6 py-2 bg-xhs-red text-white rounded-full text-sm font-medium hover:bg-red-600" @click="load">重试</button>
    </div>

    <!-- 加载态 -->
    <div v-else-if="loading" class="grid md:grid-cols-2 gap-4">
      <div v-for="i in 4" :key="i" class="bg-white rounded-2xl border border-gray-100 p-5 animate-pulse">
        <div class="h-5 bg-gray-100 rounded w-2/3 mb-4"></div>
        <div class="h-4 bg-gray-50 rounded w-1/2 mb-4"></div>
        <div class="h-4 bg-gray-50 rounded w-full mb-2"></div>
        <div class="h-4 bg-gray-50 rounded w-4/5"></div>
      </div>
    </div>

    <!-- 空态 -->
    <div v-else-if="!list.length" class="bg-white rounded-2xl border border-gray-100 p-12 text-center">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.2" stroke="currentColor" class="w-12 h-12 mx-auto text-gray-200 mb-4">
        <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 14.15v4.25c0 1.094-.886 2.05-1.98 2.146-2.093.184-4.212.279-6.352.279-2.14 0-4.26-.095-6.352-.279-1.094-.096-1.98-1.052-1.98-2.146v-4.25m16.664 0a2.25 2.25 0 0 0-2.083-2.164 48.6 48.6 0 0 0-8.33 0 2.25 2.25 0 0 0-2.083 2.164m16.664 0v-2.106c0-1.094-.886-2.05-1.98-2.146a48.6 48.6 0 0 0-3.02-.196M3.586 14.15v-2.106c0-1.094.886-2.05 1.98-2.146 1.006-.088 2.013-.153 3.02-.196m8.33 0a48.6 48.6 0 0 0-8.33 0m8.33 0v-3.375c0-.621-.504-1.125-1.125-1.125h-2.25c-.621 0-1.125.504-1.125 1.125v3.375" />
      </svg>
      <p class="text-sm text-gray-400">暂无符合条件的商单</p>
      <p class="text-xs text-gray-300 mt-1">换个筛选条件试试，或稍后再来看看</p>
    </div>

    <!-- 列表 -->
    <div v-else class="grid md:grid-cols-2 gap-4">
      <article
        v-for="o in list"
        :key="o.id"
        class="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow p-5 flex flex-col gap-3 cursor-pointer"
        @click="router.push(`/orders/${o.id}`)"
      >
        <div class="flex items-start justify-between gap-2">
          <h3 class="font-semibold text-[15px] text-gray-900 line-clamp-1">{{ o.title }}</h3>
          <span class="shrink-0 text-[11px] px-2 py-0.5 rounded-full font-medium" :class="ORDER_STATUS_CLASS[o.status]">{{ ORDER_STATUS[o.status] }}</span>
        </div>
        <div class="flex items-center gap-2 text-xs flex-wrap">
          <span class="px-2 py-0.5 rounded-full font-medium" :class="relationBadge(o).cls">{{ relationBadge(o).label }}</span>
          <span v-if="o.category" class="px-2 py-0.5 rounded-full bg-gray-50 text-gray-500 border border-gray-100">{{ o.category }}</span>
          <span class="text-xhs-red font-semibold">预算 {{ o.budget || '面议' }}</span>
        </div>
        <p class="text-sm text-gray-500 line-clamp-2 min-h-[2.5rem]">{{ o.brief || o.requirement || '暂无简介' }}</p>
        <div class="flex items-center justify-between mt-auto pt-3 border-t border-gray-50">
          <span class="text-xs text-gray-400">{{ formatTime(o.created) }}</span>
          <div class="flex gap-2">
            <button
              v-if="o.can_apply"
              class="px-4 py-1.5 bg-xhs-red text-white rounded-full text-xs font-medium hover:bg-red-600 transition-colors"
              @click.stop="router.push(`/orders/${o.id}?apply=1`)"
            >报名</button>
            <button
              v-if="o.can_deliver"
              class="px-4 py-1.5 bg-xhs-red text-white rounded-full text-xs font-medium hover:bg-red-600 transition-colors"
              @click.stop="router.push(`/orders/${o.id}?deliver=1`)"
            >提交交付</button>
            <button
              class="px-4 py-1.5 bg-gray-50 text-gray-600 rounded-full text-xs font-medium hover:bg-gray-100 transition-colors"
              @click.stop="router.push(`/orders/${o.id}`)"
            >详情</button>
          </div>
        </div>
      </article>
    </div>

    <!-- 分页 -->
    <div v-if="!loading && !loadError && total > 0" class="flex items-center justify-center gap-4 mt-6">
      <button
        class="px-4 py-1.5 rounded-full text-sm bg-white border border-gray-100 text-gray-600 disabled:opacity-40 disabled:cursor-not-allowed hover:border-gray-300"
        :disabled="page <= 1"
        @click="changePage(-1)"
      >上一页</button>
      <span class="text-sm text-gray-400">{{ page }} / {{ totalPages() }} · 共 {{ total }} 个商单</span>
      <button
        class="px-4 py-1.5 rounded-full text-sm bg-white border border-gray-100 text-gray-600 disabled:opacity-40 disabled:cursor-not-allowed hover:border-gray-300"
        :disabled="page >= totalPages()"
        @click="changePage(1)"
      >下一页</button>
    </div>
  </div>
</template>