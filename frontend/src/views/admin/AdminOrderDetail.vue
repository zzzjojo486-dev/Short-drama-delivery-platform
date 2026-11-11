<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getAdminOrderDetail,
  submitAdminOrder,
  reviewAdminOrder,
  completeAdminOrder,
  closeAdminOrder,
  getAdminOrderApplications,
  selectAdminOrderApplication,
} from '../../api'
import { useAdminStore } from '../../stores/admin'

const router = useRouter()
const route = useRoute()
const adminStore = useAdminStore()
const orderId = route.params.id

const loading = ref(false)
const order = ref({})
const applications = ref([])
const loadingDeliveries = ref(false)

// 角色:0 超管 / 1 运营 / 2 审核员
const role = computed(() => adminStore.user?.role)
const isOperator = computed(() => role.value === 0 || role.value === 1)
const isReviewer = computed(() => role.value === 0 || role.value === 2)

const ORDER_STATUS = { 0: '草稿', 1: '待审核', 2: '已驳回', 3: '已上线', 4: '进行中', 5: '已完成', 6: '已关闭' }
const STATUS_TAG = { 0: 'info', 1: 'warning', 2: 'danger', 3: 'success', 4: 'primary', 5: 'success', 6: 'info' }
const DELIVERY_STATUS = { 0: '待审核', 1: '已通过', 2: '退回修改' }
const DELIVERY_TYPE = { 0: '视频', 1: '链接' }

// 可编辑(草稿/驳回)、可提交审核(草稿/驳回)、可在线结单/关闭等状态判断
const canEdit = computed(() => isOperator.value && [0, 2].includes(order.value.status))
const canSubmit = computed(() => isOperator.value && [0, 2].includes(order.value.status))
const canReview = computed(() => isReviewer.value && order.value.status === 1)
const canComplete = computed(() => isOperator.value && order.value.status === 4 && (order.value.deliveries || []).some(delivery => delivery.status === 1))
const canClose = computed(() => isOperator.value && order.value.status !== undefined && ![5, 6].includes(order.value.status))

async function load() {
  loading.value = true
  try {
    const res = await getAdminOrderDetail(orderId)
    order.value = res.data.data.order
    if (isOperator.value) loadApplications()
  } catch (e) {
    if (e.response && e.response.status === 403) {
      ElMessage.error('无权限访问后台')
      router.push('/admin/login')
    } else {
      ElMessage.error(e.response?.data?.message || '加载失败')
    }
  } finally {
    loading.value = false
  }
}

async function loadApplications() {
  try {
    const res = await getAdminOrderApplications(orderId)
    applications.value = res.data.data.applications
  } catch (e) {
    // 报名列表接口对审核员可能不可见,静默即可
    applications.value = []
  }
}

function edit() {
  router.push(`/admin/orders/create?id=${orderId}`)
}

async function submit() {
  try {
    await submitAdminOrder(orderId)
    ElMessage.success('已提交审核')
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '提交失败')
  }
}

async function review(action) {
  let opinion = ''
  if (action === 'reject') {
    try {
      const { value } = await ElMessageBox.prompt('请填写驳回意见', '驳回', {
        inputType: 'textarea',
        confirmButtonText: '确定驳回',
        cancelButtonText: '取消',
      })
      opinion = (value || '').trim()
      if (!opinion) {
        ElMessage.warning('驳回意见必填')
        return
      }
    } catch (e) {
      return
    }
  }
  try {
    await reviewAdminOrder(orderId, action, opinion)
    ElMessage.success(action === 'approve' ? '审核通过，已上线' : '已驳回')
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '审核失败')
  }
}

async function complete() {
  try {
    await ElMessageBox.confirm('结单后商单终止，确认结单？', '结单确认')
  } catch (e) {
    return
  }
  try {
    await completeAdminOrder(orderId)
    ElMessage.success('已结单')
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '结单失败')
  }
}

async function close() {
  try {
    await ElMessageBox.confirm('关闭后商单终止，且无法重新开放，确认关闭？', '关闭确认')
  } catch (e) {
    return
  }
  try {
    await closeAdminOrder(orderId)
    ElMessage.success('已关闭')
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '关闭失败')
  }
}

async function selectParticipant(application) {
  if (application.selected) return
  try {
    await selectAdminOrderApplication(orderId, application.id)
    ElMessage.success('已选中该参与者')
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '操作失败')
  }
}

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold">商单详情</h2>
      <div>
        <el-button @click="router.push('/admin/orders')">返回列表</el-button>
        <el-button type="primary" plain @click="edit" v-if="canEdit">编辑</el-button>
        <el-button type="primary" @click="submit" v-if="canSubmit">提交审核</el-button>
        <template v-if="canReview">
          <el-button type="success" @click="review('approve')">审核通过</el-button>
          <el-button type="danger" plain @click="review('reject')">驳回</el-button>
        </template>
        <el-button type="warning" plain @click="complete" v-if="canComplete">结单</el-button>
        <el-button type="danger" plain @click="close" v-if="canClose">关闭</el-button>
      </div>
    </div>

    <!-- 需求信息 -->
    <el-card class="mb-4">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="font-semibold">{{ order.title || '(无标题)' }}</span>
          <el-tag :type="STATUS_TAG[order.status]" size="small" v-if="order.status !== undefined">{{ ORDER_STATUS[order.status] }}</el-tag>
        </div>
      </template>
      <el-descriptions :column="2">
        <el-descriptions-item label="分类">{{ order.category || '-' }}</el-descriptions-item>
        <el-descriptions-item label="预算">{{ order.budget || '-' }}</el-descriptions-item>
        <el-descriptions-item label="简介" :span="2">{{ order.brief || '-' }}</el-descriptions-item>
        <el-descriptions-item label="交付要求" :span="2">{{ order.requirement || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 报名列表(运营) -->
    <el-card class="mb-4" v-if="isOperator">
      <template #header><span class="font-semibold">报名列表</span></template>
      <div v-if="applications.length" class="space-y-2">
        <div v-for="app in applications" :key="app.id" class="flex items-center justify-between border rounded px-3 py-2">
          <div>
            <span class="font-medium">{{ app.creator_name || app.creator }}</span>
            <el-tag v-if="app.selected" type="success" size="small" class="ml-2">已选中</el-tag>
            <p class="text-gray-500 text-sm mt-1">{{ app.proposal || '无报名说明' }}</p>
          </div>
          <el-button v-if="!app.selected && [3, 4].includes(order.status)" size="small" type="primary" @click="selectParticipant(app)">选中</el-button>
        </div>
      </div>
      <el-empty v-else description="暂无报名" :image-size="60" />
    </el-card>

    <!-- 交付记录 -->
    <el-card>
      <template #header><span class="font-semibold">交付记录</span></template>
      <el-table :data="order.deliveries || []" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="交付方式" width="100">
          <template #default="{ row }">
            <el-tag :type="row.delivery_type === 0 ? 'primary' : 'warning'" size="small">{{ DELIVERY_TYPE[row.delivery_type] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="交付内容" min-width="160">
          <template #default="{ row }">
            <span v-if="row.delivery_type === 0 && row.video_url">视频:{{ row.video_url }}</span>
            <span v-else-if="row.delivery_type === 1 && row.video_url">链接:{{ row.video_url }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="note" label="交付说明" min-width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : row.status === 2 ? 'danger' : 'warning'" size="small">{{ DELIVERY_STATUS[row.status] }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!(order.deliveries || []).length" description="暂无交付" :image-size="60" />
    </el-card>
  </div>
</template>