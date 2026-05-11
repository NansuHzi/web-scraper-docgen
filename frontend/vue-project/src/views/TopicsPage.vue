<template>
  <div>
    <div class="max-w-3xl mx-auto px-6 md:px-10 pb-24">
      <!-- Hero -->
      <section class="pt-8 pb-12 animate-slide-down">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs text-muted tracking-[0.2em] mb-3 font-mono">HOT TOPICS</p>
            <h1 class="text-2xl md:text-3xl font-bold text-white tracking-tight leading-tight">
              热点选题
              <span class="text-muted font-normal">&</span>
              趋势分析
            </h1>
            <p class="text-sm text-muted mt-2 max-w-lg">
              实时追踪微博热搜和知乎热榜，AI 智能分析推荐有价值的文档选题
            </p>
          </div>
          <button @click="refreshTopics(true)" :disabled="isLoading"
            class="btn-outline text-xs flex items-center gap-1.5"
          >
            <svg class="w-3.5 h-3.5" :class="{ 'animate-spin': isLoading }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            <span>刷新</span>
          </button>
        </div>
      </section>

      <!-- Source Filter + Stats -->
      <section class="mb-6 animate-slide-up stagger-1">
        <div class="card-glass p-4 flex items-center justify-between flex-wrap gap-3">
          <div class="flex gap-1.5 p-0.5 rounded-lg bg-white/[0.03] border border-white/[0.04]">
            <button v-for="s in sources" :key="s.value" @click="activeSource = s.value"
              class="px-3 py-1.5 rounded-md text-xs font-medium transition-all"
              :class="activeSource === s.value ? 'bg-white/[0.06] text-neon-green' : 'text-muted hover:text-white'"
            >{{ s.label }}</button>
          </div>
          <p v-if="generatedAt" class="text-xs text-muted">
            更新时间 {{ formatDate(generatedAt) }}
          </p>
        </div>
      </section>

      <!-- Loading -->
      <section v-if="isLoading" class="animate-slide-up stagger-1">
        <div class="card-glass p-12 text-center">
          <div class="relative w-14 h-14 mx-auto mb-5">
            <div class="absolute inset-0 rounded-full border-2 border-neon-green/10" />
            <div class="absolute inset-1 rounded-full border-2 border-transparent border-t-neon-green animate-spin" />
          </div>
          <p class="text-sm text-white font-medium">{{ loadingText }}</p>
        </div>
      </section>

      <!-- LLM Recommendations -->
      <section v-if="!isLoading && recommendations.length > 0" class="mb-8 animate-slide-up stagger-2">
        <div class="card-glass p-6 md:p-8">
          <div class="flex items-center gap-2 mb-5">
            <svg class="w-4 h-4 text-neon-green" fill="currentColor" viewBox="0 0 24 24"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
            <h2 class="text-lg font-semibold text-white tracking-tight">AI 推荐选题</h2>
          </div>
          <div class="space-y-4">
            <div v-for="rec in recommendations" :key="rec.rank"
              class="bg-white/[0.02] border border-white/[0.04] rounded-xl p-4 hover:bg-white/[0.04] hover:border-white/[0.08] transition-all"
            >
              <div class="flex items-start justify-between gap-4">
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-1">
                    <span class="w-6 h-6 rounded-md bg-neon-green/[0.08] border border-neon-green/[0.12] flex items-center justify-center text-xs font-bold text-neon-green">{{ rec.rank }}</span>
                    <h3 class="text-base font-semibold text-white">{{ rec.title }}</h3>
                    <span v-if="rec.estimated_interest === 'high'" class="tag tag-green">高热度</span>
                    <span v-else-if="rec.estimated_interest === 'medium'" class="tag" style="background: rgba(245,158,11,0.08); color: #f59e0b; border-color: rgba(245,158,11,0.2);">中热度</span>
                    <span v-else class="tag" style="background: rgba(100,116,139,0.08); color: #94a3b8; border-color: rgba(100,116,139,0.2);">低热度</span>
                  </div>
                  <p v-if="rec.reason" class="text-xs text-muted mt-1.5">{{ rec.reason }}</p>
                  <p v-if="rec.angle" class="text-xs mt-2 flex items-start gap-1.5">
                    <span class="text-cyan-blue shrink-0 mt-0.5">◆</span>
                    <span class="text-muted/80">{{ rec.angle }}</span>
                  </p>
                  <div v-if="rec.related_topics && rec.related_topics.length" class="flex items-center gap-1.5 mt-2 flex-wrap">
                    <span class="text-[11px] text-muted">相关:</span>
                    <span v-for="rt in rec.related_topics" :key="rt" class="text-[11px] px-2 py-0.5 rounded bg-white/[0.03] border border-white/[0.04] text-muted">{{ rt }}</span>
                  </div>
                </div>
                <button @click="generateDoc(rec)"
                  class="btn-outline text-xs shrink-0 flex items-center gap-1"
                >
                  <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                  <span>生成文档</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Hot Topics Tabs -->
      <section v-if="!isLoading && (weiboTopics.length > 0 || zhihuTopics.length > 0)" class="animate-slide-up stagger-3">
        <div class="card-glass p-6 md:p-8">
          <!-- Tab bar -->
          <div class="flex gap-1 p-0.5 rounded-lg bg-white/[0.03] border border-white/[0.04] mb-5 w-fit">
            <button @click="activeTab = 'weibo'"
              class="px-3.5 py-1.5 rounded-md text-xs font-medium transition-all"
              :class="activeTab === 'weibo' ? 'bg-white/[0.06] text-neon-green' : 'text-muted hover:text-white'"
            >
              微博热搜 ({{ weiboTopics.length }})
            </button>
            <button @click="activeTab = 'zhihu'"
              class="px-3.5 py-1.5 rounded-md text-xs font-medium transition-all"
              :class="activeTab === 'zhihu' ? 'bg-white/[0.06] text-neon-green' : 'text-muted hover:text-white'"
            >
              知乎热榜 ({{ zhihuTopics.length }})
            </button>
          </div>

          <!-- Weibo tab -->
          <div v-if="activeTab === 'weibo'">
            <div class="space-y-1.5">
              <div v-for="t in weiboTopics" :key="'w'+t.rank"
                class="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/[0.04] hover:bg-white/[0.04] transition-all group"
              >
                <div class="flex items-center gap-3 min-w-0">
                  <span class="w-6 text-center text-xs font-bold" :class="t.rank <= 3 ? 'text-neon-green' : 'text-muted'">{{ t.rank }}</span>
                  <span class="text-sm text-white truncate group-hover:text-neon-green transition-colors">{{ t.title }}</span>
                  <span v-if="t.heat" class="tag scale-75 origin-left" :class="t.heat === '爆' ? 'tag' : ''" :style="t.heat === '爆' ? 'background:rgba(239,68,68,0.1);color:#f87171;border-color:rgba(239,68,68,0.2)' : ''">{{ t.heat }}</span>
                </div>
                <span v-if="t.hot_value" class="text-xs text-muted shrink-0 ml-3 font-mono">{{ t.hot_value }}</span>
              </div>
            </div>
          </div>

          <!-- Zhihu tab -->
          <div v-if="activeTab === 'zhihu'">
            <div class="space-y-1.5">
              <div v-for="t in zhihuTopics" :key="'z'+t.rank"
                class="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/[0.04] hover:bg-white/[0.04] transition-all group"
              >
                <div class="flex items-center gap-3 min-w-0">
                  <span class="w-6 text-center text-xs font-bold" :class="t.rank <= 3 ? 'text-cyan-blue' : 'text-muted'">{{ t.rank }}</span>
                  <span class="text-sm text-white truncate group-hover:text-cyan-blue transition-colors">{{ t.title }}</span>
                </div>
                <span v-if="t.hot_value" class="text-xs text-muted shrink-0 ml-3 font-mono">{{ t.hot_value }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Empty state -->
      <section v-if="!isLoading && weiboTopics.length === 0 && zhihuTopics.length === 0" class="animate-slide-up stagger-1">
        <div class="card-glass p-12 text-center">
          <div class="w-12 h-12 rounded-2xl bg-neon-green/[0.04] border border-neon-green/[0.08] flex items-center justify-center mx-auto mb-4">
            <svg class="w-5 h-5 text-neon-green/40" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
          </div>
          <p class="text-sm text-muted">暂无热搜数据</p>
          <button @click="refreshTopics" class="mt-3 btn-outline text-xs">点击刷新</button>
        </div>
      </section>
    </div>

    <!-- Error Modal -->
    <Transition name="overlay">
      <div v-if="errorMessage" class="fixed inset-0 z-50 flex items-center justify-center" style="background: rgba(6,6,8,0.7); backdrop-filter: blur(4px);" @click="errorMessage = ''">
        <div class="card-glass p-6 max-w-sm mx-4 text-center animate-scale-in" @click.stop>
          <div class="w-10 h-10 rounded-full bg-red-500/[0.08] border border-red-500/[0.15] flex items-center justify-center mx-auto mb-4">
            <svg class="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          </div>
          <p class="text-white font-semibold mb-1">获取失败</p>
          <p class="text-sm text-muted mb-5">{{ errorMessage }}</p>
          <button @click="errorMessage = ''" class="btn-gradient w-full py-2.5 text-sm">确定</button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import apiService from '../services/api'

const activeSource = ref('all')
const activeTab = ref('weibo')
const weiboTopics = ref([])
const zhihuTopics = ref([])
const recommendations = ref([])
const generatedAt = ref(null)
const isLoading = ref(false)
const loadingText = ref('正在获取热搜数据...')
const errorMessage = ref('')

const sources = [
  { value: 'all', label: '全部' },
  { value: 'weibo', label: '微博' },
  { value: 'zhihu', label: '知乎' },
]

const CACHE_KEY = 'docgen_topics_cache'
const CACHE_DURATION = 5 * 60 * 1000 // 5分钟缓存

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const loadFromCache = () => {
  try {
    const cached = sessionStorage.getItem(CACHE_KEY)
    if (cached) {
      const data = JSON.parse(cached)
      if (data.timestamp && Date.now() - data.timestamp < CACHE_DURATION) {
        return data.data
      }
    }
  } catch (e) {
    console.warn('Failed to load topics from cache:', e)
  }
  return null
}

const saveToCache = (data) => {
  try {
    sessionStorage.setItem(CACHE_KEY, JSON.stringify({
      timestamp: Date.now(),
      data: data
    }))
  } catch (e) {
    console.warn('Failed to save topics to cache:', e)
  }
}

const refreshTopics = async (forceRefresh = false) => {
  isLoading.value = true
  errorMessage.value = ''

  try {
    // 尝试从缓存加载（除非强制刷新）
    if (!forceRefresh) {
      const cachedData = loadFromCache()
      if (cachedData) {
        weiboTopics.value = cachedData.weibo_topics || []
        zhihuTopics.value = cachedData.zhihu_topics || []
        recommendations.value = (cachedData.llm_recommendations || []).filter(r => !r.note)
        generatedAt.value = cachedData.generated_at || null
        isLoading.value = false
        return
      }
    }

    loadingText.value = '正在获取热搜数据...'
    const res = await apiService.getHotTopics(activeSource.value)
    weiboTopics.value = res.weibo_topics || []
    zhihuTopics.value = res.zhihu_topics || []
    recommendations.value = (res.llm_recommendations || []).filter(r => !r.note)

    if (zhihuTopics.value.length > 0 && activeTab.value === 'weibo' && weiboTopics.value.length === 0) {
      activeTab.value = 'zhihu'
    }

    generatedAt.value = res.generated_at || null

    // 保存到缓存
    saveToCache({
      weibo_topics: weiboTopics.value,
      zhihu_topics: zhihuTopics.value,
      llm_recommendations: recommendations.value,
      generated_at: generatedAt.value
    })
  } catch (e) {
    errorMessage.value = e.message
  } finally {
    isLoading.value = false
  }
}

const generateDoc = (rec) => {
  const query = encodeURIComponent(rec.title)
  window.open(`/search?q=${query}`, '_blank')
}

onMounted(() => {
  refreshTopics()
})

// 监听来源切换，切换来源时强制刷新
watch(activeSource, () => {
  refreshTopics(true)
})
</script>

<style scoped>
.overlay-enter-active, .overlay-leave-active { transition: opacity 0.25s ease; }
.overlay-enter-from, .overlay-leave-to { opacity: 0; }
</style>
