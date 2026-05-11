<template>
  <div>
    <div class="max-w-3xl mx-auto px-6 md:px-10 pb-24">
      <!-- Hero -->
      <section class="pt-8 pb-12 animate-slide-down">
        <p class="text-xs text-muted tracking-[0.2em] mb-3 font-mono">CRAWLER</p>
        <h1 class="text-2xl md:text-3xl font-bold text-white tracking-tight leading-tight">
          通用爬虫
          <span class="text-muted font-normal">&</span>
          站点分析
        </h1>
        <p class="text-sm text-muted mt-2 max-w-lg">
          支持静态/JS渲染/混合三通道爬取，自动识别站点类型，批量并发抓取
        </p>
      </section>

      <!-- Tab Switcher -->
      <section class="flex gap-1 p-0.5 rounded-lg bg-white/[0.03] border border-white/[0.04] mb-8 animate-slide-up stagger-1">
        <button v-for="tab in tabs" :key="tab.key" @click="activeTab = tab.key"
          class="relative flex-1 py-2 rounded-md text-sm font-medium transition-all duration-300"
          :class="activeTab === tab.key ? 'text-neon-green' : 'text-muted hover:text-white'"
        >
          <span v-if="activeTab === tab.key" class="absolute inset-0 bg-neon-green/[0.06] border border-neon-green/[0.12] rounded-md" />
          <span class="relative">{{ tab.label }}</span>
        </button>
      </section>

      <!-- ====== 单页爬取 ====== -->
      <template v-if="activeTab === 'single'">
        <section class="animate-slide-up stagger-1">
          <div class="card-glass p-6 md:p-8">
            <h2 class="text-lg font-semibold text-white tracking-tight mb-5">单页爬取</h2>

            <div class="space-y-4">
              <div>
                <label class="text-xs text-muted block mb-1.5">目标 URL</label>
                <input v-model="singleUrl" type="url" placeholder="https://example.com/docs" class="input-glass" />
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="text-xs text-muted block mb-1.5">渲染模式</label>
                  <select v-model="singleRenderMode" class="select-glass w-full">
                    <option value="auto">自动检测</option>
                    <option value="static">静态 (requests)</option>
                    <option value="js">JS 渲染 (playwright)</option>
                    <option value="hybrid">混合模式</option>
                  </select>
                </div>
                <div>
                  <label class="text-xs text-muted block mb-1.5">输出格式</label>
                  <select v-model="singleFormat" class="select-glass w-full">
                    <option value="md">Markdown</option>
                    <option value="html">HTML</option>
                    <option value="text">纯文本</option>
                  </select>
                </div>
              </div>

              <div class="flex items-center gap-2">
                <input type="checkbox" v-model="singleExtractLinks" class="checkbox-glass" id="extract-links" />
                <label for="extract-links" class="text-xs text-muted cursor-pointer">提取页面内链</label>
              </div>

              <button @click="doSingleCrawl" :disabled="singleLoading || !singleUrl"
                class="btn-gradient w-full py-3 text-sm"
              >
                <span v-if="singleLoading" class="flex items-center justify-center gap-2">
                  <span class="w-4 h-4 border-2 border-base/30 border-t-base rounded-full animate-spin" />
                  爬取中...
                </span>
                <span v-else>开始爬取</span>
              </button>
            </div>

            <!-- Result -->
            <div v-if="singleResult" class="mt-6 p-4 rounded-lg bg-white/[0.02] border border-white/[0.04]">
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center gap-2">
                  <span class="tag tag-green text-[11px]">{{ singleResult.site_type || 'unknown' }}</span>
                  <span class="text-xs text-muted">{{ singleResult.page_count || 1 }} 页</span>
                  <span class="text-xs text-muted">{{ formatBytes(singleResult.size_bytes || 0) }}</span>
                </div>
                <span class="text-xs text-muted font-mono">{{ singleResult.duration_ms ? (singleResult.duration_ms / 1000).toFixed(1) + 's' : '' }}</span>
              </div>
              <div class="markdown-body max-h-96 overflow-y-auto text-sm">
                <div v-html="renderMarkdown(singleResult.content || '')" />
              </div>
            </div>
          </div>
        </section>
      </template>

      <!-- ====== 站点分析 ====== -->
      <template v-if="activeTab === 'analyze'">
        <section class="animate-slide-up stagger-1">
          <div class="card-glass p-6 md:p-8">
            <h2 class="text-lg font-semibold text-white tracking-tight mb-5">站点类型分析</h2>

            <div class="space-y-4">
              <div>
                <label class="text-xs text-muted block mb-1.5">目标 URL</label>
                <input v-model="analyzeUrl" type="url" placeholder="https://example.com" class="input-glass" />
              </div>

              <button @click="doAnalyze" :disabled="analyzeLoading || !analyzeUrl"
                class="btn-gradient w-full py-3 text-sm"
              >
                <span v-if="analyzeLoading" class="flex items-center justify-center gap-2">
                  <span class="w-4 h-4 border-2 border-base/30 border-t-base rounded-full animate-spin" />
                  分析中...
                </span>
                <span v-else>开始分析</span>
              </button>
            </div>

            <div v-if="analyzeResult" class="mt-6 space-y-3">
              <div class="grid grid-cols-2 gap-3">
                <div class="p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                  <p class="text-xs text-muted">站点类型</p>
                  <p class="text-lg font-bold text-neon-green mt-1">{{ analyzeResult.site_type || '-' }}</p>
                </div>
                <div class="p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                  <p class="text-xs text-muted">CMS 平台</p>
                  <p class="text-lg font-bold text-cyan-blue mt-1">{{ analyzeResult.cms || '通用' }}</p>
                </div>
                <div class="p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                  <p class="text-xs text-muted">推荐渲染模式</p>
                  <p class="text-lg font-bold text-amber-warm mt-1">{{ analyzeResult.render_mode || '-' }}</p>
                </div>
                <div class="p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                  <p class="text-xs text-muted">置信度</p>
                  <p class="text-lg font-bold text-white mt-1">{{ analyzeResult.confidence ? (analyzeResult.confidence * 100).toFixed(0) + '%' : '-' }}</p>
                </div>
              </div>

              <div v-if="analyzeResult.features?.length" class="p-4 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                <p class="text-xs text-muted mb-2">检测特征</p>
                <div class="flex flex-wrap gap-1.5">
                  <span v-for="f in analyzeResult.features" :key="f" class="tag text-[11px]">{{ f }}</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      </template>

      <!-- ====== 批量爬取 ====== -->
      <template v-if="activeTab === 'batch'">
        <section class="animate-slide-up stagger-1">
          <div class="card-glass p-6 md:p-8">
            <h2 class="text-lg font-semibold text-white tracking-tight mb-5">批量爬取</h2>

            <div class="space-y-4">
              <div>
                <label class="text-xs text-muted block mb-1.5">URL 列表（每行一个，最多50个）</label>
                <textarea v-model="batchUrls" rows="6" placeholder="https://example.com/page1&#10;https://example.com/page2&#10;https://example.com/page3" class="input-glass resize-none" />
                <p class="text-xs text-muted mt-1">{{ batchUrlCount }} 个 URL</p>
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="text-xs text-muted block mb-1.5">最大并发</label>
                  <select v-model="batchConcurrency" class="select-glass w-full">
                    <option :value="1">1</option>
                    <option :value="2">2</option>
                    <option :value="3">3</option>
                    <option :value="5">5</option>
                  </select>
                </div>
                <div>
                  <label class="text-xs text-muted block mb-1.5">输出格式</label>
                  <select v-model="batchFormat" class="select-glass w-full">
                    <option value="md">Markdown</option>
                    <option value="html">HTML</option>
                    <option value="text">纯文本</option>
                  </select>
                </div>
              </div>

              <button @click="doBatchCrawl" :disabled="batchLoading || batchUrlCount === 0"
                class="btn-gradient w-full py-3 text-sm"
              >
                <span v-if="batchLoading" class="flex items-center justify-center gap-2">
                  <span class="w-4 h-4 border-2 border-base/30 border-t-base rounded-full animate-spin" />
                  批量爬取中 ({{ batchProgress }}/{{ batchUrlCount }})
                </span>
                <span v-else>开始批量爬取</span>
              </button>
            </div>

            <div v-if="batchResults.length" class="mt-6 space-y-2">
              <div v-for="(r, i) in batchResults" :key="i"
                class="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]"
              >
                <div class="flex items-center gap-3 min-w-0">
                  <span class="w-2 h-2 rounded-full shrink-0"
                    :class="r.error ? 'bg-red-400' : 'bg-neon-green'"
                  />
                  <span class="text-sm text-white truncate max-w-[300px]">{{ r.url }}</span>
                  <span class="tag text-[11px] shrink-0">{{ r.site_type || '-' }}</span>
                </div>
                <span class="text-xs text-muted shrink-0 ml-3 font-mono">{{ r.duration_ms ? (r.duration_ms / 1000).toFixed(1) + 's' : '' }}</span>
              </div>
            </div>
          </div>
        </section>
      </template>

      <!-- ====== 增量追踪 ====== -->
      <template v-if="activeTab === 'incremental'">
        <section class="animate-slide-up stagger-1">
          <div class="card-glass p-6 md:p-8">
            <h2 class="text-lg font-semibold text-white tracking-tight mb-5">增量追踪</h2>

            <div class="space-y-4">
              <div>
                <label class="text-xs text-muted block mb-1.5">追踪 URL</label>
                <input v-model="trackUrl" type="url" placeholder="https://example.com/docs" class="input-glass" />
              </div>

              <div class="flex gap-3">
                <button @click="doTrackCheck" :disabled="trackLoading || !trackUrl"
                  class="btn-gradient flex-1 py-3 text-sm"
                >
                  <span v-if="trackLoading" class="flex items-center justify-center gap-2">
                    <span class="w-4 h-4 border-2 border-base/30 border-t-base rounded-full animate-spin" />
                    检测中...
                  </span>
                  <span v-else>检测变更</span>
                </button>
                <button @click="doTrackStatus" :disabled="trackLoading"
                  class="btn-outline flex-1 py-3 text-sm"
                >
                  查看状态
                </button>
              </div>
            </div>

            <div v-if="trackResult" class="mt-6 space-y-3">
              <div class="grid grid-cols-3 gap-3">
                <div class="p-3 rounded-lg bg-white/[0.02] border border-white/[0.04] text-center">
                  <p class="text-xs text-muted">状态</p>
                  <p class="text-lg font-bold mt-1" :class="trackResult.changed ? 'text-amber-warm' : 'text-neon-green'">
                    {{ trackResult.changed ? '有变更' : '无变更' }}
                  </p>
                </div>
                <div class="p-3 rounded-lg bg-white/[0.02] border border-white/[0.04] text-center">
                  <p class="text-xs text-muted">上次哈希</p>
                  <p class="text-sm font-mono text-white mt-1 truncate">{{ (trackResult.last_hash || '-').slice(0, 12) }}</p>
                </div>
                <div class="p-3 rounded-lg bg-white/[0.02] border border-white/[0.04] text-center">
                  <p class="text-xs text-muted">检查次数</p>
                  <p class="text-lg font-bold text-white mt-1">{{ trackResult.check_count || 0 }}</p>
                </div>
              </div>

              <div v-if="trackResult.last_checked" class="text-xs text-muted">
                上次检查: {{ formatTime(trackResult.last_checked) }}
              </div>
            </div>
          </div>
        </section>
      </template>
    </div>

    <!-- Error Modal -->
    <Transition name="overlay">
      <div v-if="errorMessage" class="fixed inset-0 z-50 flex items-center justify-center" style="background: rgba(6,6,8,0.7); backdrop-filter: blur(4px);" @click="errorMessage = ''">
        <div class="card-glass p-6 max-w-sm mx-4 text-center animate-scale-in" @click.stop>
          <div class="w-10 h-10 rounded-full bg-red-500/[0.08] border border-red-500/[0.15] flex items-center justify-center mx-auto mb-4">
            <svg class="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          </div>
          <p class="text-white font-semibold mb-1">操作失败</p>
          <p class="text-sm text-muted mb-5">{{ errorMessage }}</p>
          <button @click="errorMessage = ''" class="btn-gradient w-full py-2.5 text-sm">确定</button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const tabs = [
  { key: 'single', label: '单页爬取' },
  { key: 'analyze', label: '站点分析' },
  { key: 'batch', label: '批量爬取' },
  { key: 'incremental', label: '增量追踪' },
]
const activeTab = ref('single')

const errorMessage = ref('')

// --- 单页爬取 ---
const singleUrl = ref('')
const singleRenderMode = ref('auto')
const singleFormat = ref('md')
const singleExtractLinks = ref(false)
const singleLoading = ref(false)
const singleResult = ref(null)

async function doSingleCrawl() {
  singleLoading.value = true
  singleResult.value = null
  try {
    const resp = await fetch('/api/crawler/crawl', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: singleUrl.value,
        render_mode: singleRenderMode.value,
        format: singleFormat.value,
        extract_links: singleExtractLinks.value,
      }),
    })
    if (!resp.ok) {
      const err = await resp.json()
      throw new Error(err.detail || `HTTP ${resp.status}`)
    }
    singleResult.value = await resp.json()
  } catch (e) {
    errorMessage.value = e.message
  } finally {
    singleLoading.value = false
  }
}

// --- 站点分析 ---
const analyzeUrl = ref('')
const analyzeLoading = ref(false)
const analyzeResult = ref(null)

async function doAnalyze() {
  analyzeLoading.value = true
  analyzeResult.value = null
  try {
    const url = new URL(analyzeUrl.value)
    const resp = await fetch(`/api/crawler/analyze?url=${encodeURIComponent(url.href)}`)
    if (!resp.ok) {
      const err = await resp.json()
      throw new Error(err.detail || `HTTP ${resp.status}`)
    }
    analyzeResult.value = await resp.json()
  } catch (e) {
    errorMessage.value = e.message
  } finally {
    analyzeLoading.value = false
  }
}

// --- 批量爬取 ---
const batchUrls = ref('')
const batchConcurrency = ref(2)
const batchFormat = ref('md')
const batchLoading = ref(false)
const batchProgress = ref(0)
const batchResults = ref([])

const batchUrlCount = computed(() => {
  return batchUrls.value.split('\n').map(s => s.trim()).filter(Boolean).length
})

async function doBatchCrawl() {
  const urls = batchUrls.value.split('\n').map(s => s.trim()).filter(Boolean)
  if (!urls.length) return

  batchLoading.value = true
  batchResults.value = []
  batchProgress.value = 0

  try {
    const resp = await fetch('/api/crawler/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        urls,
        max_concurrency: batchConcurrency.value,
        format: batchFormat.value,
      }),
    })
    if (!resp.ok) {
      const err = await resp.json()
      throw new Error(err.detail || `HTTP ${resp.status}`)
    }
    const data = await resp.json()
    batchResults.value = data.results || []
    batchProgress.value = batchResults.value.length
  } catch (e) {
    errorMessage.value = e.message
  } finally {
    batchLoading.value = false
  }
}

// --- 增量追踪 ---
const trackUrl = ref('')
const trackLoading = ref(false)
const trackResult = ref(null)

async function doTrackCheck() {
  trackLoading.value = true
  trackResult.value = null
  try {
    const resp = await fetch('/api/crawler/incremental/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: trackUrl.value }),
    })
    if (!resp.ok) {
      const err = await resp.json()
      throw new Error(err.detail || `HTTP ${resp.status}`)
    }
    trackResult.value = await resp.json()
  } catch (e) {
    errorMessage.value = e.message
  } finally {
    trackLoading.value = false
  }
}

async function doTrackStatus() {
  trackLoading.value = true
  trackResult.value = null
  try {
    const resp = await fetch('/api/crawler/incremental/status')
    if (!resp.ok) {
      const err = await resp.json()
      throw new Error(err.detail || `HTTP ${resp.status}`)
    }
    trackResult.value = await resp.json()
  } catch (e) {
    errorMessage.value = e.message
  } finally {
    trackLoading.value = false
  }
}

// --- helpers ---
function formatBytes(bytes) {
  if (!bytes) return ''
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function formatTime(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function renderMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(.+)$/gm, (m) => m.startsWith('<') ? m : `<p>${m}</p>`)
}
</script>

<style scoped>
.overlay-enter-active, .overlay-leave-active { transition: opacity 0.25s ease; }
.overlay-enter-from, .overlay-leave-to { opacity: 0; }
</style>
