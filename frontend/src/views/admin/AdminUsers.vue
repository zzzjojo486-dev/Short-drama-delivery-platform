<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getAdminUsers, updateUserRole } from '../../api'
import { useAdminStore } from '../../stores/admin'

const router = useRouter()
const adminStore = useAdminStore()
const users = ref([])
const loading = ref(false)

const roleLabels = { 0: '超管', 1: '运营', 2: '审核员', 3: '用户' }

async function loadUsers() {
  loading.value = true
  try {
    const res = await getAdminUsers()
    users.value = res.data.data.users || []
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

async function changeRole(user) {
  try {
    const res = await updateUserRole(user.id, user.role)
    ElMessage.success('角色已更新')
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '更新失败')
    loadUsers() // 失败时回滚表格显示
  }
}

onMounted(loadUsers)
</script>

<template>
  <div>
    <h2 class="text-lg font-semibold mb-4">用户管理</h2>
    <el-table :data="users" v-loading="loading" stripe>
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
