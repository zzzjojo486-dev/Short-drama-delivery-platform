<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { getConversation, sendMessage, markMessagesRead, getPublicUserProfile, getImageUrl } from '../api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const targetUser = ref(null)
const messages = ref([])
const newMessage = ref('')
const loading = ref(true)
const messagesContainer = ref(null)
const pollingInterval = ref(null)
const showEmojiPicker = ref(false)
const emojiPickerRef = ref(null)
const emojiButtonRef = ref(null)

const handleClickOutside = (event) => {
  if (showEmojiPicker.value && 
      emojiPickerRef.value && 
      !emojiPickerRef.value.contains(event.target) && 
      emojiButtonRef.value && 
      !emojiButtonRef.value.contains(event.target)) {
    showEmojiPicker.value = false
  }
}

const emojis = [
  '😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣', '☺️', '😊',
  '😇', '🙂', '🙃', '😉', '😌', '😍', '🥰', '😘', '😗', '😙',
  '😚', '😋', '😛', '😝', '😜', '🤪', '🤨', '🧐', '🤓', '😎',
  '🤩', '🥳', '😏', '😒', '😞', '😔', '😟', '😕', '🙁', '☹️',
  '😣', '😖', '😫', '😩', '🥺', '😢', '😭', '😤', '😠', '😡',
  '🤯', '😳', '🥵', '🥶', '😱', '😨', '😰', '😥', '😓', '🤗',
  '🤔', '🤭', '🤫', '🤥', '😶', '😐', '😑', '😬', '🙄', '😯',
  '😴', '🤤', '😪', '😵', '🤐', '🥴', '🤢', '🤮', '🤧', '😷',
  '👋', '🤚', '🖐', '✋', '🖖', '👌', '🤏', '✌️', '🤞', '🤟',
  '🤘', '🤙', '👈', '👉', '👆', '🖕', '👇', '☝️', '👍', '👎',
  '✊', '👊', '🤛', '🤜', '👏', '🙌', '👐', '🤲', '🤝', '🙏',
  '💅', '🤳', '💪', '🦾', '🦿', '🦵', '🦶', '👂', '🦻', '👃',
  '🧠', '🫀', '🫁', '🦷', '🦴', '👀', '👁', '👅', '👄', '💋',
  '👶', '👧', '🧒', '👦', '👩', '🧑', '👨', '👱‍♀️', '👱‍♂️', '🧔',
  '🌹', '🥀', '🌺', '🌻', '🌼', '🌷', '🌱', '🌿', '🍀', '🍁',
  '🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨', '🐯',
  '❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔'
]

const addEmoji = (emoji) => {
  newMessage.value += emoji
}

const targetUserId = route.params.id

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const fetchMessages = async () => {
  if (!userStore.user) return
  try {
    const res = await getConversation(targetUserId, userStore.user.id)
    // If new messages arrived, update and scroll
    if (res.data.messages.length !== messages.value.length || (messages.value.length > 0 && res.data.messages[res.data.messages.length-1].id !== messages.value[messages.value.length-1].id)) {
        messages.value = res.data.messages
        scrollToBottom()
        // Mark as read if last message is from them
        if (messages.value.length > 0) {
            const lastMsg = messages.value[messages.value.length - 1]
            if (lastMsg.sender_id == targetUserId && !lastMsg.is_read) {
                 await markMessagesRead(userStore.user.id, targetUserId)
            }
        }
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const fetchTargetUser = async () => {
  try {
    const res = await getPublicUserProfile(targetUserId)
    targetUser.value = res.data.user
  } catch (e) {
    ElMessage.error('用户不存在')
    router.push('/messages')
  }
}

const handleSend = async () => {
  if (!newMessage.value.trim()) return
  
  try {
    const content = newMessage.value
    newMessage.value = '' // Optimistic clear
    
    const res = await sendMessage(userStore.user.id, targetUserId, content)
    if (res.data.success) {
      await fetchMessages()
    } else {
      ElMessage.error(res.data.message || '发送失败')
      newMessage.value = content // Restore on fail
    }
  } catch (e) {
    ElMessage.error('发送失败')
  }
}

const formatTime = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
}

const shouldShowTimestamp = (index) => {
  if (index === 0) return true
  
  const currentMsg = messages.value[index]
  const prevMsg = messages.value[index - 1]
  
  if (!currentMsg.created_at || !prevMsg.created_at) return false
  
  const currentTime = new Date(currentMsg.created_at).getTime()
  const prevTime = new Date(prevMsg.created_at).getTime()
  
  // Show if difference is more than 1 minute (60000 ms)
  return (currentTime - prevTime) > 60000
}

onMounted(async () => {
  if (!userStore.user) {
      router.push('/login')
      return
  }
  await fetchTargetUser()
  await fetchMessages()
  
  // Simple polling for new messages every 3 seconds
  pollingInterval.value = setInterval(fetchMessages, 3000)
  
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  if (pollingInterval.value) clearInterval(pollingInterval.value)
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="flex justify-center h-full bg-gray-100 md:py-4" style="box-sizing: border-box;">
    <div class="flex flex-col w-full max-w-5xl bg-gray-50 h-full md:shadow-lg md:rounded-xl overflow-hidden md:border border-gray-200" style="max-height: 100%;">
      <!-- Header -->
      <div class="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3 flex-shrink-0">
        <button @click="router.back()" class="text-gray-500 hover:text-gray-700">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
          </svg>
        </button>
        <div v-if="targetUser" class="flex items-center gap-2 cursor-pointer" @click="router.push(`/user/${targetUser.id}`)">
          <img :src="getImageUrl(targetUser.avatar_url) || 'https://via.placeholder.com/40'" class="w-8 h-8 rounded-full object-cover">
          <span class="font-medium text-gray-900">{{ targetUser.nickname }}</span>
        </div>
      </div>

      <!-- Messages -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4" ref="messagesContainer">
        <div v-if="loading" class="text-center text-gray-400 text-sm py-4">加载中...</div>
        
        <div v-for="(msg, index) in messages" :key="msg.id">
          <div v-if="shouldShowTimestamp(index)" class="flex justify-center mb-4">
              <span class="text-xs text-gray-500 bg-gray-50 px-3 py-1 rounded-full shadow-sm border border-gray-100">{{ formatTime(msg.created_at) }}</span>
          </div>
          <div 
              class="flex gap-3"
              :class="msg.sender_id === userStore.user.id ? 'flex-row-reverse' : ''"
          >
              <img 
                  :src="getImageUrl(msg.sender_id === userStore.user.id ? userStore.user.avatar_url : targetUser?.avatar_url) || 'https://via.placeholder.com/40'" 
                  class="w-9 h-9 rounded-full object-cover flex-shrink-0 bg-white border border-gray-100"
              >
              
              <div 
              class="max-w-[70%] px-4 py-2.5 rounded-2xl text-sm break-words"
              :class="msg.sender_id === userStore.user.id 
                  ? 'bg-xhs-red text-white rounded-tr-none' 
                  : 'bg-white text-gray-800 border border-gray-100 rounded-tl-none'"
              >
              {{ msg.content }}
              </div>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div class="bg-white border-t border-gray-200 p-4 flex-shrink-0" @click.self="showEmojiPicker = false">
        <div class="flex gap-3 relative">
          <!-- Emoji Picker -->
          <transition name="emoji-fade">
            <div ref="emojiPickerRef" v-if="showEmojiPicker" class="absolute bottom-full right-16 mb-4 bg-white rounded-xl shadow-[0_0_20px_rgba(0,0,0,0.1)] border border-gray-100 p-4 w-80 grid grid-cols-8 gap-2 h-64 overflow-y-auto z-50 custom-scrollbar">
                <button 
                  v-for="emoji in emojis" 
                  :key="emoji" 
                  @click="addEmoji(emoji)" 
                  class="text-2xl hover:bg-gray-50 rounded-lg p-1 transition-colors flex items-center justify-center aspect-square"
                >
                  {{ emoji }}
                </button>
            </div>
          </transition>

          <div class="flex-1 relative">
            <input 
              v-model="newMessage"
              type="text" 
              class="w-full bg-gray-100 rounded-full pl-4 pr-12 py-2.5 text-sm focus:bg-white focus:ring-1 focus:ring-xhs-red focus:outline-none transition-all"
              placeholder="发私信..."
              @keyup.enter="handleSend"
              @focus="showEmojiPicker = false"
            >
            <button 
              ref="emojiButtonRef"
              @click="showEmojiPicker = !showEmojiPicker" 
              class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors p-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.182 15.182a4.5 4.5 0 0 1-6.364 0M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0ZM9.75 9.75c0 .414-.168.75-.375.75S9 10.164 9 9.75 9.168 9 9.375 9s.375.336.375.75Zm-.375 0h.008v.015h-.008V9.75Zm5.625 0c0 .414-.168.75-.375.75s-.375-.336-.375-.75.168-.75.375-.75.375.336.375.75Zm-.375 0h.008v.015h-.008V9.75Z" />
              </svg>
            </button>
          </div>
          
          <button 
            @click="handleSend"
            class="bg-xhs-red text-white px-5 py-2 rounded-full text-sm font-medium hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex-shrink-0"
            :disabled="!newMessage.trim()"
          >
            发送
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #e5e7eb;
  border-radius: 20px;
}

.emoji-fade-enter-active,
.emoji-fade-leave-active {
  transition: all 0.2s ease;
}

.emoji-fade-enter-from,
.emoji-fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>

