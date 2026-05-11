<template>
  <div class="min-h-screen">
    <!-- Navigation -->
    <nav class="fixed top-0 left-0 right-0 z-50 nav-bg border-b nav-border">
      <div class="max-w-5xl mx-auto px-6 md:px-10 h-[52px] flex items-center justify-between gap-4">
        <router-link to="/" class="flex items-center gap-2 group shrink-0">
          <span class="w-7 h-7 rounded-lg bg-gradient-to-br from-neon-green to-cyan-blue flex items-center justify-center shadow-lg shadow-neon-green/20">
            <span class="font-mono text-sm font-bold text-base tracking-tighter">D</span>
          </span>
          <span class="text-base font-semibold text-white tracking-tight group-hover:text-neon-green transition-colors duration-300 hidden sm:inline">DocGen</span>
        </router-link>

        <div class="flex-1 flex items-center justify-end">
          <div class="nav-pill">
            <router-link
              v-for="item in navPrimary"
              :key="item.path"
              :to="item.path"
              class="nav-item"
              :class="$route.path === item.path ? 'nav-item-active' : 'nav-item-inactive'"
            >
              {{ item.label }}
            </router-link>

            <div class="relative" @mouseenter="showMore = true" @mouseleave="showMore = false">
              <button
                class="nav-item"
                :class="isMoreActive ? 'nav-item-active' : 'nav-item-inactive'"
              >
                更多
                <svg class="w-3 h-3 ml-0.5 transition-transform duration-200" :class="{ 'rotate-180': showMore }" viewBox="0 0 12 12" fill="none"><path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </button>

              <transition name="dropdown">
                <div v-show="showMore" class="dropdown-menu">
                  <p class="dropdown-label">工具</p>
                  <router-link
                    v-for="item in navTools"
                    :key="item.path"
                    :to="item.path"
                    @click="showMore = false"
                    class="dropdown-link"
                    :class="$route.path === item.path ? 'dropdown-link-active' : ''"
                  >
                    {{ item.label }}
                  </router-link>
                  <div class="dropdown-divider" />
                  <p class="dropdown-label">系统</p>
                  <router-link
                    v-for="item in navSystem"
                    :key="item.path"
                    :to="item.path"
                    @click="showMore = false"
                    class="dropdown-link"
                    :class="$route.path === item.path ? 'dropdown-link-active' : ''"
                  >
                    {{ item.label }}
                  </router-link>
                </div>
              </transition>
            </div>
          </div>
        </div>

        <div class="hidden md:flex items-center gap-2 shrink-0">
          <span class="w-1.5 h-1.5 rounded-full bg-neon-green animate-pulse shadow-sm shadow-neon-green/40" />
          <span class="text-[11px] text-muted/70 tracking-wider font-medium">v1.0</span>
        </div>
      </div>
    </nav>

    <!-- Page Content -->
    <main class="pt-[68px]">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const showMore = ref(false)

const navPrimary = [
  { path: '/', label: 'URL 抓取' },
  { path: '/search', label: '智能搜索' },
]

const navTools = [
  { path: '/scheduler', label: '定时任务' },
  { path: '/topics', label: '热点选题' },
  { path: '/crawler', label: '通用爬虫' },
  { path: '/tasks', label: '任务队列' },
]

const navSystem = [
  { path: '/monitor', label: '系统监控' },
]

const isMoreActive = computed(() => {
  const allMorePaths = [...navTools, ...navSystem].map(i => i.path)
  return allMorePaths.includes(window.location.pathname)
})
</script>

<style scoped>
/* Nav background */
.nav-bg {
  background: linear-gradient(180deg, #181b24 0%, #141720 100%);
}

.nav-border {
  border-color: rgba(255, 255, 255, 0.05);
}

/* Pill container */
.nav-pill {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 3px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

/* Nav item */
.nav-item {
  position: relative;
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  transition: all 0.18s ease;
  cursor: pointer;
  line-height: 1.4;
}

.nav-item-inactive {
  color: rgba(255, 255, 255, 0.45);
}
.nav-item-inactive:hover {
  color: rgba(255, 255, 255, 0.85);
  background: rgba(255, 255, 255, 0.04);
}

.nav-item-active {
  color: #34d399;
  background: rgba(52, 211, 153, 0.08);
  box-shadow: inset 0 0 0 1px rgba(52, 211, 153, 0.15);
}

/* Dropdown */
.dropdown-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: -4px;
  width: 176px;
  padding: 6px;
  border-radius: 14px;
  background: #1a1d26;
  border: 1px solid rgba(255, 255, 255, 0.07);
  box-shadow:
    0 4px 6px -1px rgba(0, 0, 0, 0.35),
    0 10px 25px -5px rgba(0, 0, 0, 0.45),
    0 0 0 1px rgba(255, 255, 255, 0.03) inset;
  z-index: 100;
}

.dropdown-label {
  padding: 6px 10px 4px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.28);
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
}

.dropdown-link {
  display: block;
  padding: 7px 10px;
  margin: 1px 4px;
  border-radius: 8px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.65);
  transition: all 0.15s ease;
}
.dropdown-link:hover {
  color: rgba(255, 255, 255, 0.95);
  background: rgba(255, 255, 255, 0.06);
}

.dropdown-link-active {
  color: #34d399;
  background: rgba(52, 211, 153, 0.1);
  font-weight: 500;
}
.dropdown-link-active:hover {
  background: rgba(52, 211, 153, 0.14);
}

.dropdown-divider {
  height: 1px;
  margin: 4px 10px;
  background: rgba(255, 255, 255, 0.06);
}

/* Transitions */
.page-enter-active,
.page-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.dropdown-enter-active {
  transition: opacity 0.16s ease, transform 0.16s ease;
}
.dropdown-leave-active {
  transition: opacity 0.1s ease, transform 0.1s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.97);
}
</style>
