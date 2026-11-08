<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '../../api'
import { useAdminStore } from '../../stores/admin'

const adminStore = useAdminStore()
const router = useRouter()
const form = ref({ username: '', password: '' })
const loading = ref(false)

// 后台角色:0 超管 / 1 运营 / 2 审核员(与后端 STAFF_ROLES 一致)
const STAFF_ROLES = [0, 1, 2]

async function handleSubmit() {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  loading.value = true
  try {
    const res = await login(form.value.username, form.value.password)
    if (res.data.success) {
      const role = res.data.user.role
      if (!STAFF_ROLES.includes(role)) {
        ElMessage.error('该账号无后台权限')
        return
      }
      // 只写 admin 桶,绝不触碰前台的 token
      adminStore.login(res.data.user, res.data.token)
      ElMessage.success('登录成功')
      router.push('/admin/users')
    } else {
      ElMessage.error(res.data.message)
    }
  } catch (e) {
    ElMessage.error('登录失败，请检查网络')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="admin-login">
    <div class="admin-login-card">
      <div class="admin-login-title">短剧交付平台 · 后台管理</div>
      <p class="admin-login-sub">仅限运营/审核人员登录，与前台登录互不影响</p>
      <el-form @submit.prevent="handleSubmit">
        <el-input
          v-model="form.username"
          placeholder="账号"
          size="large"
          class="mb-4"
          :disabled="loading"
        />
        <el-input
          v-model="form.password"
          type="password"
          placeholder="密码"
          size="large"
          show-password
          class="mb-6"
          :disabled="loading"
          @keyup.enter="handleSubmit"
        />
        <el-button
          type="primary"
          size="large"
          class="w-full"
          native-type="submit"
          :loading="loading"
        >
          登录后台
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.admin-login {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1f2733;
}
.admin-login-card {
  width: 100%;
  max-width: 360px;
  background: #fff;
  border-radius: 12px;
  padding: 40px 32px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
}
.admin-login-title {
  font-size: 20px;
  font-weight: 700;
  text-align: center;
  color: #1f2733;
}
.admin-login-sub {
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
  margin: 10px 0 28px;
}
</style>