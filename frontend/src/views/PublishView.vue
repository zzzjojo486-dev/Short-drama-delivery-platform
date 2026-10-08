<script setup>
import { ref } from 'vue'
import { createPost, aiPolishStream } from '../api'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

// 'image' or 'video'
const publishType = ref('image')

// Image Mode
const fileInput = ref(null)
const previewUrls = ref([])
const files = ref([])

// Video Mode
const videoInput = ref(null)
const coverInput = ref(null)
const videoFile = ref(null)
const videoPreviewUrl = ref('')
const coverFile = ref(null)
const coverPreviewUrl = ref('')

const categories = ["穿搭", "美食", "彩妆", "影视", "职场", "情感", "家居", "游戏", "旅行", "健身"]

const form = ref({
  title: '',
  content: '',
  category: '穿搭'
})

const isPolishing = ref(false)
const lastContent = ref('') // Backup for revert

const handleRevert = () => {
  if (lastContent.value) {
    form.value.content = lastContent.value
    lastContent.value = ''
    ElMessage.success('已撤销')
  }
}

const handleAIPolish = async () => {
  if (!form.value.content && !form.value.title) {
    ElMessage.warning('请先填写标题或正文')
    return
  }
  
  isPolishing.value = true
  const originalContent = form.value.content 
  lastContent.value = originalContent // Save for Revert
  
  form.value.content = '' // Clear content to show streaming result
  
  // 组合标题和正文作为上下文
  const textToPolish = [form.value.title, originalContent].filter(t => t).join('\n\n')

  await aiPolishStream(
    textToPolish,
    (chunk) => {
      form.value.content += chunk
    },
    (error) => {
      console.error(error)
      ElMessage.error('AI 润色失败: ' + error)
      if (!form.value.content) {
          form.value.content = originalContent // Restore if nothing was generated
          lastContent.value = '' // Reset revert backup if restored automatically
      }
      isPolishing.value = false
    }
  )
  isPolishing.value = false
  ElMessage.success('AI 润色完成！')
}

// --- Image Mode Handlers ---
const handleFileChange = (e) => {
  const selectedFiles = Array.from(e.target.files)
  if (selectedFiles.length > 0) {
    files.value = [...files.value, ...selectedFiles]
    const newPreviews = selectedFiles.map(file => ({
        url: URL.createObjectURL(file),
        file: file
    }))
    previewUrls.value = [...previewUrls.value, ...newPreviews]
  }
}

const removeImage = (index) => {
    files.value.splice(index, 1)
    previewUrls.value.splice(index, 1)
}

const triggerUpload = () => {
  fileInput.value.click()
}

// --- Video Mode Handlers ---
const triggerVideoUpload = () => {
    videoInput.value.click()
}

const triggerCoverUpload = () => {
    coverInput.value.click()
}

const handleVideoChange = (e) => {
    const file = e.target.files[0]
    if (file) {
        if (file.size > 500 * 1024 * 1024) {
            ElMessage.warning('视频大小不能超过500MB')
            return
        }
        videoFile.value = file
        videoPreviewUrl.value = URL.createObjectURL(file)
    }
}

const handleCoverChange = (e) => {
    const file = e.target.files[0]
    if (file) {
        coverFile.value = file
        coverPreviewUrl.value = URL.createObjectURL(file)
    }
}

const removeVideo = () => {
    videoFile.value = null
    videoPreviewUrl.value = ''
}

const removeCover = () => {
    coverFile.value = null
    coverPreviewUrl.value = ''
}

// --- Submit ---
const handleSubmit = async () => {
  const formData = new FormData()
  formData.append('user_id', userStore.user.id)
  formData.append('title', form.value.title)
  formData.append('content', form.value.content)
  formData.append('category', form.value.category)

  if (publishType.value === 'image') {
      if (files.value.length === 0) {
        ElMessage.warning('请至少上传一张图片')
        return
      }
      files.value.forEach(file => {
        formData.append('images', file)
      })
  } else {
      // Video Mode
      if (!videoFile.value) {
          ElMessage.warning('请上传视频')
          return
      }
      if (!coverFile.value) {
          ElMessage.warning('请上传视频封面')
          return
      }
      formData.append('video', videoFile.value)
      // Cover is treated as the first image in backend logic (create_post checks image_urls[0] as cover)
      formData.append('images', coverFile.value)
  }
  
  try {
    const res = await createPost(formData)
    if (res.data.success) {
      ElMessage.success('发布成功')
      router.push('/')
    } else {
      ElMessage.error(res.data.message)
    }
  } catch (e) {
    ElMessage.error('发布失败: ' + (e.response?.data?.detail || e.message))
  }
}
</script>

<template>
  <div class="max-w-5xl mx-auto p-4 md:p-6 flex flex-col md:flex-row gap-6 md:gap-8">
    <!-- Left: Upload Area -->
    <div class="w-full md:w-1/3 flex-shrink-0 flex flex-col gap-4">
        <!-- Tabs -->
        <div class="flex gap-6 px-2">
            <button 
                @click="publishType = 'image'" 
                class="text-base font-medium transition-colors relative py-2"
                :class="publishType === 'image' ? 'text-gray-900' : 'text-gray-400 hover:text-gray-600'"
            >
                上传图文
                <div v-if="publishType === 'image'" class="absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-1 bg-xhs-red rounded-full"></div>
            </button>
            <button 
                @click="publishType = 'video'" 
                class="text-base font-medium transition-colors relative py-2"
                :class="publishType === 'video' ? 'text-gray-900' : 'text-gray-400 hover:text-gray-600'"
            >
                上传视频
                <div v-if="publishType === 'video'" class="absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-1 bg-xhs-red rounded-full"></div>
            </button>
        </div>

        <!-- Image Upload UI -->
        <div v-if="publishType === 'image'" class="space-y-4">
            <div 
                v-if="previewUrls.length === 0"
                class="aspect-[3/4] bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200 flex flex-col items-center justify-center cursor-pointer hover:border-xhs-red hover:bg-red-50 transition-all overflow-hidden relative group"
                @click="triggerUpload"
            >
                <div class="text-center p-4 text-gray-400 group-hover:text-xhs-red">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-10 h-10 mx-auto mb-2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
                    </svg>
                    <span class="text-sm font-medium">点击上传图片</span>
                </div>
            </div>

            <div v-else class="grid grid-cols-2 gap-2">
                <div 
                    v-for="(item, index) in previewUrls" 
                    :key="index" 
                    class="relative aspect-[3/4] rounded-lg overflow-hidden group"
                >
                    <img :src="item.url" class="w-full h-full object-cover">
                    <button 
                        @click.stop="removeImage(index)"
                        class="absolute top-1 right-1 bg-black/50 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
                <div 
                    class="aspect-[3/4] bg-gray-50 rounded-lg border-2 border-dashed border-gray-200 flex items-center justify-center cursor-pointer hover:border-xhs-red hover:bg-red-50 transition-all"
                    @click="triggerUpload"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8 text-gray-400">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                    </svg>
                </div>
            </div>
            <input ref="fileInput" type="file" accept="image/*" multiple class="hidden" @change="handleFileChange">
            <p class="text-xs text-gray-400 text-center">支持多图上传，第一张将作为封面</p>
        </div>

        <!-- Video Upload UI -->
        <div v-else class="space-y-4">
            <!-- Video Uploader -->
            <div 
                v-if="!videoFile"
                class="aspect-[3/4] bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200 flex flex-col items-center justify-center cursor-pointer hover:border-xhs-red hover:bg-red-50 transition-all overflow-hidden group"
                @click="triggerVideoUpload"
            >
                <div class="text-center p-4 text-gray-400 group-hover:text-xhs-red">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-10 h-10 mx-auto mb-2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
                    </svg>
                    <span class="text-sm font-medium">点击上传视频</span>
                    <p class="text-xs mt-1 opacity-60">支持 mp4, mov, webm</p>
                </div>
            </div>
            <div v-else class="relative aspect-[3/4] bg-black rounded-2xl overflow-hidden group">
                <video :src="videoPreviewUrl" class="w-full h-full object-contain" controls></video>
                <button 
                    @click.stop="removeVideo"
                    class="absolute top-2 right-2 bg-black/50 text-white rounded-full p-1.5 hover:bg-black/70 transition-colors"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Cover Uploader -->
            <div class="space-y-2">
                <label class="text-sm font-medium text-gray-700">视频封面 (必填)</label>
                <div 
                    v-if="!coverFile"
                    class="aspect-video bg-gray-50 rounded-lg border-2 border-dashed border-gray-200 flex items-center justify-center cursor-pointer hover:border-xhs-red hover:bg-red-50 transition-all h-32 w-full"
                    @click="triggerCoverUpload"
                >
                    <span class="text-xs text-gray-400">点击上传封面图</span>
                </div>
                <div v-else class="relative aspect-video h-32 w-full rounded-lg overflow-hidden group">
                    <img :src="coverPreviewUrl" class="w-full h-full object-cover">
                    <button 
                        @click.stop="removeCover"
                        class="absolute top-1 right-1 bg-black/50 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3 h-3">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
            </div>
            
            <input ref="videoInput" type="file" accept="video/mp4,video/quicktime,video/webm" class="hidden" @change="handleVideoChange">
            <input ref="coverInput" type="file" accept="image/*" class="hidden" @change="handleCoverChange">
        </div>
    </div>

    <!-- Right: Form -->
    <div class="w-full md:flex-1 space-y-6 md:mt-14">
      <input 
        v-model="form.title"  
        type="text" 
        placeholder="填写标题会有更多人赞哦~" 
        class="w-full text-xl font-bold border border-gray-200 rounded-lg py-2 px-3 focus:border-xhs-red focus:outline-none transition-colors placeholder-gray-300"
      >
      
      <div class="relative">
        <textarea 
          v-model="form.content" 
          placeholder="填写更全面的描述信息，让更多人看到你吧！" 
          class="w-full h-60 resize-none text-gray-600 border border-gray-200 rounded-lg focus:border-xhs-red focus:outline-none placeholder-gray-300 text-base leading-relaxed p-3 transition-colors"
        ></textarea>
        
        <div class="absolute bottom-4 right-4 flex gap-2">
          <button 
            v-if="lastContent && !isPolishing"
            @click="handleRevert"
            class="flex items-center gap-1.5 px-3 py-1.5 bg-white/90 backdrop-blur text-gray-500 text-sm font-medium rounded-full shadow-sm border border-gray-200 hover:bg-gray-50 hover:text-gray-700 transition-all"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3" />
            </svg>
            <span>撤回</span>
          </button>

          <button 
            @click="handleAIPolish"
            :disabled="isPolishing"
            class="flex items-center gap-1.5 px-3 py-1.5 bg-white/90 backdrop-blur text-xhs-red text-sm font-medium rounded-full shadow-sm border border-red-100 hover:bg-red-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg v-if="isPolishing" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4">
              <path fill-rule="evenodd" d="M9.315 7.584C12.195 3.883 16.695 1.5 21.75 1.5a.75.75 0 01.75.75c0 5.056-2.383 9.555-6.084 12.436h.004c-.14.44-.584 1.259-1.344 2.02-.978.977-2.155 1.729-3.305 2.052l-.214.06-1.238 2.475a.75.75 0 01-1.341 0l-1.238-2.475-.214-.06c-1.15-.323-2.327-1.075-3.305-2.052C2.492 14.93 1.33 11.558 3.292 6.99a.75.75 0 011.133-.605c.94.659 1.674 1.272 2.203 1.839.49.524.89 1.142 1.192 1.836.484-.73 1.058-1.43 1.72-2.051.58-.542 1.18-1.05 1.796-1.516l-.221-.09-.001.001zM8.03 8.688a10.28 10.28 0 00-1.047 1.835l-.072.178a.75.75 0 01-1.286.065 8.78 8.78 0 00-.675-.892c-1.183 2.12-1.31 3.748-.935 4.864.32.954.96 1.778 1.73 2.55.55.55 1.137.952 1.697 1.198l.294.13a.75.75 0 01.288.995l-.744 1.487 1.487-.744a.75.75 0 01.995.288l.13.294c.246.56.648 1.146 1.198 1.697.772.77 1.596 1.41 2.55 1.73 1.116.374 2.744.248 4.864-.935-.287-.21-.587-.434-.892-.675a.75.75 0 01.065-1.286l.178-.072a10.28 10.28 0 001.835-1.047 20.81 20.81 0 01-8.695-8.695z" clip-rule="evenodd" />
            </svg>
            <span>AI 润色</span>
          </button>
        </div>
      </div>
      
      <div class="space-y-2">
        <label class="text-sm font-medium text-gray-700">选择分类</label>
        <div class="flex flex-wrap gap-2">
          <button 
            v-for="cat in categories" 
            :key="cat"
            type="button"
            @click="form.category = cat"
            class="px-3 py-1 text-xs rounded-full border transition-all"
            :class="form.category === cat ? 'border-xhs-red text-xhs-red bg-red-50' : 'border-gray-200 text-gray-500 hover:border-gray-300'"
          >
            {{ cat }}
          </button>
        </div>
      </div>
      
      <div class="pt-4 border-t border-gray-100">
        <button @click="handleSubmit" class="w-32 h-10 bg-xhs-red text-white rounded-full font-medium hover:bg-red-600 transition-colors shadow-sm">
          {{ publishType === 'image' ? '发布笔记' : '发布视频' }}
        </button>
      </div>
    </div>
  </div>
</template>