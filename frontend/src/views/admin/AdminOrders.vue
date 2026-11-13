<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getAdminOrders } from '../../api'

const router = useRouter()
const list = ref([])
const loading = ref(false)
const loadError = ref('')
const total = ref(0)

const filters = ref({ status: '', category: '', search: '' })
const page = ref(1)
const pageSize = ref(10)

// 状态机常量（与 PLAN.md §3 一致）
const ORDER_STATUS = { 0: '草稿', 1: '待审核', 2: '已驳回', 3: '已上线', 4: '进行中', 5: '已完成', 6: '已关闭' }
const STATUS_TAG = { 0: 'info', 1: 'warning', 2: 'danger', 3: 'success', 4: 'primary', 5: 'success', 6: 'info' }

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filters.value.status !== '') params.status = filters.value.status
    if (filters.value.category) params.category = filters.value.category
    if (filters.value.search) params.search = filters.value.search
    const res = await getAdminOrders(params)
    // DRF 分页信封 {count, next, previous, results}
    list.value = res.data.data.results
    total.value = res.data.data.count
  } catch (e) {
    loadError.value = e.response?.status === 403 ? '当前角色无权限查看商单列表' : (e.response?.data?.message || '加载失败')
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

function goCreate() {
  router.push('/admin/orders/create')
}

function goDetail(row) {
  router.push(`/admin/orders/${row.id}`)
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold">商单管理</h2>
      <el-button v-if="!loadError" type="primary" @click="goCreate">创建商单</el-button>
    </div>

    <!-- 筛选栏 -->
    <el-form inline class="mb-4">
      <el-form-item label="状态">
        <el-select v-model="filters.status" clearable placeholder="全部" style="width: 130px" @change="onSearch">
          <el-option v-for="(label, val) in ORDER_STATUS" :key="val" :label="label" :value="Number(val)" />
        </el-select>
      </el-form-item>
      <el-form-item label="分类">
        <el-input v-model="filters.category" placeholder="分类" clearable style="width: 150px" @keyup.enter="onSearch" @clear="onSearch" />
      </el-form-item>
      <el-form-item label="标题">
        <el-input v-model="filters.search" placeholder="搜索标题" clearable style="width: 180px" @keyup.enter="onSearch" @clear="onSearch" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" plain @click="onSearch">查询</el-button>
      </el-form-item>
    </el-form>

    <el-card v-if="loadError && !loading" class="mb-4">
      <div class="text-center py-6">
        <p class="text-sm text-red-500 mb-4">{{ loadError }}</p>
        <el-button type="primary" plain @click="load">重试</el-button>
      </div>
    </el-card>

    <template v-else>
    <el-table :data="list" v-loading="loading" stripe @row-click="goDetail" class="cursor-pointer" empty-text="暂无商单">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="title" label="标题" min-width="180" />
      <el-table-column prop="category" label="分类" width="120" />
      <el-table-column prop="budget" label="预算" width="120" />
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="STATUS_TAG[row.status]" size="small">{{ ORDER_STATUS[row.status] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="90">
        <template #default="{ row }">
          <el-link type="primary" @click.stop="goDetail(row)">详情</el-link>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      class="mt-4 justify-end"
      layout="total, prev, pager, next"
      :total="total"
      :current-page="page"
      :page-size="pageSize"
      @current-change="v => { page = v; load() }"
    />
    </template>
  </div>
</template>