<template>
  <div>
    <div class="max-w-3xl mx-auto px-6 md:px-10 pb-24">
      <!-- Hero -->
      <section class="pt-8 pb-12 animate-slide-down">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs text-muted tracking-[0.2em] mb-3 font-mono">INTELLIGENT SEARCH</p>
            <h1 class="text-2xl md:text-3xl font-bold text-white tracking-tight leading-tight">
              智能搜索
              <span class="text-muted font-normal">&</span>
              知识发现
            </h1>
            <p class="text-sm text-muted mt-2 max-w-lg">
              输入主题关键词，搜索相关网站并基于多来源智能生成文档
            </p>
          </div>
          <div class="flex items-center gap-2">
            <div v-if="zhihuLoggedIn" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-neon-green/[0.06] border border-neon-green/[0.15]">
              <span class="w-1.5 h-1.5 rounded-full bg-neon-green" />
              <span class="text-xs text-neon-green/80">知乎已登录</span>
            </div>
            <button v-else @click="loginZhihu" :disabled="isLoggingIn"
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06] hover:border-white/[0.12] hover:bg-white/[0.05] transition-all text-xs text-muted hover:text-white">
              <svg v-if="isLoggingIn" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3.5"/><path class="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"/></svg>
              <span>{{ isLoggingIn ? '等待登录...' : '登录知乎' }}</span>
            </button>
          </div>
        </div>
      </section>

      <!-- Search Bar -->
      <section class="animate-slide-up stagger-1">
        <div class="card-glass p-6 md:p-8 space-y-5">
          <div>
            <label class="block text-xs font-medium text-muted mb-2 tracking-wide">搜索主题</label>
            <div class="flex gap-2.5">
              <input
                v-model="query"
                type="text"
                placeholder="输入关键词，如：养鱼知识、Python 异步编程..."
                class="input-glass flex-1"
                @keyup.enter="doSearch"
              />
              <button
                @click="doSearch"
                :disabled="isSearching || !query.trim()"
                class="btn-gradient px-5 py-3 flex items-center gap-2 whitespace-nowrap"
              >
                <svg v-if="isSearching" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3.5"/><path class="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                <span class="text-sm">{{ isSearching ? '搜索中' : '搜索' }}</span>
              </button>
            </div>
          </div>

          <div class="flex items-center gap-3">
            <span class="text-xs text-muted tracking-wide">数量</span>
            <select v-model.number="maxResults" class="select-glass text-sm">
              <option :value="5">5 条</option>
              <option :value="10">10 条</option>
              <option :value="15">15 条</option>
              <option :value="20">20 条</option>
            </select>
          </div>
        </div>
      </section>

      <!-- Existing RAG Stores -->
      <section v-if="ragStores.length > 0" class="pt-10 animate-slide-up stagger-2">
        <div class="card-glass p-6 md:p-8">
          <div class="flex items-center justify-between mb-5">
            <h2 class="text-lg font-semibold text-white tracking-tight">
              已有知识库
              <span class="text-sm font-normal text-muted ml-1.5">{{ ragStores.length }} 个</span>
            </h2>
            <button @click="loadRagStores" class="btn-outline text-xs">
              <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
              <span>刷新</span>
            </button>
          </div>
          <div class="space-y-2">
            <div v-for="store in ragStores" :key="store.rag_id"
              class="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/[0.04] hover:bg-white/[0.04] transition-all"
            >
              <div class="flex items-center gap-3">
                <span class="w-2 h-2 rounded-full shrink-0"
                  :class="store.status === 'ready' ? 'bg-neon-green' : store.status === 'building' ? 'bg-amber-warm animate-pulse' : 'bg-red-400'"
                />
                <div>
                  <p class="text-sm text-white font-mono">{{ store.rag_id }}</p>
                  <p class="text-xs text-muted">{{ store.url_count }} URL · {{ store.chunk_count }} 块 · {{ formatTime(store.created_at) }}</p>
                </div>
              </div>
              <button v-if="store.status === 'ready'" @click="generateFromRagStore(store)"
                class="btn-outline text-xs flex items-center gap-1"
              >
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                <span>生成文档</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Results -->
      <section v-if="searchResults.length > 0" class="pt-10 animate-slide-up stagger-2">
        <div class="card-glass p-6 md:p-8">
          <div class="flex items-center justify-between mb-5">
            <h2 class="text-lg font-semibold text-white tracking-tight">
              搜索结果
              <span class="text-sm font-normal text-muted ml-1.5">{{ searchResults.length }} 条</span>
            </h2>
            <div class="flex gap-1.5">
              <button @click="selectAll" class="text-xs text-muted hover:text-white px-2.5 py-1 rounded-md hover:bg-white/[0.04] transition-all">全选</button>
              <button @click="deselectAll" class="text-xs text-muted hover:text-white px-2.5 py-1 rounded-md hover:bg-white/[0.04] transition-all">反选</button>
            </div>
          </div>

          <div class="space-y-2">
            <div
              v-for="(result, index) in searchResults"
              :key="index"
              class="group bg-white/[0.02] border rounded-xl p-4 transition-all cursor-pointer"
              :class="selectedIndices.has(index)
                ? 'border-neon-green/[0.2] bg-neon-green/[0.02]'
                : 'border-white/[0.04] hover:border-white/[0.08] hover:bg-white/[0.03]'"
              @click="toggleSelect(index)"
            >
              <div class="flex items-start gap-3">
                <input
                  type="checkbox"
                  :checked="selectedIndices.has(index)"
                  class="checkbox-glass mt-0.5"
                  @click.stop
                  @change="toggleSelect(index)"
                />
                <div class="flex-1 min-w-0">
                  <h3 class="text-sm font-medium text-white mb-1 group-hover:text-neon-green transition-colors">{{ result.title }}</h3>
                  <p class="text-xs text-muted mb-2 line-clamp-2 leading-relaxed">{{ result.snippet }}</p>
                  <p class="text-xs text-cyan-blue/70 truncate font-mono">{{ result.url }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- No Results -->
      <section v-if="!isSearching && hasSearched && searchResults.length === 0" class="pt-10 animate-slide-up">
        <div class="card-glass p-12 text-center">
          <div class="w-12 h-12 rounded-2xl bg-amber-warm/[0.06] border border-amber-warm/[0.1] flex items-center justify-center mx-auto mb-4">
            <svg class="w-5 h-5 text-amber-warm/50" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
          </div>
          <p class="text-white font-medium mb-1">未找到相关结果</p>
          <p class="text-sm text-muted">尝试使用不同的关键词重新搜索</p>
        </div>
      </section>

      <!-- Initial Empty -->
      <section v-if="!hasSearched" class="pt-10 animate-slide-up">
        <div class="card-glass p-12 text-center">
          <div class="w-12 h-12 rounded-2xl bg-cyan-blue/[0.04] border border-cyan-blue/[0.08] flex items-center justify-center mx-auto mb-4">
            <svg class="w-5 h-5 text-cyan-blue/40" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          </div>
          <p class="text-white font-medium mb-1">智能搜索区域</p>
          <p class="text-sm text-muted">输入主题关键词，搜索相关网站资源</p>
        </div>
      </section>

      <!-- Action Bar -->
      <section v-if="selectedCount > 0" class="pt-10 animate-slide-up stagger-3">
        <div class="card-glass card-active p-6 md:p-8 space-y-4">
          <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-neon-green animate-pulse" />
              <span class="text-sm text-white">
                已选择 <span class="text-neon-green font-semibold">{{ selectedCount }}</span> 个网站
              </span>
            </div>

            <div class="flex flex-wrap items-center gap-2.5">
              <select v-model="docType" class="select-glass text-sm">
                <option value="tech_doc">技术文档</option>
                <option value="api_doc">API 文档</option>
                <option value="readme">README</option>
                <option value="summary">摘要总结</option>
              </select>

              <select v-model="integrationMode" class="select-glass text-sm">
                <option value="merge">合并模式</option>
                <option value="separate">独立模式</option>
              </select>

              <select v-model="exportFormat" class="select-glass text-sm">
                <option value="md">Markdown</option>
                <option value="txt">纯文本</option>
                <option value="ppt">PPT</option>
              </select>

              <button
                @click="generateFromSelected"
                :disabled="isGenerating"
                class="btn-gradient px-5 py-2.5 flex items-center gap-2 text-sm"
              >
                <svg v-if="isGenerating" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3.5"/><path class="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                <span>{{ isGenerating ? '生成中' : '生成文档' }}</span>
              </button>
            </div>
          </div>

          <div class="flex items-center gap-4 pt-1">
            <div class="flex-1 h-px bg-white/[0.04]" />
            <span class="text-[11px] text-muted whitespace-nowrap font-mono">
              {{ integrationMode === 'merge' ? '所有网站 → 一份综合文档' : '每个网站 → 独立文档' }}
            </span>
            <div class="flex-1 h-px bg-white/[0.04]" />
          </div>
        </div>
      </section>

      <!-- Document Output -->
      <section v-if="documentContent" class="pt-10 animate-slide-up stagger-4">
        <div class="card-glass p-6 md:p-8">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-5">
            <div class="flex items-center gap-4">
              <h2 class="text-lg font-semibold text-white tracking-tight">文档输出</h2>
              <div class="flex gap-1 p-0.5 rounded-md bg-white/[0.03] border border-white/[0.04]">
                <button @click="previewMode = 'raw'" class="px-2.5 py-1 text-xs rounded transition-all duration-200"
                  :class="previewMode === 'raw' ? 'bg-white/[0.06] text-white' : 'text-muted hover:text-white'">原文</button>
                <button @click="previewMode = 'rendered'" class="px-2.5 py-1 text-xs rounded transition-all duration-200"
                  :class="previewMode === 'rendered' ? 'bg-white/[0.06] text-white' : 'text-muted hover:text-white'">渲染</button>
              </div>
            </div>
            <button @click="exportDocument" class="btn-outline">
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
              <span>导出文档</span>
            </button>
          </div>

          <div v-if="previewMode === 'rendered'" class="bg-base/60 rounded-xl p-5 overflow-auto max-h-[55vh] border border-white/[0.03]">
            <div class="markdown-body" v-html="renderedContent" />
          </div>
          <div v-else class="bg-base/60 rounded-xl p-5 overflow-auto max-h-[55vh] border border-white/[0.03]">
            <pre class="text-sm text-muted whitespace-pre-wrap font-mono leading-relaxed">{{ documentContent }}</pre>
          </div>
        </div>
      </section>
    </div>

    <!-- Loading Overlay -->
    <Transition name="overlay">
      <div v-if="isGenerating" class="fixed inset-0 z-50 flex items-center justify-center" style="background: rgba(6,6,8,0.7); backdrop-filter: blur(4px);">
        <div class="text-center animate-scale-in">
          <div class="relative w-14 h-14 mx-auto mb-5">
            <div class="absolute inset-0 rounded-full border-2 border-neon-green/10" />
            <div class="absolute inset-1 rounded-full border-2 border-transparent border-t-neon-green animate-spin" />
          </div>
          <p class="text-sm text-white font-medium">正在生成文档</p>
          <p v-if="generatingProgress" class="text-xs text-muted mt-1.5 max-w-xs mx-auto font-mono leading-relaxed">{{ generatingProgress }}</p>
        </div>
      </div>
    </Transition>

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
import { ref, computed, onMounted, watch } from 'vue'
import { marked } from 'marked'
import apiService from '../services/api'

// 状态持久化键名
const STORAGE_KEY = 'docgen_searchpage_state'

// 从sessionStorage恢复状态
const loadState = () => {
  try {
    const saved = sessionStorage.getItem(STORAGE_KEY)
    if (saved) {
      const data = JSON.parse(saved)
      return {
        query: data.query || '',
        maxResults: data.maxResults || 10,
        searchResults: data.searchResults || [],
        selectedIndices: data.selectedIndices || [],
        docType: data.docType || 'tech_doc',
        integrationMode: data.integrationMode || 'merge',
        exportFormat: data.exportFormat || 'md',
        documentContent: data.documentContent || '',
        previewMode: data.previewMode || 'raw',
      }
    }
  } catch (e) {
    console.warn('Failed to load state from sessionStorage:', e)
  }
  return { query: '', maxResults: 10, searchResults: [], selectedIndices: [], docType: 'tech_doc', integrationMode: 'merge', exportFormat: 'md', documentContent: '', previewMode: 'raw' }
}

const savedState = loadState()

const query = ref(savedState.query)
const maxResults = ref(savedState.maxResults)
const isSearching = ref(false)
const hasSearched = ref(savedState.searchResults.length > 0)
const searchResults = ref(savedState.searchResults)
const selectedIndices = ref(new Set(savedState.selectedIndices))
const docType = ref(savedState.docType)
const integrationMode = ref(savedState.integrationMode)
const exportFormat = ref(savedState.exportFormat)
const isGenerating = ref(false)
const generatingProgress = ref('')
const errorMessage = ref('')
const documentContent = ref(savedState.documentContent)
const previewMode = ref(savedState.previewMode)
const selectedCount = ref(selectedIndices.value.size)
const isLoggingIn = ref(false)
const zhihuLoggedIn = ref(false)
const ragStores = ref([])

// 监听状态变化并保存
const saveState = () => {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
      query: query.value,
      maxResults: maxResults.value,
      searchResults: searchResults.value,
      selectedIndices: Array.from(selectedIndices.value),
      docType: docType.value,
      integrationMode: integrationMode.value,
      exportFormat: exportFormat.value,
      documentContent: documentContent.value,
      previewMode: previewMode.value,
    }))
  } catch (e) {
    console.warn('Failed to save state to sessionStorage:', e)
  }
}

watch([query, maxResults, searchResults, docType, integrationMode, exportFormat, documentContent, previewMode], saveState, { deep: true })
// 监听selectedIndices变化
watch(selectedIndices, () => {
  selectedCount.value = selectedIndices.value.size
  saveState()
}, { deep: true })

marked.setOptions({ breaks: true, gfm: true })

const checkZhihuLoginState = async () => {
  try {
    const state = await apiService.getLoginState()
    zhihuLoggedIn.value = state.sites?.zhihu?.has_saved_state || false
  } catch (e) {
    zhihuLoggedIn.value = false
  }
}

onMounted(() => {
  checkZhihuLoginState()
  loadRagStores()
})

const formatTime = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const loadRagStores = async () => {
  try {
    const resp = await fetch('/api/rag/list')
    if (resp.ok) {
      const data = await resp.json()
      ragStores.value = data.stores || []
    }
  } catch (e) {
    console.warn('Failed to load RAG stores:', e)
  }
}

const generateFromRagStore = async (store) => {
  isGenerating.value = true
  documentContent.value = ''
  errorMessage.value = ''
  generatingProgress.value = '基于已有知识库生成文档...'

  try {
    const gr = await apiService.generateFromRag(store.rag_id, docType.value, 'merge', exportFormat.value, query.value || '综合文档')
    if (!gr.success) throw new Error(gr.message || '文档生成启动失败')
    const doc = await apiService.pollDocumentStatus(gr.document_id)
    documentContent.value = doc.content || ''
    await loadRagStores()
  } catch (e) {
    errorMessage.value = e.message
  } finally {
    isGenerating.value = false
    generatingProgress.value = ''
  }
}

const loginZhihu = async () => {
  if (isLoggingIn.value) return
  isLoggingIn.value = true
  try {
    const r = await apiService.startLogin('zhihu')
    if (!r.success && r.status !== 'waiting_login') {
      throw new Error(r.message || '启动登录失败')
    }
    const pollInterval = setInterval(async () => {
      try {
        const status = await apiService.getLoginStatus()
        if (status.status === 'success') {
          zhihuLoggedIn.value = true
          isLoggingIn.value = false
          clearInterval(pollInterval)
        } else if (status.status === 'error' || status.status === 'timeout') {
          isLoggingIn.value = false
          clearInterval(pollInterval)
          errorMessage.value = status.message || '登录失败'
        }
      } catch (e) {
        isLoggingIn.value = false
        clearInterval(pollInterval)
      }
    }, 3000)
  } catch (e) {
    isLoggingIn.value = false
    errorMessage.value = e.message
  }
}

const renderedContent = computed(() => {
  if (!documentContent.value) return ''
  return marked(documentContent.value)
})

const toggleSelect = (index) => {
  const s = new Set(selectedIndices.value)
  s.has(index) ? s.delete(index) : s.add(index)
  selectedIndices.value = s
  selectedCount.value = s.size
}

const selectAll = () => {
  const all = new Set(searchResults.value.map((_, i) => i))
  selectedIndices.value = all
  selectedCount.value = all.size
}

const deselectAll = () => {
  selectedIndices.value = new Set()
  selectedCount.value = 0
}

const doSearch = async () => {
  if (!query.value.trim() || isSearching.value) return
  isSearching.value = true
  errorMessage.value = ''
  searchResults.value = []
  selectedIndices.value = new Set()
  selectedCount.value = 0
  try {
    const r = await apiService.searchWeb(query.value.trim(), maxResults.value)
    hasSearched.value = true
    if (r.success) searchResults.value = r.results || []
    else throw new Error(r.detail || '搜索失败')
  } catch (e) {
    errorMessage.value = e.message
  } finally {
    isSearching.value = false
  }
}

const generateFromSelected = async () => {
  if (selectedCount.value === 0) return

  const urls = []
  for (const idx of selectedIndices.value) {
    if (searchResults.value[idx]) urls.push(searchResults.value[idx].url)
  }

  isGenerating.value = true
  documentContent.value = ''
  errorMessage.value = ''
  generatingProgress.value = `正在提交 ${urls.length} 个网站构建知识库...`

  try {
    const br = await apiService.buildRag(urls, docType.value)
    if (!br.success) throw new Error(br.message || '启动知识库构建失败')

    generatingProgress.value = `知识库构建中（${br.sources_count} 来源），正在抓取并向量化...`
    const rr = await apiService.pollRagStatus(br.rag_id)
    await loadRagStores()

    if (integrationMode.value === 'merge') {
      generatingProgress.value = '合并模式：基于知识库生成综合文档...'
      const gr = await apiService.generateFromRag(br.rag_id, docType.value, 'merge', exportFormat.value, query.value)
      if (!gr.success) throw new Error(gr.message || '文档生成启动失败')
      const doc = await apiService.pollDocumentStatus(gr.document_id)
      documentContent.value = doc.content || ''
    } else {
      generatingProgress.value = '独立模式：逐个生成文档...'
      const gr = await apiService.generateFromRag(br.rag_id, docType.value, 'separate', exportFormat.value)
      if (!gr.success) throw new Error(gr.message || '文档生成启动失败')
      const docs = gr.documents || []
      let done = 0
      for (const d of docs) {
        try {
          generatingProgress.value = `独立模式：${done}/${docs.length} 已完成`
          await apiService.pollDocumentStatus(d.document_id)
          done++
        } catch (error) {
          console.warn(`Failed to generate doc for ${d.url}:`, error)
        }
      }
      generatingProgress.value = `${done}/${docs.length} 个文档生成完成！请到首页查看。`
      await new Promise(r => setTimeout(r, 2000))
    }
  } catch (e) {
    errorMessage.value = e.message
  } finally {
    isGenerating.value = false
    generatingProgress.value = ''
  }
}

const exportDocument = () => {
  if (!documentContent.value) return

  const fmts = {
    md: { type: 'text/markdown', ext: '.md' },
    txt: { type: 'text/plain', ext: '.txt' },
    ppt: { type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation', ext: '.pptx' },
  }
  const f = fmts[exportFormat.value] || fmts.md
  let content = documentContent.value
  if (exportFormat.value === 'txt') {
    content = content.replace(/[#*`>\-\[\]]/g, '').replace(/\n{2,}/g, '\n\n').trim()
  }

  const blob = new Blob([content], { type: f.type })
  const u = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = u; a.download = `rag_document_${Date.now()}${f.ext}`
  document.body.appendChild(a); a.click(); document.body.removeChild(a)
  URL.revokeObjectURL(u)
}
</script>

<style scoped>
.overlay-enter-active, .overlay-leave-active { transition: opacity 0.25s ease; }
.overlay-enter-from, .overlay-leave-to { opacity: 0; }
</style>
