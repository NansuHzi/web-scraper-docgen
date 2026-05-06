<template>
  <div class="min-h-screen">
    <!-- Navigation -->
    <nav class="fixed top-0 left-0 right-0 z-50 glass">
      <div class="max-w-5xl mx-auto px-6 md:px-10 h-16 flex items-center justify-between">
        <div class="flex items-center gap-8">
          <router-link to="/" class="flex items-center gap-2.5 group">
            <span class="w-8 h-8 rounded-lg bg-gradient-to-br from-neon-green to-cyan-blue flex items-center justify-center">
              <span class="font-mono text-base font-bold text-base tracking-tighter">D</span>
            </span>
            <span class="text-lg font-semibold text-white tracking-tight group-hover:text-neon-green transition-colors duration-300">DocGen</span>
          </router-link>

          <div class="flex gap-1 p-0.5 rounded-lg bg-white/[0.03] border border-white/[0.04]">
            <router-link
              to="/"
              class="relative px-3.5 py-1.5 rounded-md text-sm font-medium transition-all duration-300"
              :class="$route.path === '/'
                ? 'text-neon-green'
                : 'text-muted hover:text-white'"
            >
              <span v-if="$route.path === '/'" class="absolute inset-0 bg-neon-green/[0.06] border border-neon-green/[0.12] rounded-md" />
              <span class="relative">URL 抓取</span>
            </router-link>
            <router-link
              to="/search"
              class="relative px-3.5 py-1.5 rounded-md text-sm font-medium transition-all duration-300"
              :class="$route.path === '/search'
                ? 'text-neon-green'
                : 'text-muted hover:text-white'"
            >
              <span v-if="$route.path === '/search'" class="absolute inset-0 bg-neon-green/[0.06] border border-neon-green/[0.12] rounded-md" />
              <span class="relative">智能搜索</span>
            </router-link>
          </div>
        </div>

        <div class="hidden md:flex items-center gap-3">
          <span class="w-1.5 h-1.5 rounded-full bg-neon-green animate-pulse" />
          <span class="text-xs text-muted tracking-wider">v1.0</span>
        </div>
      </div>
    </nav>

    <!-- Page Content -->
    <main class="pt-20">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
</script>

<style scoped>
.page-enter-active,
.page-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
