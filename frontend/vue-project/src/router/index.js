import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomePage.vue'),
    },
    {
      path: '/search',
      name: 'search',
      component: () => import('@/views/SearchPage.vue'),
    },
    {
      path: '/scheduler',
      name: 'scheduler',
      component: () => import('@/views/SchedulerPage.vue'),
    },
    {
      path: '/topics',
      name: 'topics',
      component: () => import('@/views/TopicsPage.vue'),
    },
    {
      path: '/monitor',
      name: 'monitor',
      component: () => import('@/views/MonitorPage.vue'),
    },
    {
      path: '/crawler',
      name: 'crawler',
      component: () => import('@/views/CrawlerPage.vue'),
    },
    {
      path: '/tasks',
      name: 'tasks',
      component: () => import('@/views/TaskQueuePage.vue'),
    },
  ],
})

export default router
