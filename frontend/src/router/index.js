import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import PublishView from '../views/PublishView.vue'
import { useUserStore } from '../stores/user'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      children: [
        {
          path: 'explore/:id',
          name: 'post-detail',
          component: () => import('../views/PostDetailView.vue')
        }
      ]
    },
    {
      path: '/category',
      name: 'category',
      component: () => import('../views/CategoryView.vue')
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { hideNavBar: true, hideTabBar: true }
    },
    {
      path: '/publish',
      name: 'publish',
      component: PublishView,
      meta: { requiresAuth: true }
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/ProfileView.vue'),
      children: [
        {
          path: 'explore/:postId',
          name: 'profile-post-detail',
          component: () => import('../views/PostDetailView.vue')
        }
      ]
    },
    {
      path: '/user/:id',
      name: 'user-profile',
      component: () => import('../views/ProfileView.vue'),
      children: [
        {
          path: 'explore/:postId',
          name: 'user-profile-post-detail',
          component: () => import('../views/PostDetailView.vue')
        }
      ]
    },
    {
      path: '/messages',
      name: 'messages',
      component: () => import('../views/MessageIndexView.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: 'post/:postId',
          name: 'message-post-detail',
          component: () => import('../views/PostDetailView.vue')
        }
      ]
    },
    {
      path: '/messages/:id',
      name: 'chat',
      component: () => import('../views/ChatView.vue'),
      meta: { requiresAuth: true, hideNavBar: true, hideTabBar: true }
    }
  ]
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  if (to.meta.requiresAuth && !userStore.user) {
    next('/login')
  } else {
    next()
  }
})

export default router

