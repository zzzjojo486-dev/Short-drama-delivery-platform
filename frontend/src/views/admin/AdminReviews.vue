<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getPendingDeliveries, reviewDelivery } from '../../api'

const router = useRouter()
const deliveries = ref([])
const loading = ref(false)

const dialogs = ref({
  visible: false,
  action: '',
  delivery: null,
  opinion: '',
})

async function loadDeliveries() {
  loading.value = true
  try {
    const res = await getPendingDeliveries()
    deliveries.value = res.data.data.deliveries || []
  } catch (e) {
    if (e.response && e.response.status === 403) {
      ElMessage.error('无权限访问后台')
      router.push('/admin/login')
    } else {
      ElMessage.error('加载失败')
    }
  } finally {
    loading.value = false
  }
}

function openReview(delivery, action) {
  dialogs.value = { visible: true, action, delivery, opinion: '' }
}

async function confirmReview() {
  const { action, delivery, opinion } = dialogs.value
  if (action === 'reject' && !opinion.trim()) {
    ElMessage.warning('驳回时请填写审核意见')
    return
  }
  try {
    await reviewDelivery(delivery.id, action, opinion.trim())
    ElMessage.success(action === 'approve' ? '已通过' : '已驳回')
    dialogs.value.visible = false
    loadDeliveries()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '审核失败')
  }
}

onMounted(loadDeliveries)
</script>

<template>
  <div>
    <h2 class="text-lg font-semibold mb-4">交付审核</h2>
    <el-table :data="deliveries" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="order" label="所属商单" />
      <el-table-column prop="creator" label="创作者" width="140" />
      <el-table-column label="交付方式" width="120">
        <template #default="{ row }">
          <el-tag :type="row.delivery_type === 0 ? 'primary' : 'warning'" size="small">
            {{ row.delivery_type === 0 ? '视频' : '链接' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="note" label="交付说明" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" type="success" @click="openReview(row, 'approve')">通过</el-button>
          <el-button size="small" type="danger" @click="openReview(row, 'reject')">驳回</el-button>
        </template>
      </el-table-column>
    </el-table>

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
        <el-button type="primary" @click="confirmReview">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>
