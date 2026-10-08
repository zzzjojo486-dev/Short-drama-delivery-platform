<script setup>
import { ref } from 'vue'
import { useUserStore } from '../stores/user'
import { login, register } from '../api'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const isLogin = ref(true)
const router = useRouter()
const userStore = useUserStore()
const agree = ref(false)
const fileInput = ref(null)
const avatarFile = ref(null)
const avatarPreview = ref(null)

const form = ref({
  username: '',
  password: '',
  nickname: ''
})

const triggerFileInput = () => {
  fileInput.value.click()
}

const handleFileChange = (event) => {
  const file = event.target.files[0]
  if (file) {
    if (file.size > 5 * 1024 * 1024) {
      ElMessage.warning('图片大小不能超过 5MB')
      return
    }
    avatarFile.value = file
    avatarPreview.value = URL.createObjectURL(file)
  }
}

const handleSubmit = async () => {
  if (!agree.value) {
    ElMessage.warning('请阅读并勾选《用户协议》与《隐私政策》')
    return
  }
  
  // 注册时必须上传头像
  if (!isLogin.value && !avatarFile.value) {
    ElMessage.warning('请上传头像')
    return
  }
  
  try {
    if (isLogin.value) {
      const res = await login(form.value.username, form.value.password)
      if (res.data.success) {
        userStore.login(res.data.user)
        ElMessage.success('登录成功')
        router.push('/')
      } else {
        ElMessage.error(res.data.message)
      }
    } else {
      const res = await register(form.value.username, form.value.password, form.value.nickname, avatarFile.value)
      if (res.data.success) {
        ElMessage.success('注册成功，请登录')
        isLogin.value = true
        // Reset form
        form.value = { username: '', password: '', nickname: '' }
        avatarFile.value = null
        avatarPreview.value = null
      } else {
        ElMessage.error(res.data.message)
      }
    }
  } catch (e) {
    ElMessage.error('操作失败，请检查网络')
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-white px-4">
    <!-- Login Card -->
    <div class="w-full max-w-[400px] bg-white">
      <!-- Header Logo -->
      <div class="flex justify-center mb-10">
        <img src="/logo2.png" alt="Logo" class="h-12 w-auto object-contain" />
      </div>

      <div class="px-4">
        <h2 class="text-2xl font-medium text-center mb-8 text-[#333]">
          {{ isLogin ? '用户名登录' : '注册账号' }}
        </h2>
        
        <!-- Avatar Upload for Register -->
        <div v-if="!isLogin" class="flex flex-col items-center mb-6">
          <div class="relative group cursor-pointer" @click="triggerFileInput">
            <div class="w-20 h-20 rounded-full bg-gray-50 flex items-center justify-center overflow-hidden border transition-colors" :class="avatarPreview ? 'border-gray-200 hover:border-xhs-red' : 'border-xhs-red border-2'">
              <img v-if="avatarPreview" :src="avatarPreview" class="w-full h-full object-cover" />
              <div v-else class="flex flex-col items-center justify-center text-gray-400">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span class="text-[10px]">上传头像</span>
              </div>
            </div>
            <div v-if="avatarPreview" class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 rounded-full transition-all duration-200 flex items-center justify-center pointer-events-none">
              <span class="text-xs text-transparent group-hover:text-white font-medium">更换</span>
            </div>
          </div>
          <input type="file" ref="fileInput" class="hidden" accept="image/*" @change="handleFileChange">
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <input 
              v-model="form.username" 
              type="text" 
              :placeholder="isLogin ? '手机号 / 邮箱 / 用户名' : '设置用户名'" 
              class="w-full h-12 px-6 bg-gray-50 rounded-full border border-transparent focus:bg-white focus:border-xhs-red focus:outline-none transition-all placeholder-gray-400 text-[15px]" 
              required
            >
          </div>
          <div>
            <input 
              v-model="form.password" 
              type="password" 
              :placeholder="isLogin ? '输入密码' : '设置密码'" 
              class="w-full h-12 px-6 bg-gray-50 rounded-full border border-transparent focus:bg-white focus:border-xhs-red focus:outline-none transition-all placeholder-gray-400 text-[15px]" 
              required
            >
          </div>
          <div v-if="!isLogin">
            <input 
              v-model="form.nickname" 
              type="text" 
              placeholder="设置昵称 (可选)" 
              class="w-full h-12 px-6 bg-gray-50 rounded-full border border-transparent focus:bg-white focus:border-xhs-red focus:outline-none transition-all placeholder-gray-400 text-[15px]"
            >
          </div>
          
          <button 
            type="submit" 
            class="w-full h-12 bg-xhs-red text-white rounded-full font-semibold hover:bg-red-600 active:scale-[0.98] transition-all text-[16px] shadow-sm mt-4 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ isLogin ? '登录' : '注册' }}
          </button>

          <!-- Agreement -->
          <div class="flex items-start mt-4 text-xs text-gray-400 justify-center">
            <div 
              class="flex-shrink-0 w-4 h-4 mr-1.5 rounded-full border cursor-pointer flex items-center justify-center transition-colors"
              :class="agree ? 'bg-xhs-red border-xhs-red' : 'border-gray-300'"
              @click="agree = !agree"
            >
              <svg v-if="agree" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-3 h-3 text-white">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
            </div>
            <div class="leading-relaxed select-none" @click="agree = !agree">
              我已阅读并同意
              <a href="#" class="text-gray-800 font-medium hover:underline" @click.stop>《用户协议》</a>
              <a href="#" class="text-gray-800 font-medium hover:underline" @click.stop>《隐私政策》</a>
              <a href="#" class="text-gray-800 font-medium hover:underline" @click.stop>《儿童/青少年个人信息保护规则》</a>
            </div>
          </div>
        </form>
        
        <!-- Switch Mode -->
        <div class="mt-4 text-center text-sm text-gray-500">
          {{ isLogin ? '还没有账号？' : '已有账号？' }}
          <button @click="isLogin = !isLogin; agree = false; avatarFile = null; avatarPreview = null" class="text-xhs-red font-medium hover:underline ml-1">
            {{ isLogin ? '去注册' : '去登录' }}
          </button>
        </div>

        <!-- Social Login (Only show on Login) -->
        <div v-if="isLogin" class="mt-12">
          <div class="relative">
            <div class="absolute inset-0 flex items-center">
              <div class="w-full border-t border-gray-100"></div>
            </div>
            <div class="relative flex justify-center text-xs">
              <span class="px-2 bg-white text-gray-400">其他登录方式</span>
            </div>
          </div>

          <div class="flex justify-center gap-8 mt-6">
            <!-- WeChat -->
            <button class="p-2 rounded-full bg-gray-50 hover:bg-gray-100 transition-colors cursor-not-allowed opacity-60" title="暂未开放">
              <svg class="w-6 h-6 text-[#07C160]" viewBox="0 0 24 24" fill="currentColor">
                <path d="M8.5,16.5c0-3,2.5-5.5,5.5-5.5c3,0,5.5,2.5,5.5,5.5s-2.5,5.5-5.5,5.5C11,22,8.5,19.5,8.5,16.5z M14,16.5 c0-1.9-1.6-3.5-3.5-3.5S7,14.6,7,16.5s1.6,3.5,3.5,3.5S14,18.4,14,16.5z M5.5,7.5C5.5,4.5,8,2,11,2s5.5,2.5,5.5,5.5S14,13,11,13 S5.5,10.5,5.5,7.5z M11,7.5c0-1.9-1.6-3.5-3.5-3.5S4,5.6,4,7.5s1.6,3.5,3.5,3.5S11,9.4,11,7.5z"/>
                <path d="M17.5,12c-2.5,0-4.5-1.8-4.5-4c0-2.2,2-4,4.5-4c2.5,0,4.5,1.8,4.5,4C22,10.2,20,12,17.5,12z M16.3,9.2 c0.4,0,0.8-0.4,0.8-0.8c0-0.4-0.4-0.8-0.8-0.8c-0.4,0-0.8,0.4-0.8,0.8C15.5,8.9,15.9,9.2,16.3,9.2z M18.7,9.2 c0.4,0,0.8-0.4,0.8-0.8c0-0.4-0.4-0.8-0.8-0.8s-0.8,0.4-0.8,0.8C17.9,8.9,18.3,9.2,18.7,9.2z"/>
                <path d="M7.8,13C4.6,13,2,10.8,2,8c0-2.8,2.6-5,5.8-5c3.2,0,5.8,2.2,5.8,5c0,2.8-2.6,5-5.8,5c-0.6,0-1.2-0.1-1.8-0.2 L4.5,14l0.4-1.7C3.5,11.5,2,9.8,2,8"/>
              </svg>
            </button>
            <!-- QQ -->
            <button class="p-2 rounded-full bg-gray-50 hover:bg-gray-100 transition-colors cursor-not-allowed opacity-60" title="暂未开放">
              <svg class="w-6 h-6 text-[#12B7F5]" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12,2C6.5,2,2,6.5,2,12s4.5,10,10,10s10-4.5,10-10S17.5,2,12,2z M12,18.5c-3.6,0-6.5-2.9-6.5-6.5S8.4,5.5,12,5.5 s6.5,2.9,6.5,6.5S15.6,18.5,12,18.5z"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Custom checkbox styling logic handled in template with utility classes */
</style>










