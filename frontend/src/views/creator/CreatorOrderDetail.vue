<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getCreatorOrderDetail, applyCreatorOrder, submitCreatorDelivery, getMediaUrl } from '../../api'
import { ORDER_STATUS, ORDER_STATUS_CLASS, DELIVERY_STATUS, DELIVERY_STATUS_CLASS, DELIVERY_TYPE, formatTime, formatSize } from './meta'

const route = useRoute()
const router = useRouter()
const orderId = computed(() => route.params.id)

const loading = ref(true)
const loadError = ref('')
const order = ref(null)
const flags = ref({ is_applied: false, is_selected: false, can_apply: false, can_deliver: false })
const application = ref(null)
const deliveries = ref([])

const applySection = ref(null)
const deliverSection = ref(null)

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const res = await getCreatorOrderDetail(orderId.value)
    const d = res.data.data
    order.value = d.order
    flags.value = { is_applied: d.is_applied, is_selected: d.is_selected, can_apply: d.can_apply, can_deliver: d.can_deliver }
    application.value = d.application
    deliveries.value = d.deliveries || []
    await nextTick()
    if (route.query.apply && flags.value.can_apply) applySection.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    if (route.query.deliver && flags.value.can_deliver) deliverSection.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  } catch (e) {
    loadError.value = e.response?.data?.message || '加载失败，请重试'
  } finally {
    loading.value = false
  }
}

watch(orderId, load)
onMounted(load)

// ---- 报名 ----
const proposal = ref('')
const applying = ref(false)

async function submitApply() {
  if (applying.value) return
  applying.value = true
  try {
    await applyCreatorOrder(orderId.value, proposal.value.trim())
    ElMessage.success('报名成功，等待运营选中')
    proposal.value = ''
    await load()
  } catch (e) {
    // 失败保留输入,错误提示由拦截器统一弹出
  } finally {
    applying.value = false
  }
}

// ---- 交付 ----
const MAX_VIDEO_BYTES = 1073741824
const deliveryMode = ref('video')
const videoFile = ref(null)
const videoUrl = ref('')
const note = ref('')
const formError = ref('')
const submitting = ref(false)
const uploadPercent = ref(0)
const fileInput = ref(null)

function switchMode(mode) {
  if (submitting.value) return
  deliveryMode.value = mode
  formError.value = ''
}

function pickFile(event) {
  const file = event.target.files[0]
  event.target.value = ''
  if (!file) return
  formError.value = ''
  videoFile.value = null
  if (!/\.mp4$/i.test(file.name)) {
    formError.value = '仅支持 MP4 格式视频'
    return
  }
  if (file.size === 0) {
    formError.value = '视频文件不能为空'
    return
  }
  if (file.size > MAX_VIDEO_BYTES) {
    formError.value = '视频大小不能超过 1GB'
    return
  }
  videoFile.value = file
}

async function submitDelivery() {
  if (submitting.value) return
  formError.value = ''
  if (deliveryMode.value === 'video') {
    if (!videoFile.value) {
      formError.value = '请先选择 MP4 视频文件'
      return
    }
  } else {
    const url = videoUrl.value.trim()
    if (!/^https?:\/\/\S+/i.test(url)) {
      formError.value = '视频外链必须是 http/https 链接'
      return
    }
    if (url.length > 500) {
      formError.value = '视频外链不能超过 500 个字符'
      return
    }
  }
  submitting.value = true
  uploadPercent.value = 0
  try {
    await submitCreatorDelivery(
      orderId.value,
      { mode: deliveryMode.value, file: videoFile.value, url: videoUrl.value.trim(), note: note.value.trim() },
      (evt) => {
        if (evt.total) uploadPercent.value = Math.min(100, Math.round((evt.loaded / evt.total) * 100))
      }
    )
    ElMessage.success('交付已提交，等待审核')
    videoFile.value = null
    videoUrl.value = ''
    note.value = ''
    uploadPercent.value = 0
    await load()
  } catch (e) {
    // 失败保留已填内容,可直接重试
  } finally {
    submitting.value = false
  }
}

// ---- 展示派生(仅用于文案/历史展示,按钮显隐只用后端四个标志) ----
const hasPending = computed(() => deliveries.value.some(d => d.status === 0))
const hasApproved = computed(() => deliveries.value.some(d => d.status === 1))
const latestReturned = computed(() => deliveries.value.find(d => d.status === 2))
const returnedOpinion = computed(() => {
  const reviews = latestReturned.value?.reviews || []
  for (let i = reviews.length - 1; i >= 0; i--) {
    if (reviews[i].action === 2) return reviews[i].opinion
  }
  return ''
})
</script>

<template>
  <div class="max-w-3xl mx-auto px-4 py-6">
    <button class="flex items-center gap-1 text-sm text-gray-400 hover:text-gray-700 mb-4" @click="router.push('/orders')">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
        <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
      </svg>
      返回商单列表
    </button>

    <!-- 失败态 -->
    <div v-if="loadError && !loading" class="bg-white rounded-2xl border border-red-100 p-10 text-center">
      <p class="text-sm text-xhs-red mb-4">{{ loadError }}</p>
      <div class="flex justify-center gap-3">
        <button class="px-6 py-2 bg-xhs-red text-white rounded-full text-sm font-medium hover:bg-red-600" @click="load">重试</button>
        <button class="px-6 py-2 bg-gray-50 text-gray-600 rounded-full text-sm font-medium hover:bg-gray-100" @click="router.push('/orders')">返回列表</button>
      </div>
    </div>

    <!-- 加载态 -->
    <div v-else-if="loading" class="space-y-4">
      <div v-for="i in 3" :key="i" class="bg-white rounded-2xl border border-gray-100 p-6 animate-pulse">
        <div class="h-6 bg-gray-100 rounded w-1/2 mb-4"></div>
        <div class="h-4 bg-gray-50 rounded w-full mb-2"></div>
        <div class="h-4 bg-gray-50 rounded w-3/4"></div>
      </div>
    </div>

    <template v-else-if="order">
      <!-- 商单信息 -->
      <section class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-4">
        <div class="flex items-start justify-between gap-3 mb-3">
          <h1 class="text-xl font-bold text-gray-900">{{ order.title }}</h1>
          <span class="shrink-0 text-xs px-2.5 py-1 rounded-full font-medium" :class="ORDER_STATUS_CLASS[order.status]">{{ ORDER_STATUS[order.status] }}</span>
        </div>
        <div class="flex items-center gap-2 text-xs mb-4 flex-wrap">
          <span v-if="order.category" class="px-2 py-0.5 rounded-full bg-gray-50 text-gray-500 border border-gray-100">{{ order.category }}</span>
          <span class="text-xhs-red font-semibold text-sm">预算 {{ order.budget || '面议' }}</span>
          <span class="text-gray-300">·</span>
          <span class="text-gray-400">发布于 {{ formatTime(order.created) }}</span>
        </div>
        <div class="space-y-3 text-sm">
          <div v-if="order.brief">
            <h3 class="text-gray-400 text-xs mb-1">商单简介</h3>
            <p class="text-gray-700 whitespace-pre-wrap">{{ order.brief }}</p>
          </div>
          <div v-if="order.requirement">
            <h3 class="text-gray-400 text-xs mb-1">交付要求</h3>
            <p class="text-gray-700 whitespace-pre-wrap">{{ order.requirement }}</p>
          </div>
        </div>
      </section>

      <!-- 我的报名 -->
      <section ref="applySection" class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-4">
        <h2 class="font-semibold text-gray-900 mb-3">我的报名</h2>
        <template v-if="application">
          <div class="flex items-center gap-2 mb-2">
            <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="flags.is_selected ? 'bg-emerald-500 text-white' : 'bg-blue-500 text-white'">
              {{ flags.is_selected ? '已入选' : '已报名，等待选中' }}
            </span>
            <span class="text-xs text-gray-400">{{ formatTime(application.created_at) }}</span>
          </div>
          <p class="text-sm text-gray-600 whitespace-pre-wrap">{{ application.proposal || '未填写报名说明' }}</p>
        </template>
        <template v-else-if="flags.can_apply">
          <textarea
            v-model="proposal"
            :disabled="applying"
            maxlength="2000"
            rows="4"
            placeholder="介绍你的交付能力、档期与思路（选填，2000 字以内）"
            class="w-full rounded-xl border border-gray-100 bg-gray-50 focus:bg-white focus:border-xhs-red focus:outline-none p-3 text-sm transition-colors resize-y"
          ></textarea>
          <div class="flex items-center justify-between mt-2">
            <span class="text-xs text-gray-300">{{ proposal.length }} / 2000</span>
            <button
              class="px-6 py-2 bg-xhs-red text-white rounded-full text-sm font-medium hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              :disabled="applying"
              @click="submitApply"
            >{{ applying ? '报名中…' : '提交报名' }}</button>
          </div>
        </template>
        <p v-else class="text-sm text-gray-400">当前商单暂不可报名</p>
      </section>

      <!-- 退回提醒 -->
      <section v-if="latestReturned && flags.can_deliver" class="bg-red-50 border border-red-100 rounded-2xl p-4 mb-4">
        <p class="text-sm text-xhs-red font-medium mb-1">交付被退回，请修改后重新提交</p>
        <p v-if="returnedOpinion" class="text-sm text-red-400 whitespace-pre-wrap">审核意见：{{ returnedOpinion }}</p>
      </section>

      <!-- 提交交付 -->
      <section v-if="flags.can_deliver" ref="deliverSection" class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-4">
        <h2 class="font-semibold text-gray-900 mb-3">提交交付</h2>
        <div class="flex gap-2 mb-4">
          <button
            class="px-4 py-1.5 rounded-full text-sm font-medium transition-colors"
            :class="deliveryMode === 'video' ? 'bg-xhs-red text-white' : 'bg-gray-50 text-gray-500 hover:bg-gray-100'"
            :disabled="submitting"
            @click="switchMode('video')"
          >上传视频</button>
          <button
            class="px-4 py-1.5 rounded-full text-sm font-medium transition-colors"
            :class="deliveryMode === 'link' ? 'bg-xhs-red text-white' : 'bg-gray-50 text-gray-500 hover:bg-gray-100'"
            :disabled="submitting"
            @click="switchMode('link')"
          >视频外链</button>
        </div>

        <!-- 视频模式 -->
        <div v-if="deliveryMode === 'video'">
          <input ref="fileInput" type="file" accept=".mp4,video/mp4" class="hidden" :disabled="submitting" @change="pickFile">
          <button
            v-if="!videoFile"
            class="w-full rounded-xl border-2 border-dashed border-gray-200 hover:border-xhs-red bg-gray-50 hover:bg-red-50 transition-colors p-6 text-center disabled:opacity-50"
            :disabled="submitting"
            @click="fileInput.click()"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.2" stroke="currentColor" class="w-10 h-10 mx-auto text-gray-300 mb-2">
              <path stroke-linecap="round" stroke-linejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
            </svg>
            <p class="text-sm text-gray-500 font-medium">点击选择 MP4 视频</p>
            <p class="text-xs text-gray-400 mt-1">仅支持 .mp4，大小不超过 1GB</p>
          </button>
          <div v-else class="flex items-center justify-between rounded-xl border border-gray-100 bg-gray-50 px-4 py-3">
            <div class="flex items-center gap-2 min-w-0">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-xhs-red shrink-0">
                <path stroke-linecap="round" stroke-linejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
              </svg>
              <span class="text-sm text-gray-700 truncate">{{ videoFile.name }}</span>
              <span class="text-xs text-gray-400 shrink-0">{{ formatSize(videoFile.size) }}</span>
            </div>
            <button class="text-xs text-gray-400 hover:text-xhs-red shrink-0 ml-3" :disabled="submitting" @click="videoFile = null">移除</button>
          </div>
          <!-- 真实上传进度 -->
          <div v-if="submitting && deliveryMode === 'video'" class="mt-3">
            <div class="h-2 rounded-full bg-gray-100 overflow-hidden">
              <div class="h-full bg-xhs-red rounded-full transition-all duration-200" :style="{ width: uploadPercent + '%' }"></div>
            </div>
            <p class="text-xs text-gray-400 mt-1">
              {{ uploadPercent < 100 ? `上传中 ${uploadPercent}%` : '上传完成，服务器处理中…' }}
            </p>
          </div>
        </div>

        <!-- 外链模式 -->
        <div v-else>
          <input
            v-model="videoUrl"
            :disabled="submitting"
            type="url"
            maxlength="500"
            placeholder="https:// 视频外链地址"
            class="w-full h-11 px-4 rounded-xl border border-gray-100 bg-gray-50 focus:bg-white focus:border-xhs-red focus:outline-none text-sm transition-colors"
          >
          <p class="text-xs text-gray-400 mt-1">支持 http/https 链接，500 字符以内</p>
        </div>

        <textarea
          v-model="note"
          :disabled="submitting"
          rows="3"
          maxlength="500"
          placeholder="交付说明（选填）"
          class="w-full rounded-xl border border-gray-100 bg-gray-50 focus:bg-white focus:border-xhs-red focus:outline-none p-3 text-sm transition-colors resize-y mt-3"
        ></textarea>

        <p v-if="formError" class="text-xs text-xhs-red mt-2">{{ formError }}</p>
        <div class="flex justify-end mt-3">
          <button
            class="px-6 py-2 bg-xhs-red text-white rounded-full text-sm font-medium hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            :disabled="submitting"
            @click="submitDelivery"
          >{{ submitting ? '提交中…' : '提交交付' }}</button>
        </div>
      </section>

      <!-- 不可交付时的状态说明 -->
      <section v-else class="rounded-2xl p-4 mb-4 text-sm"
        :class="hasApproved ? 'bg-emerald-50 text-emerald-600' : hasPending ? 'bg-amber-50 text-amber-600' : 'bg-gray-50 text-gray-400'">
        <template v-if="hasApproved">交付已审核通过，无需重复提交</template>
        <template v-else-if="hasPending">已有待审核交付，审核完成前无需重复提交</template>
        <template v-else-if="order.status === 5">商单已完成</template>
        <template v-else-if="order.status === 6">商单已关闭</template>
        <template v-else-if="flags.is_selected">等待商单进入进行中后即可提交交付</template>
        <template v-else>报名并被选中后即可提交交付</template>
      </section>

      <!-- 交付历史 -->
      <section class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <h2 class="font-semibold text-gray-900 mb-4">我的交付历史</h2>
        <div v-if="!deliveries.length" class="text-center py-8">
          <p class="text-sm text-gray-400">暂无交付记录</p>
        </div>
        <div v-else class="space-y-4">
          <article v-for="d in deliveries" :key="d.id" class="rounded-xl border border-gray-100 p-4">
            <div class="flex items-center gap-2 flex-wrap mb-2">
              <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="d.delivery_type === 0 ? 'bg-blue-50 text-blue-600' : 'bg-amber-50 text-amber-600'">
                {{ DELIVERY_TYPE[d.delivery_type] }}
              </span>
              <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="DELIVERY_STATUS_CLASS[d.status]">{{ DELIVERY_STATUS[d.status] }}</span>
              <span class="text-xs text-gray-400 ml-auto">{{ formatTime(d.created_at) }}</span>
            </div>
            <p v-if="d.note" class="text-sm text-gray-600 whitespace-pre-wrap mb-3">{{ d.note }}</p>
            <!-- 视频:video_file 播放(后端支持 Range) -->
            <video
              v-if="d.delivery_type === 0 && d.video_file"
              controls
              preload="metadata"
              :src="getMediaUrl(d.video_file)"
              class="w-full max-h-[420px] rounded-xl bg-black mb-3"
            ></video>
            <!-- 外链:新窗口打开 -->
            <a
              v-else-if="d.delivery_type === 1 && d.video_url"
              :href="d.video_url"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-1.5 text-sm text-blue-600 hover:underline mb-3 break-all"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 shrink-0">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
              </svg>
              {{ d.video_url }}
            </a>
            <!-- 审核意见 -->
            <div v-if="(d.reviews || []).length" class="border-t border-gray-50 pt-3 space-y-2">
              <div v-for="r in d.reviews" :key="r.id" class="flex items-start gap-2 text-sm">
                <span class="shrink-0 text-xs px-2 py-0.5 rounded-full font-medium mt-0.5" :class="r.action === 1 ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-xhs-red'">
                  {{ r.action === 1 ? '通过' : '退回' }}
                </span>
                <div class="min-w-0">
                  <p class="text-gray-600 whitespace-pre-wrap">{{ r.opinion || '无审核意见' }}</p>
                  <p class="text-xs text-gray-300 mt-0.5">{{ formatTime(r.created_at) }}</p>
                </div>
              </div>
            </div>
          </article>
        </div>
      </section>
    </template>
  </div>
</template>