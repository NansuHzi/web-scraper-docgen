<template>
  <div>
    <div class="max-w-3xl mx-auto px-6 md:px-10 pb-24">
      <!-- Hero -->
      <section class="pt-8 pb-12 animate-slide-down">
        <p class="text-xs text-muted tracking-[0.2em] mb-3 font-mono">SINGLE URL</p>
        <h1 class="text-2xl md:text-3xl font-bold text-white tracking-tight leading-tight">
          网页内容抓取
          <span class="text-muted font-normal">&</span>
          文档生成
        </h1>
        <p class="text-sm text-muted mt-2 max-w-lg">
          输入任意网页 URL，智能提取内容并生成结构化技术文档
        </p>
      </section>

      <!-- Input Card -->
      <section class="animate-slide-up stagger-1">
        <div class="card-glass p-6 md:p-8 space-y-6">
          <!-- URL Input -->
          <div>
            <label class="block text-xs font-medium text-muted mb-2 tracking-wide">目标网址</label>
            <div class="relative">
              <input
                v-model="url"
                type="text"
                placeholder="https://example.com"
                class="input-glass"
                @input="validateUrl"
                @blur="validateUrl"
              />
              <button
                v-if="url"
                @click="url = ''"
                class="absolute right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-white/[0.06] flex items-center justify-center text-muted hover:text-white hover:bg-white/[0.1] transition-all"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
              </button>
            </div>
          </div>

          <!-- Doc Type -->
          <div>
            <label class="block text-xs font-medium text-muted mb-3 tracking-wide">文档类型</label>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
              <label
                v-for="doc in docTypes"
                :key="doc.value"
                class="relative flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer transition-all duration-300 border"
                :class="docType === doc.value
                  ? 'border-neon-green/[0.25] bg-neon-green/[0.04]'
                  : 'border-white/[0.05] bg-white/[0.02] hover:border-white/[0.1]'"
              >
                <input type="radio" :value="doc.value" v-model="docType" class="sr-only" />
                <span class="text-base">{{ doc.icon }}</span>
                <span class="text-sm font-medium" :class="docType === doc.value ? 'text-neon-green' : 'text-muted'">{{ doc.label }}</span>
                <span v-if="docType === doc.value" class="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-neon-green" />
              </label>
            </div>
          </div>

          <!-- Export Format -->
          <div>
            <label class="block text-xs font-medium text-muted mb-3 tracking-wide">导出格式</label>
            <div class="flex gap-2">
              <label
                v-for="fmt in exportFormats"
                :key="fmt.value"
                class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-lg cursor-pointer transition-all duration-300 border text-sm font-medium"
                :class="exportFormat === fmt.value
                  ? 'border-cyan-blue/[0.3] bg-cyan-blue/[0.05] text-cyan-blue'
                  : 'border-white/[0.05] bg-white/[0.02] text-muted hover:border-white/[0.1]'"
              >
                <input type="radio" :value="fmt.value" v-model="exportFormat" class="sr-only" />
                {{ fmt.label }}
              </label>
            </div>
          </div>

          <!-- Generate Button -->
          <button
            @click="generateDocument"
            :disabled="isLoading || !url.trim()"
            class="btn-gradient w-full py-3.5 text-base flex items-center justify-center gap-2.5"
          >
            <svg v-if="isLoading" class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3.5" />
              <path class="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span>{{ isLoading ? '正在生成文档...' : '生成文档' }}</span>
          </button>
        </div>
      </section>

      <!-- Output Section -->
      <section v-if="documentContent || (!isLoading && !documentContent)" class="pt-10 animate-slide-up stagger-2">
        <div class="card-glass p-6 md:p-8">
          <!-- Output Header -->
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-5">
            <div class="flex items-center gap-4">
              <h2 class="text-lg font-semibold text-white tracking-tight">文档输出</h2>
              <div v-if="documentContent" class="flex gap-1 p-0.5 rounded-md bg-white/[0.03] border border-white/[0.04]">
                <button @click="previewMode = 'raw'" class="px-2.5 py-1 text-xs rounded transition-all duration-200"
                  :class="previewMode === 'raw' ? 'bg-white/[0.06] text-white' : 'text-muted hover:text-white'">原文</button>
                <button @click="previewMode = 'rendered'" class="px-2.5 py-1 text-xs rounded transition-all duration-200"
                  :class="previewMode === 'rendered' ? 'bg-white/[0.06] text-white' : 'text-muted hover:text-white'">渲染</button>
              </div>
            </div>
            <button v-if="documentContent" @click="exportDocument" class="btn-outline">
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
              <span>导出文档</span>
            </button>
          </div>

          <!-- Rendered -->
          <div v-if="documentContent && previewMode === 'rendered'" class="bg-base/60 rounded-xl p-5 overflow-auto max-h-[55vh] border border-white/[0.03]">
            <div class="markdown-body" v-html="renderedContent" />
          </div>

          <!-- Raw -->
          <div v-else-if="documentContent" class="bg-base/60 rounded-xl p-5 overflow-auto max-h-[55vh] border border-white/[0.03]">
            <pre class="text-sm text-muted whitespace-pre-wrap font-mono leading-relaxed">{{ documentContent }}</pre>
          </div>

          <!-- Empty -->
          <div v-else class="py-16 text-center">
            <div class="w-12 h-12 rounded-2xl bg-neon-green/[0.04] border border-neon-green/[0.08] flex items-center justify-center mx-auto mb-4">
              <svg class="w-5 h-5 text-neon-green/40" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
            </div>
            <p class="text-sm text-muted">输入网址并点击生成，文档将在此显示</p>
          </div>
        </div>
      </section>

      <!-- History -->
      <section v-if="history.length > 0" class="pt-10 animate-slide-up stagger-3">
        <div class="card-glass p-6 md:p-8">
          <h2 class="text-lg font-semibold text-white tracking-tight mb-5">历史记录</h2>
          <div class="grid gap-2 md:grid-cols-2">
            <div
              v-for="(item, i) in history"
              :key="item.document_id"
              class="group bg-white/[0.02] border border-white/[0.04] rounded-xl p-4 hover:bg-white/[0.04] hover:border-white/[0.08] transition-all cursor-pointer"
              :style="{ animationDelay: `${0.3 + i * 0.04}s` }"
              @click="loadHistoryItem(item)"
            >
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-medium text-neon-green">{{ docLabel(item.doc_type) }}</span>
                <span class="text-[11px] text-muted font-mono">{{ formatDate(item.created_at) }}</span>
              </div>
              <p class="text-sm text-muted truncate">{{ item.url }}</p>
              <div class="flex items-center gap-2 mt-2">
                <span v-if="item.from_cache" class="tag tag-green">缓存</span>
                <span class="tag">{{ item.format }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- Loading Overlay -->
    <Transition name="overlay">
      <div v-if="isLoading" class="fixed inset-0 z-50 flex items-center justify-center" style="background: rgba(6,6,8,0.7); backdrop-filter: blur(4px);">
        <div class="text-center animate-scale-in">
          <div class="relative w-14 h-14 mx-auto mb-5">
            <div class="absolute inset-0 rounded-full border-2 border-neon-green/10" />
            <div class="absolute inset-1 rounded-full border-2 border-transparent border-t-neon-green animate-spin" />
          </div>
          <p class="text-sm text-white font-medium">正在生成文档</p>
          <p v-if="loadingProgress" class="text-xs text-muted mt-1.5 font-mono">{{ loadingProgress }}</p>
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
import { ref, computed, onMounted } from 'vue'
import { marked } from 'marked'
import apiService from '../services/api'

const url = ref('')
const docType = ref('tech_doc')
const urlError = ref('')
const isLoading = ref(false)
const documentContent = ref('')
const errorMessage = ref('')
const loadingProgress = ref('')
const previewMode = ref('raw')
const history = ref([])
const exportFormat = ref('md')

const docTypes = [
  { value: 'tech_doc', label: '技术文档', icon: '📝' },
  { value: 'api_doc', label: 'API 文档', icon: '🔌' },
  { value: 'readme', label: 'README', icon: '📖' },
  { value: 'summary', label: '摘要总结', icon: '📋' },
]

const exportFormats = [
  { value: 'md', label: 'Markdown' },
  { value: 'txt', label: '纯文本' },
  { value: 'ppt', label: 'PPT' },
]

marked.setOptions({ breaks: true, gfm: true })

const renderedContent = computed(() => {
  if (!documentContent.value) return ''
  return marked(documentContent.value)
})

const docLabel = (type) => {
  const m = { tech_doc: '技术文档', api_doc: 'API 文档', readme: 'README', summary: '摘要总结' }
  return m[type] || type
}

onMounted(async () => {
  try {
    const result = await apiService.getHistory()
    history.value = result.history || []
  } catch (error) {
    console.error('Failed to load history:', error)
  }
})

const loadHistoryItem = async (item) => {
  try {
    const result = await apiService.getDocument(item.document_id)
    if (result.content) {
      documentContent.value = result.content
      docType.value = item.doc_type
      exportFormat.value = item.format || 'md'
    }
  } catch {
    errorMessage.value = '加载历史文档失败'
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const validateUrl = () => {
  if (!url.value) { urlError.value = ''; return }
  if (!url.value.trim().includes('.')) urlError.value = '请输入有效的网址'
  else urlError.value = ''
}

const generateDocument = async () => {
  if (!url.value) { urlError.value = '请输入网址'; return }
  validateUrl()
  if (urlError.value) return

  isLoading.value = true
  documentContent.value = ''
  errorMessage.value = ''
  loadingProgress.value = '正在验证请求...'

  try {
    loadingProgress.value = '正在验证 URL 和文档类型...'
    const vr = await apiService.validateRequest(url.value, docType.value)
    if (!vr.valid) throw new Error(vr.message || '验证失败')

    loadingProgress.value = '启动文档生成...'
    const gr = await apiService.generateDocument(url.value, docType.value, exportFormat.value)
    if (!gr.success) throw new Error(gr.message || '启动失败')

    loadingProgress.value = '正在抓取网页内容...'
    const doc = await apiService.pollDocumentStatus(gr.document_id)
    if (doc.status === 'failed') throw new Error(doc.error || '生成失败')
    if (!doc.content || doc.content.trim() === '') throw new Error('生成的文档内容为空')

    documentContent.value = doc.content
    const hr = await apiService.getHistory()
    history.value = hr.history || []
  } catch (e) {
    errorMessage.value = e.message
  } finally {
    isLoading.value = false
    loadingProgress.value = ''
  }
}

const exportDocument = () => {
  if (!documentContent.value) return
  const exts = { md: { type: 'text/markdown', ext: '.md' }, txt: { type: 'text/plain', ext: '.txt' }, ppt: { type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation', ext: '.pptx' } }
  const cfg = exts[exportFormat.value] || exts.md
  let content = documentContent.value
  if (exportFormat.value === 'txt') content = content.replace(/[#*`>\-\[\]]/g, '').replace(/\n{2,}/g, '\n\n').trim()
  const blob = new Blob([content], { type: cfg.type })
  const u = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = u; a.download = `document_${docType.value}_${Date.now()}${cfg.ext}`
  document.body.appendChild(a); a.click(); document.body.removeChild(a)
  URL.revokeObjectURL(u)
}
</script>

<style scoped>
.overlay-enter-active, .overlay-leave-active { transition: opacity 0.25s ease; }
.overlay-enter-from, .overlay-leave-to { opacity: 0; }
</style>
