<template>
  <div class="min-h-screen bg-dark-bg">
    <!-- 导航栏 -->
    <nav class="fixed top-0 left-0 right-0 z-50 glass">
      <div class="max-w-2xl mx-auto px-4 md:px-8 py-4 flex justify-between items-center">
        <div class="text-xl md:text-2xl font-bold bg-gradient-to-r from-neon-green to-cyan-blue bg-clip-text text-transparent">
          DocGen
        </div>
        <span class="text-gray-400 text-sm hidden md:block">智能文档生成器</span>
      </div>
    </nav>

    <!-- 主内容区域 -->
    <main class="max-w-4xl mx-auto px-4 md:px-8 pt-24 pb-16">
      <!-- 输入区域 - 居中显示 -->
      <section class="py-16">
        <div class="card-glass p-8">
            <!-- URL输入 -->
            <div class="mb-6">
              <label class="block text-gray-400 mb-2 text-sm">目标网址</label>
              <div class="relative">
                <input
                  v-model="url"
                  type="text"
                  placeholder="请输入要爬取的网址，如: https://example.com"
                  class="input-glass w-full pr-10"
                  @input="validateUrl"
                  @blur="validateUrl"
                />
                <button
                  v-if="url"
                  @click="url = ''"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- 文档类型选择 -->
            <div class="mb-6">
              <label class="block text-gray-400 mb-3 text-sm">文档类型</label>
              <div class="flex gap-3">
                <label
                  v-for="doc in docTypes"
                  :key="doc.value"
                  class="flex-1 flex items-center justify-center px-4 py-3 rounded-xl cursor-pointer transition-all duration-300 border"
                  :class="docType === doc.value ? 'bg-neon-green/20 border-neon-green' : 'bg-dark-surface border-dark-border hover:border-neon-green/50'"
                >
                  <input
                    type="radio"
                    :value="doc.value"
                    v-model="docType"
                    class="sr-only"
                  />
                  <span class="text-lg mr-2">{{ doc.icon }}</span>
                  <span class="text-sm" :class="docType === doc.value ? 'text-neon-green' : 'text-gray-400'">{{ doc.label }}</span>
                </label>
              </div>
            </div>

            <!-- 导出格式选择 -->
            <div class="mb-6">
              <label class="block text-gray-400 mb-3 text-sm">导出格式</label>
              <div class="flex gap-3">
                <label
                  v-for="fmt in exportFormats"
                  :key="fmt.value"
                  class="flex-1 flex items-center justify-center px-4 py-3 rounded-xl cursor-pointer transition-all duration-300 border"
                  :class="exportFormat === fmt.value ? 'bg-cyan-blue/20 border-cyan-blue' : 'bg-dark-surface border-dark-border hover:border-cyan-blue/50'"
                >
                  <input
                    type="radio"
                    :value="fmt.value"
                    v-model="exportFormat"
                    class="sr-only"
                  />
                  <span class="text-sm" :class="exportFormat === fmt.value ? 'text-cyan-blue' : 'text-gray-400'">{{ fmt.label }}</span>
                </label>
              </div>
            </div>

            <!-- 生成按钮 -->
            <button
              @click="generateDocument"
              :disabled="isLoading || !url.trim()"
              class="w-full py-4 bg-gradient-to-r from-neon-green to-cyan-blue text-dark-bg font-bold rounded-xl transition-all duration-300 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              :class="{ 'hover:scale-[1.02]': !isLoading && url.trim() }"
            >
              <svg v-if="isLoading" class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>{{ isLoading ? '生成中...' : '生成文档' }}</span>
            </button>
        </div>
      </section>

      <!-- 输出区域 -->
      <section class="py-8">
        <div class="card-glass p-6 md:p-8">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
            <div class="flex items-center gap-4">
              <h2 class="text-xl font-bold text-white">文档输出</h2>
              <div v-if="documentContent" class="flex gap-2">
                <button
                  @click="previewMode = 'raw'"
                  class="px-3 py-1 text-xs rounded-lg transition-all"
                  :class="previewMode === 'raw' ? 'bg-neon-green/20 text-neon-green' : 'bg-dark-surface text-gray-400 hover:text-white'"
                >
                  原文
                </button>
                <button
                  @click="previewMode = 'rendered'"
                  class="px-3 py-1 text-xs rounded-lg transition-all"
                  :class="previewMode === 'rendered' ? 'bg-neon-green/20 text-neon-green' : 'bg-dark-surface text-gray-400 hover:text-white'"
                >
                  渲染
                </button>
              </div>
            </div>
            <button
              v-if="documentContent"
              @click="exportDocument"
              class="px-4 py-2 bg-transparent border border-neon-green text-neon-green font-semibold rounded-lg hover:bg-neon-green/10 transition-all duration-300 flex items-center gap-2 text-sm"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              <span>导出文档</span>
            </button>
          </div>

          <!-- Markdown预览 - 渲染模式 -->
          <div v-if="documentContent && previewMode === 'rendered'" class="bg-dark-bg rounded-xl p-4 overflow-x-auto max-h-[60vh] overflow-y-auto">
            <div class="markdown-body text-gray-300 text-sm" v-html="renderedContent"></div>
          </div>

          <!-- Markdown预览 - 原文模式 -->
          <div v-else-if="documentContent" class="bg-dark-bg rounded-xl p-4 overflow-x-auto max-h-[60vh] overflow-y-auto">
            <pre class="text-gray-300 text-sm whitespace-pre-wrap font-mono">{{ documentContent }}</pre>
          </div>

          <!-- 空状态提示 -->
          <div v-if="!documentContent" class="bg-dark-bg/50 rounded-xl p-12 text-center">
            <div class="w-16 h-16 bg-neon-green/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <span class="text-3xl">📄</span>
            </div>
            <h3 class="text-lg font-semibold text-gray-300 mb-2">文档输出区域</h3>
            <p class="text-gray-500 text-sm">输入目标网址并点击"生成文档"按钮，生成的文档内容将在这里显示</p>
          </div>
        </div>
      </section>

      <!-- 历史记录区域 -->
      <section v-if="history.length > 0" class="py-8">
        <div class="card-glass p-6 md:p-8">
          <h2 class="text-xl font-bold text-white mb-4">历史记录</h2>
          <div class="grid gap-3 md:grid-cols-2">
            <div
              v-for="item in history"
              :key="item.document_id"
              class="bg-dark-bg/50 rounded-xl p-4 hover:bg-dark-bg/80 transition-all cursor-pointer"
              @click="loadHistoryItem(item)"
            >
              <div class="flex items-center justify-between mb-2">
                <span class="text-neon-green text-sm font-medium">{{ item.doc_type }}</span>
                <span class="text-gray-500 text-xs">{{ formatDate(item.created_at) }}</span>
              </div>
              <p class="text-gray-400 text-sm truncate">{{ item.url }}</p>
              <div class="flex items-center gap-2 mt-2">
                <span v-if="item.from_cache" class="text-xs px-2 py-0.5 bg-cyan-blue/20 text-cyan-blue rounded">缓存</span>
                <span class="text-xs text-gray-500">{{ item.format }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- 加载状态提示 -->
    <div v-if="isLoading" class="fixed inset-0 bg-dark-bg/50 flex items-center justify-center z-50">
      <div class="text-center">
        <div class="w-12 h-12 border-4 border-neon-green/30 border-t-neon-green rounded-full animate-spin mx-auto mb-4"></div>
        <p class="text-gray-300">正在生成文档，请稍候...</p>
        <p v-if="loadingProgress" class="text-gray-500 text-sm mt-2">{{ loadingProgress }}</p>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMessage" class="fixed inset-0 bg-dark-bg/50 flex items-center justify-center z-50" @click="errorMessage = ''">
      <div class="bg-dark-surface rounded-xl p-6 max-w-md mx-4 text-center" @click.stop>
        <div class="w-12 h-12 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 class="text-white font-bold mb-2">操作失败</h3>
        <p class="text-gray-400 text-sm mb-4">{{ errorMessage }}</p>
        <button
          @click="errorMessage = ''"
          class="px-6 py-2 bg-neon-green text-dark-bg font-semibold rounded-lg hover:bg-neon-green/80 transition-colors"
        >
          确定
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { marked } from 'marked'
import apiService from './services/api'

const url = ref('')
const docType = ref('tech_doc')
const urlError = ref('')
const isLoading = ref(false)
const documentContent = ref('')
const errorMessage = ref('')
const loadingProgress = ref('')
const previewMode = ref('raw')
const history = ref([])

const docTypes = [
  { value: 'tech_doc', label: '技术文档', icon: '📝' },
  { value: 'api_doc', label: 'API文档', icon: '🔌' },
  { value: 'readme', label: 'README', icon: '📖' },
  { value: 'summary', label: '摘要总结', icon: '📋' }
]

const exportFormats = [
  { value: 'md', label: 'Markdown' },
  { value: 'txt', label: '纯文本' },
  { value: 'ppt', label: 'PPT' }
]

const exportFormat = ref('md')

marked.setOptions({
  breaks: true,
  gfm: true
})

const renderedContent = computed(() => {
  if (!documentContent.value) return ''
  return marked(documentContent.value)
})

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
  } catch (error) {
    errorMessage.value = '加载历史文档失败'
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const validateUrl = () => {
  if (!url.value) {
    urlError.value = ''
    return
  }
  
  const trimmedUrl = url.value.trim()
  
  if (!trimmedUrl.includes('.')) {
    urlError.value = '请输入有效的网址'
  } else {
    urlError.value = ''
  }
}

const generateDocument = async () => {
  if (!url.value) {
    urlError.value = '请输入网址'
    return
  }
  
  validateUrl()
  if (urlError.value) {
    return
  }

  isLoading.value = true
  documentContent.value = ''
  errorMessage.value = ''
  loadingProgress.value = '正在验证请求...'

  try {
    loadingProgress.value = '正在验证URL和文档类型...'
    const validateResult = await apiService.validateRequest(url.value, docType.value)
    
    if (!validateResult.valid) {
      throw new Error(validateResult.message || '验证失败')
    }

    loadingProgress.value = '正在启动文档生成...'
    const generateResult = await apiService.generateDocument(url.value, docType.value, exportFormat.value)
    
    if (!generateResult.success) {
      throw new Error(generateResult.message || '生成启动失败')
    }

    loadingProgress.value = '正在抓取网页内容...'
    const documentResult = await apiService.pollDocumentStatus(generateResult.document_id)
    
    if (documentResult.status === 'failed') {
      throw new Error(documentResult.error || '文档生成失败')
    }

    if (!documentResult.content || documentResult.content.trim() === '') {
      throw new Error('生成的文档内容为空')
    }

    documentContent.value = documentResult.content

    const historyResult = await apiService.getHistory()
    history.value = historyResult.history || []

  } catch (error) {
    errorMessage.value = error.message
  } finally {
    isLoading.value = false
    loadingProgress.value = ''
  }
}

const exportDocument = () => {
  if (!documentContent.value) return

  const formatConfig = {
    md: { type: 'text/markdown', ext: '.md' },
    txt: { type: 'text/plain', ext: '.txt' },
    ppt: { type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation', ext: '.pptx' }
  }

  const config = formatConfig[exportFormat.value] || formatConfig.md
  
  let content = documentContent.value
  let filename = `document_${docType.value}_${Date.now()}${config.ext}`

  if (exportFormat.value === 'txt') {
    content = content.replace(/[#*`>\-\[\]]/g, '').replace(/\n{2,}/g, '\n\n').trim()
  }

  const blob = new Blob([content], { type: config.type })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
@keyframes gradient {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

.animate-gradient {
  animation: gradient 3s ease infinite;
}
</style>
