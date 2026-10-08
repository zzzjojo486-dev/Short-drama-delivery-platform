<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getPostDetail, getComments, addComment, toggleLike, toggleCollection, getImageUrl, followUser, unfollowUser, checkIsFollowing, toggleCommentLike } from '../api'
import { useUserStore } from '../stores/user'
import { useTransitionStore } from '../stores/transition'
import { ElMessage } from 'element-plus'
import html2canvas from 'html2canvas'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const transitionStore = useTransitionStore()
const post = ref(null)
const comments = ref([])
const newComment = ref('')
const isLiked = ref(false)
const isCollected = ref(false)
const isFollowing = ref(false)
const containerRef = ref(null)
const isLoading = ref(true)

// Animation states
const isAnimating = ref(false)
const initialRect = transitionStore.selectedImgRect
const initialSrc = transitionStore.selectedImgSrc
const placeholderImg = ref(initialSrc)
const showContent = ref(false)

// Styles for animation
const animStyle = ref({})

// Share states
const showShareModal = ref(false)
const shareCardRef = ref(null)
const generatedImage = ref('')
const isGenerating = ref(false)

// Full Screen Image Viewer states
const isFullScreen = ref(false)
const scale = ref(1)
const translateX = ref(0)
const translateY = ref(0)
const isDragging = ref(false)
const startX = ref(0)
const startY = ref(0)

// Carousel states
const currentImageIndex = ref(0)
const autoPlayInterval = ref(null)

const currentImage = computed(() => {
    if (!post.value) return ''
    // If images array exists and is not empty, use it
    if (post.value.images && post.value.images.length > 0) {
        return post.value.images[currentImageIndex.value]
    }
    // Fallback to legacy single image
    return post.value.image_url
})

const imageList = computed(() => {
    if (!post.value) return []
    if (post.value.images && post.value.images.length > 0) {
        return post.value.images
    }
    return [post.value.image_url].filter(Boolean)
})

const nextImage = () => {
    if (imageList.value.length <= 1) return
    currentImageIndex.value = (currentImageIndex.value + 1) % imageList.value.length
}

const prevImage = () => {
    if (imageList.value.length <= 1) return
    currentImageIndex.value = (currentImageIndex.value - 1 + imageList.value.length) % imageList.value.length
}

const startAutoPlay = () => {
    stopAutoPlay()
    if (imageList.value.length > 1) {
        autoPlayInterval.value = setInterval(nextImage, 3000) // 3s
    }
}

const stopAutoPlay = () => {
    if (autoPlayInterval.value) {
        clearInterval(autoPlayInterval.value)
        autoPlayInterval.value = null
    }
}

const openFullScreen = () => {
  isFullScreen.value = true
  scale.value = 1
  translateX.value = 0
  translateY.value = 0
  stopAutoPlay() // Stop auto play when fullscreen
}

const closeFullScreen = () => {
  isFullScreen.value = false
  startAutoPlay() // Resume auto play
}

const handleWheel = (e) => {
  e.preventDefault()
  const delta = e.deltaY > 0 ? 0.9 : 1.1
  const newScale = scale.value * delta
  if (newScale >= 0.5 && newScale <= 5) {
    scale.value = newScale
  }
}

const startDrag = (e) => {
  e.preventDefault()
  isDragging.value = true
  startX.value = e.clientX - translateX.value
  startY.value = e.clientY - translateY.value
}

const onDrag = (e) => {
  if (!isDragging.value) return
  e.preventDefault()
  translateX.value = e.clientX - startX.value
  translateY.value = e.clientY - startY.value
}

const stopDrag = () => {
  isDragging.value = false
}

const fullScreenImageStyle = computed(() => ({
  transform: `translate(${translateX.value}px, ${translateY.value}px) scale(${scale.value})`,
  cursor: isDragging.value ? 'grabbing' : 'grab',
  transition: isDragging.value ? 'none' : 'transform 0.1s ease-out'
}))

const isLoggedIn = computed(() => !!userStore.user)

onMounted(async () => {
  // Debug log
  console.log('PostDetailView mounted, route params:', route.params)
  
  await loadPostData()
})

onUnmounted(() => {
  document.body.style.overflow = ''
  stopAutoPlay()
})

// Listen to route changes to reload data if ID changes
watch(() => [route.params.id, route.params.postId], ([newId, newPostId]) => {
    const id = newId || newPostId
    console.log('Route params changed:', { newId, newPostId, resolvedId: id })
    if (id) loadPostData()
})

const loadPostData = async () => {
  stopAutoPlay()
  currentImageIndex.value = 0
  const currentPostId = route.params.id || route.params.postId
  console.log('Loading post data for ID:', currentPostId)

  if (!currentPostId) {
    console.error('No post ID found', route.params)
    // Don't redirect back immediately, let user see error
    ElMessage.error('帖子ID无效')
    isLoading.value = false
    return
  }

  // Reset state
  post.value = null
  showContent.value = false
  isLoading.value = true

  try {
    if (initialRect) {
      isAnimating.value = true
      // Initialize animation with placeholder if available
      animStyle.value = {
        position: 'fixed',
        top: `${initialRect.top}px`,
        left: `${initialRect.left}px`,
        width: `${initialRect.width}px`,
        height: `${initialRect.height}px`,
        transition: 'all 0.4s cubic-bezier(0.2, 0, 0.2, 1)',
        zIndex: 100,
        borderRadius: '0px',
        objectFit: 'cover'
      }
      
      // Start animation immediately using placeholder
      await nextTick()
      setTimeout(() => {
          const windowWidth = window.innerWidth
          const windowHeight = window.innerHeight
          const modalWidth = Math.min(windowWidth, 1152)
          const modalHeight = windowHeight * 0.85
          const imgWidth = windowWidth >= 768 ? modalWidth * 0.6 : modalWidth
          const imgHeight = modalHeight
          const targetLeft = windowWidth >= 768 ? (windowWidth - modalWidth) / 2 : 0
          const targetTop = (windowHeight - modalHeight) / 2
          
          animStyle.value = {
            position: 'fixed',
            top: `${targetTop}px`,
            left: `${targetLeft}px`,
            width: `${imgWidth}px`,
            height: `${imgHeight}px`,
            transition: 'all 0.3s cubic-bezier(0.2, 0, 0.2, 1)',
            zIndex: 100,
            borderRadius: '1.5rem 0 0 1.5rem',
            objectFit: 'contain',
            backgroundColor: '#ffffff'
          }
      }, 50)
    }
    
    const userId = userStore.user ? userStore.user.id : null
    console.log('Fetching details from API...')
    const postRes = await getPostDetail(currentPostId, userId)
    console.log('API Response:', postRes)
    
    if (!postRes || !postRes.data) {
      throw new Error('No data returned')
    }
    
    console.log('Post data loaded successfully', postRes.data)
    post.value = postRes.data
    
    // Start auto play if multiple images
    startAutoPlay()
    
    isLiked.value = !!post.value.is_liked
    isCollected.value = !!post.value.is_collected
    
    if (userStore.user && post.value.user_id !== userStore.user.id) {
       try {
         const followRes = await checkIsFollowing(post.value.user_id, userStore.user.id)
         isFollowing.value = followRes.data.is_following
       } catch (e) {
         console.error('Check follow failed', e)
       }
    }
    
    fetchComments(currentPostId)

    if (initialRect) {
       // Animation already started, just finish it when data is ready
        setTimeout(() => {
        isAnimating.value = false
        // showContent.value = true
        transitionStore.setRect(null)
        }, 350) // Wait for animation to complete
    } else {
        // If no animation, just ensure content is shown
        console.log('No initial animation, showing content directly')
        await nextTick()
        // showContent.value = true
        isAnimating.value = false // Ensure animation state is off
    }

  } catch (e) {
    console.error('加载笔记失败:', e)
    ElMessage.error('加载失败，请重试')
  } finally {
    console.log('Setting isLoading to false')
    isLoading.value = false
  }
}

const fetchComments = async (pid) => {
  const id = pid || post.value?.id
  if (!id) return
  try {
    // Pass user ID if logged in
    const userId = userStore.user ? userStore.user.id : null
    const res = await getComments(id, userId)
    comments.value = res.data
  } catch (e) {
    console.error(e)
  }
}

const handleCommentLike = async (comment) => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    return
  }
  
  try {
    const res = await toggleCommentLike(comment.id, userStore.user.id)
    if (res.data.success) {
        comment.is_liked = !comment.is_liked
        comment.likes_count = (comment.likes_count || 0) + (comment.is_liked ? 1 : -1)
    } else {
        ElMessage.error(res.data.message)
    }
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleFollow = async () => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  
  try {
    const res = await followUser(post.value.user_id, userStore.user.id)
    if (res.data.success) {
      isFollowing.value = true
      ElMessage.success('关注成功')
    } else {
      ElMessage.error(res.data.message)
    }
  } catch (e) {
    ElMessage.error('关注失败')
  }
}

const handleUnfollow = async () => {
  try {
    const res = await unfollowUser(post.value.user_id, userStore.user.id)
    if (res.data.success) {
      isFollowing.value = false
      ElMessage.success('已取消关注')
    } else {
      ElMessage.error(res.data.message)
    }
  } catch (e) {
    ElMessage.error('取消关注失败')
  }
}

const handleLike = async () => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    return
  }
  const currentPostId = route.params.id || route.params.postId
  if (!currentPostId) return
  try {
    const res = await toggleLike(currentPostId, userStore.user.id)
    if (res.data.success) {
      isLiked.value = !isLiked.value
      post.value.likes_count += isLiked.value ? 1 : -1
      ElMessage.success(isLiked.value ? '点赞成功' : '已取消点赞')
    }
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleCollect = async () => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    return
  }
  const currentPostId = route.params.id || route.params.postId
  if (!currentPostId) return
  try {
    const res = await toggleCollection(currentPostId, userStore.user.id)
    if (res.data.success) {
      isCollected.value = !isCollected.value
      ElMessage.success(isCollected.value ? '收藏成功' : '已取消收藏')
    }
  } catch (e) {
    ElMessage.error('操作失败')
  }
}


const handleShare = async () => {
  showShareModal.value = true
  isGenerating.value = true
  generatedImage.value = ''
  
  // Allow DOM to render the hidden card
  await nextTick()
  
  // Small delay to ensure image loaded
  setTimeout(async () => {
    if (shareCardRef.value) {
      try {
        const canvas = await html2canvas(shareCardRef.value, {
          useCORS: true,
          scale: 2, // Higher quality
          backgroundColor: '#ffffff',
        })
        generatedImage.value = canvas.toDataURL('image/jpeg', 0.9)
      } catch (e) {
        console.error('Generation failed', e)
        ElMessage.error('生成分享图失败')
      } finally {
        isGenerating.value = false
      }
    }
  }, 500)
}

const downloadImage = () => {
  if (!generatedImage.value) return
  const currentPostId = route.params.id || route.params.postId || 'unknown'
  const link = document.createElement('a')
  link.href = generatedImage.value
  link.download = `xhs-share-${currentPostId}.jpg`
  link.click()
}

const handleComment = async () => {
  if (!newComment.value.trim()) return
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    return
  }
  const currentPostId = route.params.id || route.params.postId
  if (!currentPostId) return
  try {
    const res = await addComment(currentPostId, userStore.user.id, newComment.value)
    if (res.data.success) {
      ElMessage.success('评论成功')
      newComment.value = ''
      fetchComments()
    }
  } catch (e) {
    ElMessage.error('评论失败')
  }
}

const closeDetail = () => {
  router.back()
}
</script>

<template>
  <!-- Modal Overlay -->
  <div class="fixed inset-0 z-[60] bg-white md:bg-black/40 md:flex md:items-center md:justify-center md:p-10 overflow-y-auto md:overflow-hidden custom-scrollbar" @click.self="closeDetail">
    
    <div v-if="isLoading" class="absolute inset-0 flex items-center justify-center z-[70]">
        <div class="animate-spin rounded-full h-10 w-10 border-4 border-gray-200 border-t-xhs-red md:border-white/20 md:border-t-white"></div>
    </div>

    <!-- Full Screen Image Viewer -->
    <div v-if="isFullScreen" 
         class="fixed inset-0 z-[100] bg-black flex items-center justify-center overflow-hidden group"
         @click.self="closeFullScreen"
         @wheel="handleWheel"
    >
      <!-- Controls -->
      <div class="absolute top-4 right-4 flex gap-4 z-[101]">
         <div class="bg-black/50 text-white px-3 py-1 rounded-full text-sm backdrop-blur-sm select-none pointer-events-none flex items-center justify-center">
            {{ Math.round(scale * 100) }}%
         </div>
         <button @click="closeFullScreen" class="w-10 h-10 bg-white/10 hover:bg-white/20 text-white rounded-full flex items-center justify-center backdrop-blur-md transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-6 h-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
         </button>
      </div>

      <!-- Navigation Buttons (Fullscreen) -->
      <button 
        v-if="imageList.length > 1"
        @click.stop="prevImage" 
        class="absolute left-4 top-1/2 -translate-y-1/2 w-12 h-12 bg-black/20 hover:bg-black/40 text-white rounded-full flex items-center justify-center backdrop-blur-sm transition-colors z-[102]"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-6 h-6">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
        </svg>
      </button>

      <button 
        v-if="imageList.length > 1"
        @click.stop="nextImage" 
        class="absolute right-4 top-1/2 -translate-y-1/2 w-12 h-12 bg-black/20 hover:bg-black/40 text-white rounded-full flex items-center justify-center backdrop-blur-sm transition-colors z-[102]"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-6 h-6">
          <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
        </svg>
      </button>


      <img 
        :src="getImageUrl(currentImage)" 
        class="max-w-none select-none transition-all duration-300"
        :style="fullScreenImageStyle"
        @mousedown="startDrag"
        @mousemove="onDrag"
        @mouseup="stopDrag"
        @mouseleave="stopDrag"
        draggable="false"
      />
      
      <!-- Indicators (Fullscreen) -->
      <div class="absolute bottom-8 left-1/2 -translate-x-1/2 flex gap-2 z-[102]" v-if="imageList.length > 1">
        <div 
            v-for="(_, idx) in imageList" 
            :key="idx"
            class="w-2 h-2 rounded-full transition-all"
            :class="idx === currentImageIndex ? 'bg-white w-4' : 'bg-white/40 hover:bg-white/60'"
            @click.stop="currentImageIndex = idx"
        ></div>
      </div>

    </div>

    <!-- Share Modal -->
    <div v-if="showShareModal" class="fixed inset-0 bg-black/60 z-[80] flex items-center justify-center p-4" @click.self="showShareModal = false">
      <div class="bg-white rounded-2xl overflow-hidden max-w-sm w-full flex flex-col max-h-[90vh]">
        <div class="p-4 border-b border-gray-100 flex justify-between items-center">
          <h3 class="text-lg font-medium">分享给好友</h3>
          <button @click="showShareModal = false" class="text-gray-400 hover:text-gray-600">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div class="p-6 flex-1 overflow-y-auto flex flex-col items-center justify-center bg-gray-50">
          <div v-if="isGenerating" class="flex flex-col items-center text-gray-500">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-xhs-red mb-2"></div>
            <p>生成分享卡片中...</p>
          </div>
          <img v-else-if="generatedImage" :src="generatedImage" class="w-full rounded-lg shadow-md object-contain max-h-[60vh]" />
        </div>
        
        <div class="p-4 border-t border-gray-100">
          <button 
            @click="downloadImage"
            :disabled="!generatedImage"
            class="w-full py-2.5 bg-xhs-red text-white rounded-full font-medium hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M12 12.75l-3-3m0 0 3-3m-3 3h7.5" />
            </svg>
            保存到本地
          </button>
        </div>
      </div>
    </div>

    <!-- Invisible Render Container for Share Card -->
    <div class="fixed left-[-9999px] top-0" v-if="showShareModal">
      <div ref="shareCardRef" class="w-[375px] bg-white p-5 flex flex-col gap-4">
        <!-- Header -->
        <div class="flex items-center gap-2">
          <img :src="getImageUrl(post?.avatar_url) || 'https://via.placeholder.com/40'" class="w-8 h-8 rounded-full object-cover" crossOrigin="anonymous">
          <span class="text-sm font-medium text-gray-900">{{ post?.nickname }}</span>
        </div>
        
        <!-- Main Image -->
        <div class="rounded-xl overflow-hidden aspect-[4/3] bg-gray-50 relative">
           <div 
            class="w-full h-full bg-cover bg-center bg-no-repeat"
            :style="{ backgroundImage: `url(${getImageUrl(currentImage)})` }"
          ></div>
        </div>
        
        <!-- Content -->
        <div>
          <h1 class="text-lg font-bold text-gray-900 mb-2">{{ post?.title }}</h1>
          <p class="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">{{ post?.content }}</p>
        </div>
        
        <!-- Footer -->
        <div class="flex items-center justify-between pt-4 border-t border-gray-100 mt-2">
          <div class="flex items-center gap-1">
            <!-- <img src="/logo2.png" class="h-4 object-contain"> -->
            <span class="text-xs text-gray-400">小红书 - 你的生活指南</span>
          </div>
          <div class="text-xs text-gray-300">长按识别二维码</div>
        </div>
      </div>
    </div>

    <!-- Close Button -->
    <button @click="closeDetail" class="absolute top-4 left-4 w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-md hover:bg-gray-100 transition-colors z-[70]">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5 text-gray-600">
        <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
      </svg>
    </button>

    <!-- Floating Image for Animation -->
    <img 
      v-if="isAnimating"
      :src="getImageUrl(post?.image_url) || placeholderImg || 'https://via.placeholder.com/600x800'"
      :style="animStyle"
      class="pointer-events-none shadow-2xl"
    />

    <!-- Detail Card -->
    <div v-if="post" 
      class="w-full max-w-6xl bg-white md:h-[85vh] md:rounded-3xl md:overflow-hidden flex flex-col md:flex-row md:shadow-2xl min-h-full md:min-h-0"
    >
      
      <!-- Left: Image Carousel or Video Player -->
      <div class="w-full md:h-full md:w-[60%] bg-black flex items-center justify-center relative overflow-hidden group/image z-10 flex-shrink-0"
           :class="{'opacity-0': isAnimating}"
           @mouseenter="stopAutoPlay"
           @mouseleave="startAutoPlay"
      >
        <!-- Video Player -->
        <div v-if="post.video_url" class="w-full h-auto aspect-[3/4] md:aspect-auto md:h-full flex items-center justify-center bg-black">
            <video 
                :src="getImageUrl(post.video_url)" 
                controls 
                autoplay 
                class="max-w-full max-h-full w-full h-full object-contain"
                :poster="getImageUrl(post.image_url)"
            ></video>
        </div>

        <!-- Image Carousel -->
        <div v-else class="w-full h-auto aspect-[3/4] md:aspect-auto md:h-full flex items-center justify-center bg-gray-100 relative">
           <transition name="fade" mode="out-in">
             <img 
              :key="currentImage"
              :src="getImageUrl(currentImage) || 'https://via.placeholder.com/600x800'" 
              class="max-w-full max-h-full object-contain cursor-zoom-in transition-transform duration-300 group-hover/image:scale-[1.02]"
              @click="openFullScreen"
            >
           </transition>
           
           <div class="absolute inset-0 flex items-center justify-center pointer-events-none opacity-0 group-hover/image:opacity-100 transition-opacity duration-300">
              <div class="bg-black/50 text-white px-3 py-1.5 rounded-full text-sm backdrop-blur-sm flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
                  <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607ZM10.5 7.5v6m3-3h-6" />
                </svg>
                查看大图
              </div>
           </div>

           <!-- Navigation Buttons -->
           <button 
             v-if="imageList.length > 1"
             @click.stop="prevImage"
             class="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 bg-black/20 hover:bg-black/40 text-white rounded-full flex items-center justify-center backdrop-blur-sm transition-colors opacity-0 group-hover/image:opacity-100"
           >
             <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-5 h-5">
               <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
             </svg>
           </button>

           <button 
             v-if="imageList.length > 1"
             @click.stop="nextImage"
             class="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 bg-black/20 hover:bg-black/40 text-white rounded-full flex items-center justify-center backdrop-blur-sm transition-colors opacity-0 group-hover/image:opacity-100"
           >
             <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-5 h-5">
               <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
             </svg>
           </button>

           <!-- Indicators -->
           <div class="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-1.5" v-if="imageList.length > 1">
             <div 
                v-for="(_, idx) in imageList" 
                :key="idx"
                class="w-1.5 h-1.5 rounded-full transition-all cursor-pointer shadow-sm"
                :class="idx === currentImageIndex ? 'bg-white w-3' : 'bg-white/50 hover:bg-white/80'"
                @click.stop="currentImageIndex = idx"
             ></div>
           </div>

        </div>
      </div>

      <!-- Right: Content & Interaction -->
      <div 
        class="w-full md:w-[40%] flex flex-col bg-white md:h-full transition-all duration-500 transform relative z-0"
        :class="isAnimating ? '-translate-x-full opacity-0' : 'translate-x-0 opacity-100'"
      >
        <!-- Header: Author -->
        <div class="p-5 border-b border-gray-50 flex items-center justify-between flex-shrink-0 sticky top-0 bg-white/95 backdrop-blur-sm z-20 md:relative md:bg-white md:z-auto">
          <div class="flex items-center gap-3 cursor-pointer hover:opacity-80 transition-opacity" @click="router.push(`/user/${post.user_id}`)">
            <img 
              :src="getImageUrl(post.avatar_url) || 'https://via.placeholder.com/40'" 
              class="w-10 h-10 rounded-full object-cover border border-gray-100"
            >
            <span class="font-medium text-gray-900">{{ post.nickname }}</span>
          </div>
          
          <button 
            v-if="!userStore.user || userStore.user.id !== post.user_id"
            @click="isFollowing ? handleUnfollow() : handleFollow()"
            class="px-5 py-1.5 rounded-full text-sm font-medium transition-colors"
            :class="isFollowing ? 'border border-gray-200 text-gray-500 hover:bg-gray-50' : 'border border-xhs-red text-xhs-red hover:bg-red-50'"
          >
            {{ isFollowing ? '已关注' : '关注' }}
          </button>
        </div>

        <!-- Scrollable Content Area -->
        <div class="md:flex-1 md:overflow-y-auto p-5 custom-scrollbar pb-24 md:pb-5">
          <h1 class="text-xl font-bold text-gray-900 mb-3 leading-snug">{{ post.title }}</h1>
          <p class="text-gray-700 whitespace-pre-wrap text-base leading-relaxed mb-4">
            {{ post.content }}
          </p>
          <p class="text-xs text-gray-400 mb-6">{{ new Date(post.created_at).toLocaleDateString() }}</p>
          
          <div class="border-t border-gray-100 pt-6">
            <h3 class="text-sm font-medium text-gray-500 mb-4">共 {{ comments.length }} 条评论</h3>
            
            <!-- Comment List -->
            <div class="max-h-[60vh] overflow-y-auto custom-scrollbar md:max-h-none md:overflow-visible pr-1">
              <div class="space-y-5">
                <div v-for="comment in comments" :key="comment.id" class="flex gap-3 group">
                  <img 
                    :src="getImageUrl(comment.avatar_url) || 'https://via.placeholder.com/32'" 
                    class="w-8 h-8 rounded-full object-cover border border-gray-100 flex-shrink-0 cursor-pointer"
                    @click="router.push(`/user/${comment.user_id}`)"
                  >
                  <div class="flex-1">
                    <div class="flex items-center justify-between mb-1">
                      <span class="text-sm font-medium text-gray-600 cursor-pointer hover:text-gray-900" @click="router.push(`/user/${comment.user_id}`)">{{ comment.nickname }}</span>
                      
                      <!-- Comment Like Button -->
                      <div class="flex flex-col items-center gap-0.5 cursor-pointer" @click="handleCommentLike(comment)">
                        <svg xmlns="http://www.w3.org/2000/svg" :fill="comment.is_liked ? 'currentColor' : 'none'" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 transition-colors" :class="comment.is_liked ? 'text-xhs-red' : 'text-gray-400 group-hover:text-gray-600'">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z" />
                        </svg>
                        <span class="text-xs text-gray-400" v-if="comment.likes_count > 0">{{ comment.likes_count }}</span>
                      </div>
                    </div>
                    <p class="text-sm text-gray-800 leading-normal">{{ comment.content }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer: Actions & Input -->
        <div class="p-4 border-t border-gray-100 flex-shrink-0 bg-white fixed bottom-0 left-0 right-0 md:relative md:bottom-auto z-20">
          <!-- Action Buttons -->
          <div class="flex items-center justify-between mb-4 px-2">
            <div class="flex items-center gap-6">
              <button @click="handleLike" class="flex items-center gap-1.5 group">
                <svg xmlns="http://www.w3.org/2000/svg" :fill="isLiked ? 'currentColor' : 'none'" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-7 h-7 transition-colors" :class="isLiked ? 'text-xhs-red' : 'text-gray-600 group-hover:text-gray-900'">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z" />
                </svg>
                <span class="text-sm font-medium" :class="isLiked ? 'text-gray-900' : 'text-gray-600'">{{ post.likes_count }}</span>
              </button>
              
              <button @click="handleCollect" class="flex items-center gap-1.5 group">
                <svg xmlns="http://www.w3.org/2000/svg" :fill="isCollected ? 'currentColor' : 'none'" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-7 h-7 transition-colors" :class="isCollected ? 'text-yellow-500' : 'text-gray-600 group-hover:text-gray-900'">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M11.48 3.499a.562.562 0 0 1 1.04 0l2.125 5.111a.563.562 0 0 0 .475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 0 0-.182.557l1.285 5.385a.562.562 0 0 1-.84.61l-4.725-2.885a.563.563 0 0 0-.586 0L6.982 20.54a.562.562 0 0 1-.84-.61l1.285-5.386a.562.562 0 0 0-.182-.557l-4.204-3.602a.563.563 0 0 1 .321-.988l5.518-.442a.563.563 0 0 0 .475-.345L11.48 3.5Z" />
                </svg>
                <span class="text-sm font-medium" :class="isCollected ? 'text-gray-900' : 'text-gray-600'">收藏</span>
              </button>
              
              <button @click="handleShare" class="flex items-center gap-1.5 group">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-7 h-7 text-gray-600 group-hover:text-gray-900">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M7.217 10.907a2.25 2.25 0 1 0 0 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186 9.566-5.314m-9.566 7.5 9.566 5.314m0 0a2.25 2.25 0 1 0 3.935 2.186 2.25 2.25 0 0 0-3.935-2.186Zm0-12.814a2.25 2.25 0 1 0 3.933-2.185 2.25 2.25 0 0 0-3.933 2.185Z" />
                </svg>
                <span class="text-sm font-medium text-gray-600">分享</span>
              </button>
            </div>
          </div>

          <!-- Input -->
          <div class="flex items-center gap-3 relative">
            <div class="relative flex-1">
              <input 
                v-model="newComment"
                type="text" 
                placeholder="说点什么..." 
                class="w-full h-10 pl-4 pr-16 bg-gray-100 rounded-full border-none focus:bg-gray-50 focus:ring-1 focus:ring-gray-200 transition-all text-sm"
                @keyup.enter="handleComment"
              >
              <!-- Emoji Icon placeholder -->
              <div class="absolute right-3 top-2 text-gray-400 cursor-pointer hover:text-gray-600">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.182 15.182a4.5 4.5 0 0 1-6.364 0M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0ZM9.75 9.75c0 .414-.168.75-.375.75S9 10.164 9 9.75 9.168 9 9.375 9s.375.336.375.75Zm-.375 0h.008v.015h-.008V9.75Zm5.625 0c0 .414-.168.75-.375.75s-.375-.336-.375-.75.168-.75.375-.75.375.336.375.75Zm-.375 0h.008v.015h-.008V9.75Z" />
                </svg>
              </div>
            </div>
            <button 
              @click="handleComment"
              class="px-4 py-1.5 bg-xhs-red text-white rounded-full text-sm font-medium hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              :disabled="!newComment.trim()"
            >
              发送
            </button>
          </div>
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

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
