<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { getConversations, getNotifications, markNotificationsRead, getImageUrl } from '../api'
import moment from 'moment'
import 'moment/dist/locale/zh-cn'

moment.locale('zh-cn')

const userStore = useUserStore()
const router = useRouter()
const conversations = ref([])
const notifications = ref([])
const loading = ref(true)
const activeTab = ref('messages') // 'messages' or 'notifications'

const fetchConversations = async () => {
  if (!userStore.user) return
  try {
    const res = await getConversations(userStore.user.id)
    conversations.value = res.data.conversations
  } catch (e) {
    console.error(e)
  }
}

const fetchNotifications = async () => {
  if (!userStore.user) return
  try {
    const res = await getNotifications(userStore.user.id)
    notifications.value = res.data.notifications
    
    // Mark as read immediately when fetching (simple strategy)
    // Or we could do it when tab is switched
    if (notifications.value.some(n => !n.is_read)) {
        await markNotificationsRead(userStore.user.id)
    }
  } catch (e) {
    console.error(e)
  }
}

const loadData = async () => {
    loading.value = true
    await Promise.all([fetchConversations(), fetchNotifications()])
    loading.value = false
}

const formatTime = (timestamp) => {
  return moment(timestamp).fromNow()
}

const goToChat = (userId) => {
  router.push(`/messages/${userId}`)
}

const goToPost = (postId) => {
    if (postId) {
        router.push(`/messages/post/${postId}`)
    }
}

const switchTab = (tab) => {
    activeTab.value = tab
    if (tab === 'notifications') {
        // Refresh notifications and mark read
        fetchNotifications()
    }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="container mx-auto px-4 py-4 md:py-8 max-w-2xl">
    <div class="flex gap-6 mb-4 md:mb-6 border-b border-gray-100">
        <button 
            class="pb-3 px-2 font-bold text-lg transition-colors border-b-2"
            :class="activeTab === 'messages' ? 'text-gray-900 border-xhs-red' : 'text-gray-400 border-transparent hover:text-gray-600'"
            @click="switchTab('messages')"
        >
            消息列表
        </button>
        <button 
            class="pb-3 px-2 font-bold text-lg transition-colors border-b-2 relative"
            :class="activeTab === 'notifications' ? 'text-gray-900 border-xhs-red' : 'text-gray-400 border-transparent hover:text-gray-600'"
            @click="switchTab('notifications')"
        >
            通知
            <!-- Red dot for unread notifications could be added here if we had separate counts -->
        </button>
    </div>
    
    <div v-if="loading" class="text-center py-10 text-gray-500">加载中...</div>
    
    <!-- Messages Tab -->
    <div v-else-if="activeTab === 'messages'">
        <div v-if="conversations.length === 0" class="text-center py-20 text-gray-400 bg-white rounded-xl border border-gray-100">
          还没有消息哦
        </div>
        
        <div v-else class="bg-white rounded-xl border border-gray-100 divide-y divide-gray-50">
          <div 
            v-for="conv in conversations" 
            :key="conv.user.id"
            class="p-4 flex items-center gap-4 hover:bg-gray-50 cursor-pointer transition-colors"
            @click="goToChat(conv.user.id)"
          >
            <div class="relative">
              <img 
                :src="getImageUrl(conv.user.avatar_url) || 'https://via.placeholder.com/50'" 
                class="w-12 h-12 rounded-full object-cover border border-gray-200"
              >
              <div v-if="conv.unread_count > 0" class="absolute -top-1 -right-1 w-5 h-5 bg-xhs-red text-white text-xs flex items-center justify-center rounded-full border-2 border-white">
                {{ conv.unread_count > 99 ? '99+' : conv.unread_count }}
              </div>
            </div>
            
            <div class="flex-1 min-w-0">
              <div class="flex justify-between items-baseline mb-1">
                <h3 class="font-medium text-gray-900 truncate">{{ conv.user.nickname }}</h3>
                <span class="text-xs text-gray-400 flex-shrink-0">{{ formatTime(conv.timestamp) }}</span>
              </div>
              <p class="text-sm text-gray-500 truncate">{{ conv.last_message.content }}</p>
            </div>
          </div>
        </div>
    </div>

    <!-- Notifications Tab -->
    <div v-else-if="activeTab === 'notifications'">
        <div v-if="notifications.length === 0" class="text-center py-20 text-gray-400 bg-white rounded-xl border border-gray-100">
          还没有通知哦
        </div>
        
        <div v-else class="bg-white rounded-xl border border-gray-100 divide-y divide-gray-50">
          <div 
            v-for="note in notifications" 
            :key="note.id"
            class="p-4 flex items-start gap-4 hover:bg-gray-50 cursor-pointer transition-colors"
            @click="goToPost(note.target_id)"
          >
            <!-- Sender Avatar -->
             <img 
                :src="getImageUrl(note.sender_avatar) || 'https://via.placeholder.com/40'" 
                class="w-10 h-10 rounded-full object-cover border border-gray-200 flex-shrink-0"
              >
            
            <div class="flex-1 min-w-0">
                <div class="flex justify-between items-baseline mb-1">
                    <h3 class="font-medium text-gray-900 text-sm">{{ note.sender_name }}</h3>
                    <span class="text-xs text-gray-400 flex-shrink-0">{{ formatTime(note.created_at) }}</span>
                </div>
                <p class="text-sm text-gray-600">
                    <span v-if="note.type === 'like_post'">赞了你的帖子</span>
                    <span v-else>{{ note.content }}</span>
                </p>
            </div>

            <!-- Post Thumbnail -->
            <div v-if="note.post_image" class="w-12 h-12 flex-shrink-0 rounded overflow-hidden border border-gray-100 bg-gray-50">
                <img :src="getImageUrl(note.post_image)" class="w-full h-full object-cover">
            </div>
            <div v-else-if="note.post_title" class="w-12 h-12 flex-shrink-0 rounded overflow-hidden border border-gray-100 bg-gray-50 flex items-center justify-center text-[10px] text-gray-400 text-center p-1 leading-tight">
                {{ note.post_title.substring(0, 4) }}
            </div>

          </div>
        </div>
    </div>

    <!-- Router View for Post Modal -->
    <router-view v-slot="{ Component }">
      <transition name="modal-fade">
        <component :is="Component" />
      </transition>
    </router-view>

  </div>
</template>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>