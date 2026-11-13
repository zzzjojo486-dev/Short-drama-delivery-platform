<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getAdminUsers, updateUserRole } from '../../api'
import { useAdminStore } from '../../stores/admin'

const adminStore = useAdminStore()
const users = ref([])
const loading = ref(false)
const loadError = ref('')

const roleLabels = { 0: '超管', 1: '运营', 2: '审核员', 3: '用户' }

async function loadUsers() {
  loading.value = true
  loadError.value = ''
  try {
    const res = await getAdminUsers()
    users.value = res.data.data.users || []
  } catch (e) {
    loadError.value = e.response?.status === 403 ? '当前角色无权限查看用户列表' : (e.response?.data?.message || '加载失败')
    users.value = []
  } finally {
    loading.value = false
  }
}

async function changeRole(user) {
  try {
    await updateUserRole(user.id, user.role)
    ElMessage.success('角色已更新')
  } catch (e) {
    loadUsers() // 失败时回滚表格显示,错误提示由拦截器弹出
  }
}

onMounted(loadUsers)
</script>

<template>
  <div>
    <h2 class="text-lg font-semibold mb-4">用户管理</h2>
    <el-card v-if="loadError && !loading" class="mb-4">
      <div class="text-center py-6">
        <p class="text-sm text-red-500 mb-4">{{ loadError }}</p>
        <el-button type="primary" plain @click="loadUsers">重试</el-button>
      </div>
    </el-card>
    <el-table v-else :data="users" v-loading="loading" stripe empty-text="暂无用户">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="nickname" label="昵称" />
      <el-table-column label="角色" width="140">
        <template #default="{ row }">
          <el-select v-model="row.role" size="small" :disabled="adminStore.user?.role !== 0" @change="changeRole(row)">
            <el-option v-for="(label, val) in roleLabels" :key="val" :label="label" :value="Number(val)" />
          </el-select>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
