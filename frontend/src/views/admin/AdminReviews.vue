<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import moment from 'moment'
import { getPendingDeliveries, reviewDelivery, getMediaUrl } from '../../api'

const router = useRouter()
const deliveries = ref([])
const loading = ref(false)
const loadError = ref('')
const total = ref(0)
const page = ref(1)
const pageSize = 10

const formatTime = (t) => (t ? moment(t).format('YYYY-MM-DD HH:mm') : '-')

const dialogs = ref({
  visible: false,
  action: '',
  delivery: null,
  opinion: '',
  submitting: false,
})

const videoDialog = ref({ visible: false, url: '', title: '' })
function previewVideo(row) {
  videoDialog.value = { visible: true, url: getMediaUrl(row.video_file), title: `交付 #${row.id} · ${row.creator}` }
}

async function loadDeliveries() {
  loading.value = true
  loadError.value = ''
  try {
    const res = await getPendingDeliveries({ page: page.value, page_size: pageSize })
    const d = res.data.data
    deliveries.value = d.deliveries || d.results || []
    total.value = d.count || 0
  } catch (e) {
    loadError.value = e.response?.status === 403 ? '当前角色无权限查看待审核交付' : (e.response?.data?.message || '加载失败')
    deliveries.value = []
  } finally {
    loading.value = false
  }
}

function openReview(delivery, action) {
  dialogs.value = { visible: true, action, delivery, opinion: '', submitting: false }
}

async function confirmReview() {
  const { action, delivery, opinion, submitting } = dialogs.value
  if (submitting) return
  if (action === 'reject' && !opinion.trim()) {
    ElMessage.warning('驳回时请填写审核意见')
    return
  }
  dialogs.value.submitting = true
  try {
    await reviewDelivery(delivery.id, action, opinion.trim())
    ElMessage.success(action === 'approve' ? '已通过' : '已驳回')
    dialogs.value.visible = false
    loadDeliveries()
  } catch (e) {
    // 拦截器已提示
  } finally {
    dialogs.value.submitting = false
  }
}

onMounted(loadDeliveries)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold">交付审核</h2>
      <span class="text-xs text-gray-400">共 {{ total }} 条待审核</span>
    </div>

    <el-card v-if="loadError && !loading" class="mb-4">
      <div class="text-center py-6">
        <p class="text-sm text-red-500 mb-4">{{ loadError }}</p>
        <el-button type="primary" plain @click="loadDeliveries">重试</el-button>
      </div>
    </el-card>

    <template v-else>
      <el-table :data="deliveries" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="所属商单" min-width="160">
          <template #default="{ row }">
            <el-link type="primary" @click="router.push(`/admin/orders/${row.order_id}`)">{{ row.order }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="creator" label="创作者" width="120" />
        <el-table-column label="交付方式" width="100">
          <template #default="{ row }">
            <el-tag :type="row.delivery_type === 0 ? 'primary' : 'warning'" size="small">
              {{ row.delivery_type === 0 ? '视频' : '外链' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="交付内容" min-width="160">
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
        <el-table-column label="提交时间" width="150">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button size="small" type="success" @click="openReview(row, 'approve')">通过</el-button>
            <el-button size="small" type="danger" @click="openReview(row, 'reject')">驳回</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && !deliveries.length" description="暂无待审核交付" :image-size="60" />

      <el-pagination
        v-if="total > pageSize"
        class="mt-4 justify-end"
        layout="total, prev, pager, next"
        :total="total"
        :current-page="page"
        :page-size="pageSize"
        @current-change="v => { page = v; loadDeliveries() }"
      />
    </template>

    <el-dialog
      v-model="dialogs.visible"
      :title="dialogs.action === 'approve' ? '审核通过' : '审核驳回'"
      width="460px"
    >
      <el-input
        v-model="dialogs.opinion"
        type="textarea"
        :rows="3"
        :placeholder="dialogs.action === 'approve' ? '可填审核意见(选填)' : '请填写驳回意见(必填)'"
      />
      <template #footer>
        <el-button @click="dialogs.visible = false">取消</el-button>
        <el-button type="primary" :loading="dialogs.submitting" @click="confirmReview">确认</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="videoDialog.visible" :title="videoDialog.title" width="720px" destroy-on-close>
      <video v-if="videoDialog.url" controls preload="metadata" :src="videoDialog.url" class="w-full max-h-[60vh] rounded bg-black"></video>
    </el-dialog>
  </div>
</template>
