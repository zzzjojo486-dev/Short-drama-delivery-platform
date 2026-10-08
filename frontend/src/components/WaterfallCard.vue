<script setup>
import { getImageUrl } from '../api'
import { ref } from 'vue'

const props = defineProps({
  post: Object,
  showActions: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click', 'delete', 'toggle-privacy'])

const handleDelete = (e) => {
  e.stopPropagation()
  emit('delete', props.post.id)
}

const handleTogglePrivacy = (e) => {
  e.stopPropagation()
  emit('toggle-privacy', props.post.id, !props.post.is_private)
}
</script>

<template>
  <div class="group bg-white rounded-xl overflow-hidden border border-gray-100 mb-4 cursor-pointer hover:-translate-y-1 hover:shadow-lg transition-all duration-300 relative" @click="emit('click', post.id, $event)">
    
    <!-- Private Indicator Overlay -->
    <div v-if="post.is_private" class="absolute top-2 left-2 z-10 bg-black/50 text-white px-2 py-0.5 rounded-full text-xs flex items-center gap-1 backdrop-blur-sm">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-3 h-3">
        <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
      </svg>
      仅自己可见
    </div>

    <!-- Video Indicator -->
    <div v-if="post.video_url" class="absolute top-2 right-2 z-10 w-6 h-6 bg-black/30 text-white rounded-full flex items-center justify-center backdrop-blur-sm">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4">
          <path fill-rule="evenodd" d="M4.5 5.653c0-1.426 1.529-2.33 2.779-1.643l11.54 6.348c1.295.712 1.295 2.573 0 3.285L7.28 19.991c-1.25.687-2.779-.217-2.779-1.643V5.653Z" clip-rule="evenodd" />
        </svg>
    </div>

    <!-- Action Buttons (Visible on Hover if showActions is true) -->
    <div v-if="showActions" class="absolute top-2 right-2 z-20 flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
      <!-- Toggle Privacy Button -->
      <button 
        @click="handleTogglePrivacy"
        class="w-8 h-8 bg-white/90 hover:bg-white text-gray-600 hover:text-xhs-red rounded-full flex items-center justify-center shadow-sm backdrop-blur-sm transition-colors"
        :title="post.is_private ? '设为公开' : '设为私密'"
      >
        <svg v-if="post.is_private" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
          <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
        </svg>
      </button>
      
      <!-- Delete Button -->
      <button 
        @click="handleDelete"
        class="w-8 h-8 bg-white/90 hover:bg-white text-gray-600 hover:text-red-600 rounded-full flex items-center justify-center shadow-sm backdrop-blur-sm transition-colors"
        title="删除笔记"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
          <path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
        </svg>
      </button>
    </div>

    <div class="relative w-full pt-[133%] bg-gray-50">
      <img 
        :src="getImageUrl(post.image_url) || 'https://via.placeholder.com/300x400'" 
        class="absolute top-0 left-0 w-full h-full object-cover transition-transform duration-300"
        loading="lazy"
      >
      <div class="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors"></div>
    </div>
    
    <div class="p-3">
      <h3 class="text-sm font-medium text-gray-900 line-clamp-2 mb-2 leading-snug min-h-[2.5rem]">
        {{ post.title }}
      </h3>
      
      <div class="flex items-center justify-between text-xs text-gray-500">
        <div class="flex items-center gap-1.5 min-w-0">
          <img 
            :src="getImageUrl(post.avatar_url) || 'https://via.placeholder.com/20'" 
            class="w-5 h-5 rounded-full object-cover flex-shrink-0 border border-gray-100"
          >
          <span class="truncate">{{ post.nickname }}</span>
        </div>
        <div class="flex items-center gap-1 flex-shrink-0">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3.5 h-3.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z" />
          </svg>
          <span>{{ post.likes_count }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
