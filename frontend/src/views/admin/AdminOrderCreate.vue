<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createAdminOrder, updateAdminOrder, getAdminOrderDetail } from '../../api'

const router = useRouter()
const route = useRoute()
const editing = ref(false)
const loading = ref(false)
const saving = ref(false)

const form = ref({ title: '', brief: '', requirement: '', category: '', budget: '' })

async function loadForEdit() {
  const id = route.query.id
  if (!id) return
  editing.value = true
  loading.value = true
  try {
    const res = await getAdminOrderDetail(id)
    const d = res.data.data.order
    form.value = {
      title: d.title || '',
      brief: d.brief || '',
      requirement: d.requirement || '',
      category: d.category || '',
      budget: d.budget || '',
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!form.value.title.trim()) {
    ElMessage.warning('标题必填')
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      await updateAdminOrder(route.query.id, form.value)
      ElMessage.success('已保存')
    } else {
      await createAdminOrder(form.value)
      ElMessage.success('创建成功，已进入草稿列表')
    }
    router.push('/admin/orders')
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(loadForEdit)
</script>

<template>
  <div>
    <h2 class="text-lg font-semibold mb-4">{{ editing ? '编辑商单' : '创建商单' }}</h2>
    <el-card v-loading="loading">
      <el-form label-width="90px" :model="form">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" placeholder="商单标题" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.brief" type="textarea" :rows="2" placeholder="需求秒速" />
        </el-form-item>
        <el-form-item label="交付要求">
          <el-input v-model="form.requirement" type="textarea" :rows="4" placeholder="交付要求" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="form.category" placeholder="分类" maxlength="32" />
        </el-form-item>
        <el-form-item label="预算">
          <el-input v-model="form.budget" placeholder="预算（仅展示不结算）" maxlength="32" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存</el-button>
          <el-button @click="router.push('/admin/orders')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>