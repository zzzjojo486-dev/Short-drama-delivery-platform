<script setup>
import { useRouter } from 'vue-router'
import { useAdminStore } from '../../stores/admin'

const router = useRouter()
const adminStore = useAdminStore()

function goHome() {
  router.push('/')
}

function logout() {
  // 只清后台会话,不触碰前台登录态
  adminStore.logout()
  router.push('/admin/login')
}
</script>

<template>
  <el-container class="admin-shell">
    <!-- 侧边栏 -->
    <el-aside width="200px" class="admin-aside">
      <div class="admin-brand">短剧交付平台 · 后台</div>
      <el-menu router :default-active="$route.path" class="admin-menu">
        <el-menu-item index="/admin/users">用户管理</el-menu-item>
        <el-menu-item index="/admin/reviews">审核管理</el-menu-item>
        <el-menu-item index="/admin/orders">商单管理</el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- 顶栏 -->
      <el-header class="admin-header">
        <div class="flex items-center gap-4">
          <el-button size="small" @click="goHome">返回前台</el-button>
          <el-button size="small" type="danger" plain @click="logout">退出登录</el-button>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.admin-shell {
  height: 100vh;
}
.admin-aside {
  background: #1f2733;
  color: #fff;
  display: flex;
  flex-direction: column;
}
.admin-brand {
  height: 64px;
  line-height: 64px;
  padding: 0 20px;
  font-weight: 600;
  border-bottom: 1px solid rgba(255,255,255,.08);
}
.admin-menu {
  border-right: none;
  background: #1f2733;
}
.admin-menu :deep(.el-menu-item) {
  color: #cbd5e1;
}
.admin-menu :deep(.el-menu-item.is-active) {
  color: #fff;
  background: #374151;
}
.admin-header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  border-bottom: 1px solid #e5e7eb;
  background: #fff;
}
.admin-main {
  background: #f5f6f8;
}
</style>
