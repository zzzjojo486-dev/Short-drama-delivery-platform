import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import PublishView from '../views/PublishView.vue'
import { useUserStore } from '../stores/user'
import { useAdminStore } from '../stores/admin'
import AdminLoginView from '../views/admin/AdminLoginView.vue'

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
      path: '/admin/login',
      name: 'admin-login',
      component: AdminLoginView,
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
    },
    {
      path: '/orders',
      name: 'creator-orders',
      component: () => import('../views/creator/CreatorOrders.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/orders/:id',
      name: 'creator-order-detail',
      component: () => import('../views/creator/CreatorOrderDetail.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin',
      component: () => import('../views/admin/AdminLayout.vue'),
      meta: { requiresAdmin: true, hideNavBar: true, hideTabBar: true },
      children: [
        {
          path: '',
          redirect: () => {
            const adminStore = useAdminStore()
            return adminStore.user?.role === 2 ? '/admin/reviews' : '/admin/users'
          }
        },
        { path: 'users', name: 'admin-users', component: () => import('../views/admin/AdminUsers.vue') },
        { path: 'reviews', name: 'admin-reviews', component: () => import('../views/admin/AdminReviews.vue') },
        { path: 'orders', name: 'admin-orders', component: () => import('../views/admin/AdminOrders.vue') },
        { path: 'orders/create', name: 'admin-orders-create', component: () => import('../views/admin/AdminOrderCreate.vue') },
        { path: 'orders/:id', name: 'admin-order-detail', component: () => import('../views/admin/AdminOrderDetail.vue') }
      ]
    }
  ]
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const adminStore = useAdminStore()
  // 前台页面:认前台登录
  if (to.meta.requiresAuth && (!userStore.user || !userStore.token)) {
    next({ path: '/login', query: { redirect: to.fullPath } })
  } else if (to.meta.requiresAdmin && !adminStore.token) {
    // 后台页面:只认后台自己的 admin_token,与前台互不干涉;登录后回原目标
    next({ path: '/admin/login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router

