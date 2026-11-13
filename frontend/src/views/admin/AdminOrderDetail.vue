<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import moment from 'moment'
import {
  getAdminOrderDetail,
  submitAdminOrder,
  reviewAdminOrder,
  completeAdminOrder,
  closeAdminOrder,
  getAdminOrderApplications,
  selectAdminOrderApplication,
  assignAdminOrder,
  getAdminUsers,
  getMediaUrl,
} from '../../api'
import { useAdminStore } from '../../stores/admin'

const router = useRouter()
const route = useRoute()
const adminStore = useAdminStore()
const orderId = route.params.id

const loading = ref(false)
const loadError = ref('')
const order = ref({})

// 角色:0 超管 / 1 运营 / 2 审核员
const role = computed(() => adminStore.user?.role)
const isOperator = computed(() => role.value === 0 || role.value === 1)
const isReviewer = computed(() => role.value === 0 || role.value === 2)

const ORDER_STATUS = { 0: '草稿', 1: '待审核', 2: '已驳回', 3: '已上线', 4: '进行中', 5: '已完成', 6: '已关闭' }
const STATUS_TAG = { 0: 'info', 1: 'warning', 2: 'danger', 3: 'success', 4: 'primary', 5: 'success', 6: 'info' }
const DELIVERY_STATUS = { 0: '待审核', 1: '已通过', 2: '退回修改' }
const DELIVERY_TYPE = { 0: '视频', 1: '外链' }
const formatTime = (t) => (t ? moment(t).format('YYYY-MM-DD HH:mm') : '-')

const canEdit = computed(() => isOperator.value && [0, 2].includes(order.value.status))
const canSubmit = computed(() => isOperator.value && [0, 2].includes(order.value.status))
const canReview = computed(() => isReviewer.value && order.value.status === 1)
const canAssign = computed(() => isOperator.value && [3, 4].includes(order.value.status))
const canClose = computed(() => isOperator.value && order.value.status !== undefined && ![5, 6].includes(order.value.status))
const showComplete = computed(() => isOperator.value && order.value.status === 4)

// ---- 报名列表(分页) ----
const applications = ref([])
const appLoading = ref(false)
const appError = ref('')
const appTotal = ref(0)
const appPage = ref(1)
const appPageSize = 5

async function loadApplications() {
  appLoading.value = true
  appError.value = ''
  try {
    const res = await getAdminOrderApplications(orderId, { page: appPage.value, page_size: appPageSize })
    const d = res.data.data
    applications.value = d.applications || d.results || []
    appTotal.value = d.count || 0
  } catch (e) {
    appError.value = e.response?.data?.message || '报名列表加载失败'
    applications.value = []
  } finally {
    appLoading.value = false
  }
}

// ---- 指派 ----
const creators = ref([])
const creatorsLoading = ref(false)
const creatorsError = ref('')
const assignCreatorId = ref(null)
const assigning = ref(false)

async function loadCreators() {
  creatorsLoading.value = true
  creatorsError.value = ''
  try {
    const res = await getAdminUsers()
    creators.value = (res.data.data.users || []).filter(u => u.role === 3)
  } catch (e) {
    creatorsError.value = e.response?.data?.message || '创作者列表加载失败'
  } finally {
    creatorsLoading.value = false
  }
}

async function assign() {
  if (!assignCreatorId.value || assigning.value) return
  assigning.value = true
  try {
    await assignAdminOrder(orderId, assignCreatorId.value)
    ElMessage.success('已指派该创作者')
    assignCreatorId.value = null
    await Promise.all([load(), loadApplications()])
  } catch (e) {
    // 重复指派等 400 提示由拦截器统一弹出
  } finally {
    assigning.value = false
  }
}

// ---- 交付预览 ----
const videoDialog = ref({ visible: false, url: '', title: '' })
function previewVideo(row) {
  videoDialog.value = { visible: true, url: getMediaUrl(row.video_file), title: `交付 #${row.id} · ${row.creator}` }
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const res = await getAdminOrderDetail(orderId)
    order.value = res.data.data.order
    if (isOperator.value) {
      loadApplications()
      if ([3, 4].includes(order.value.status)) loadCreators()
    }
  } catch (e) {
    loadError.value = e.response?.status === 403 ? '当前角色无权限查看该商单' : (e.response?.data?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function edit() {
  router.push(`/admin/orders/create?id=${orderId}`)
}

const submitting = ref(false)
async function submit() {
  if (submitting.value) return
  submitting.value = true
  try {
    await submitAdminOrder(orderId)
    ElMessage.success('已提交审核')
    await load()
  } catch (e) {
    // 拦截器已提示
  } finally {
    submitting.value = false
  }
}

const reviewing = ref(false)
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
  reviewing.value = true
  try {
    await reviewAdminOrder(orderId, action, opinion)
    ElMessage.success(action === 'approve' ? '审核通过，已上线' : '已驳回')
    await load()
  } catch (e) {
    // 拦截器已提示
  } finally {
    reviewing.value = false
  }
}

const completing = ref(false)
async function complete() {
  try {
    await ElMessageBox.confirm('结单后商单终止，确认结单？', '结单确认', {
      confirmButtonText: '确定结单',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch (e) {
    return
  }
  completing.value = true
  try {
    await completeAdminOrder(orderId)
    ElMessage.success('已结单')
    await load()
  } catch (e) {
    // 被拒时展示后端 message(拦截器弹出)
  } finally {
    completing.value = false
  }
}

const closing = ref(false)
async function close() {
  try {
    await ElMessageBox.confirm('关闭后商单终止，且无法重新开放，确认关闭？', '关闭确认', {
      confirmButtonText: '确定关闭',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch (e) {
    return
  }
  closing.value = true
  try {
    await closeAdminOrder(orderId)
    ElMessage.success('已关闭')
    await load()
  } catch (e) {
    // 拦截器已提示
  } finally {
    closing.value = false
  }
}

const selectingId = ref(null)
async function selectParticipant(application) {
  if (application.selected || selectingId.value) return
  selectingId.value = application.id
  try {
    await selectAdminOrderApplication(orderId, application.id)
    ElMessage.success('已选中该参与者')
    await Promise.all([load(), loadApplications()])
  } catch (e) {
    // 拦截器已提示
  } finally {
    selectingId.value = null
  }
}

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
      <h2 class="text-lg font-semibold">商单详情</h2>
      <div class="flex flex-wrap gap-2">
        <el-button @click="router.push('/admin/orders')">返回列表</el-button>
        <el-button v-if="isReviewer" type="primary" plain @click="router.push('/admin/reviews')">交付审核</el-button>
        <el-button v-if="canEdit" type="primary" plain @click="edit">编辑</el-button>
        <el-button v-if="canSubmit" type="primary" :loading="submitting" @click="submit">提交审核</el-button>
        <template v-if="canReview">
          <el-button type="success" :loading="reviewing" @click="review('approve')">审核通过</el-button>
          <el-button type="danger" plain :loading="reviewing" @click="review('reject')">驳回</el-button>
        </template>
        <el-tooltip v-if="showComplete" :content="order.complete_blocked_reason || '满足前置条件，可结单'" :disabled="!!order.can_complete" placement="top">
          <span>
            <el-button type="warning" plain :disabled="!order.can_complete" :loading="completing" @click="complete">结单</el-button>
          </span>
        </el-tooltip>
        <el-button v-if="canClose" type="danger" plain :loading="closing" @click="close">关闭</el-button>
      </div>
    </div>
    <p v-if="showComplete && !order.can_complete && order.complete_blocked_reason" class="text-xs text-gray-400 mb-4 text-right">
      结单前置未满足：{{ order.complete_blocked_reason }}
    </p>

    <!-- 失败态 -->
    <el-card v-if="loadError && !loading" class="mb-4">
      <div class="text-center py-6">
        <p class="text-sm text-red-500 mb-4">{{ loadError }}</p>
        <el-button type="primary" plain @click="load">重试</el-button>
        <el-button @click="router.push('/admin/orders')">返回列表</el-button>
      </div>
    </el-card>

    <template v-if="!loadError">
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

      <!-- 指派参与者(运营,上线/进行中) -->
      <el-card v-if="canAssign" class="mb-4">
        <template #header><span class="font-semibold">指派参与者</span></template>
        <div v-if="creatorsError" class="text-sm text-red-500">
          {{ creatorsError }}
          <el-button size="small" class="ml-2" @click="loadCreators">重试</el-button>
        </div>
        <div v-else class="flex items-center gap-3 flex-wrap">
          <el-select
            v-model="assignCreatorId"
            filterable
            clearable
            placeholder="选择创作者(普通用户)"
            :loading="creatorsLoading"
            style="width: 260px"
          >
            <el-option v-for="u in creators" :key="u.id" :label="`${u.nickname || u.username} (${u.username})`" :value="u.id" />
          </el-select>
          <el-button type="primary" :disabled="!assignCreatorId" :loading="assigning" @click="assign">指派</el-button>
          <span class="text-xs text-gray-400">指派后创作者直接入选，商单进入进行中</span>
        </div>
      </el-card>

      <!-- 报名列表(运营,分页) -->
      <el-card class="mb-4" v-if="isOperator">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="font-semibold">报名列表</span>
            <span class="text-xs text-gray-400">共 {{ appTotal }} 条</span>
          </div>
        </template>
        <div v-if="appError" class="text-sm text-red-500 py-2">
          {{ appError }}
          <el-button size="small" class="ml-2" @click="loadApplications">重试</el-button>
        </div>
        <template v-else>
          <div v-loading="appLoading">
            <div v-if="applications.length" class="space-y-2">
              <div v-for="app in applications" :key="app.id" class="flex items-center justify-between border rounded px-3 py-2">
                <div>
                  <span class="font-medium">{{ app.creator_name || app.creator }}</span>
                  <el-tag v-if="app.selected" type="success" size="small" class="ml-2">已选中</el-tag>
                  <span class="text-xs text-gray-400 ml-2">{{ formatTime(app.created_at) }}</span>
                  <p class="text-gray-500 text-sm mt-1">{{ app.proposal || '无报名说明' }}</p>
                </div>
                <el-button
                  v-if="!app.selected && [3, 4].includes(order.status)"
                  size="small"
                  type="primary"
                  :loading="selectingId === app.id"
                  @click="selectParticipant(app)"
                >选中</el-button>
              </div>
            </div>
            <el-empty v-else-if="!appLoading" description="暂无报名" :image-size="60" />
          </div>
          <el-pagination
            v-if="appTotal > appPageSize"
            class="mt-3 justify-end"
            layout="total, prev, pager, next"
            :total="appTotal"
            :current-page="appPage"
            :page-size="appPageSize"
            small
            @current-change="v => { appPage = v; loadApplications() }"
          />
        </template>
      </el-card>

      <!-- 交付记录 -->
      <el-card>
        <template #header>
          <div class="flex items-center justify-between">
            <span class="font-semibold">交付记录</span>
            <el-button v-if="isReviewer" size="small" type="primary" plain @click="router.push('/admin/reviews')">去审核交付</el-button>
          </div>
        </template>
        <el-table :data="order.deliveries || []" stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="creator" label="创作者" width="120" />
          <el-table-column label="交付方式" width="100">
            <template #default="{ row }">
              <el-tag :type="row.delivery_type === 0 ? 'primary' : 'warning'" size="small">{{ DELIVERY_TYPE[row.delivery_type] }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="交付内容" min-width="180">
            <template #default="{ row }">
              <el-button v-if="row.delivery_type === 0 && row.video_file" size="small" type="primary" plain @click="previewVideo(row)">预览视频</el-button>
              <a
                v-else-if="row.delivery_type === 1 && row.video_url"
                :href="row.video_url"
                target="_blank"
                rel="noopener noreferrer"
                class="text-blue-600 hover:underline break-all"
              >{{ row.video_url }}</a>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="note" label="交付说明" min-width="120" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 1 ? 'success' : row.status === 2 ? 'danger' : 'warning'" size="small">{{ DELIVERY_STATUS[row.status] }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="提交时间" width="150">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!(order.deliveries || []).length" description="暂无交付" :image-size="60" />
      </el-card>
    </template>

    <!-- 视频预览弹窗 -->
    <el-dialog v-model="videoDialog.visible" :title="videoDialog.title" width="720px" destroy-on-close>
      <video v-if="videoDialog.url" controls preload="metadata" :src="videoDialog.url" class="w-full max-h-[60vh] rounded bg-black"></video>
    </el-dialog>
  </div>
</template>