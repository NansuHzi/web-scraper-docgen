<template>
  <div>
    <div class="max-w-3xl mx-auto px-6 md:px-10 pb-24">
      <!-- Hero -->
      <section class="pt-8 pb-12 animate-slide-down">
        <p class="text-xs text-muted tracking-[0.2em] mb-3 font-mono">TASK QUEUE</p>
        <h1 class="text-2xl md:text-3xl font-bold text-white tracking-tight leading-tight">
          任务队列
          <span class="text-muted font-normal">&</span>
          异步调度
        </h1>
        <p class="text-sm text-muted mt-2 max-w-lg">
          提交异步任务、查看执行状态、管理任务优先级，支持文档生成和批量爬取
        </p>
      </section>

      <!-- Stats Bar -->
      <section v-if="stats" class="grid grid-cols-4 gap-3 mb-8 animate-slide-up stagger-1">
        <div class="card-glass p-3 text-center">
          <p class="text-xl font-bold text-neon-green">{{ stats.pending || 0 }}</p>
          <p class="text-xs text-muted">等待中</p>
        </div>
        <div class="card-glass p-3 text-center">
          <p class="text-xl font-bold text-cyan-blue">{{ stats.running || 0 }}</p>
          <p class="text-xs text-muted">执行中</p>
        </div>
        <div class="card-glass p-3 text-center">
          <p class="text-xl font-bold text-white">{{ stats.completed || 0 }}</p>
          <p class="text-xs text-muted">已完成</p>
        </div>
        <div class="card-glass p-3 text-center">
          <p class="text-xl font-bold text-red-400">{{ stats.failed || 0 }}</p>
          <p class="text-xs text-muted">失败</p>
        </div>
      </section>

      <!-- Submit Task -->
      <section class="mb-8 animate-slide-up stagger-1">
        <div class="card-glass p-6 md:p-8">
          <div class="flex items-center justify-between mb-5">
            <h2 class="text-lg font-semibold text-white tracking-tight">提交任务</h2>
            <button @click="showSubmitForm = !showSubmitForm" class="btn-outline text-xs py-1.5 px-3">
              {{ showSubmitForm ? '收起' : '展开' }}
            </button>
          </div>

          <Transition name="collapse">
            <div v-if="showSubmitForm" class="space-y-4">
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="text-xs text-muted block mb-1.5">任务类型</label>
                  <select v-model="submitType" class="select-glass w-full">
                    <option value="generate_document">生成文档</option>
                    <option value="batch_crawl">批量爬取</option>
                    <option value="build_rag">构建知识库</option>
                    <option value="analyze_topics">热点分析</option>
                  </select>
                </div>
                <div>
                  <label class="text-xs text-muted block mb-1.5">优先级</label>
                  <select v-model="submitPriority" class="select-glass w-full">
                    <option value="low">低</option>
                    <option value="normal">普通</option>
                    <option value="high">高</option>
                    <option value="urgent">紧急</option>
                  </select>
                </div>
              </div>

              <div>
                <label class="text-xs text-muted block mb-1.5">目标 URL</label>
                <input v-model="submitUrl" type="url" placeholder="https://example.com" class="input-glass" />
              </div>

              <div v-if="submitType === 'generate_document'" class="grid grid-cols-2 gap-3">
                <div>
                  <label class="text-xs text-muted block mb-1.5">文档类型</label>
                  <select v-model="submitDocType" class="select-glass w-full">
                    <option value="tech_doc">技术文档</option>
                    <option value="api_doc">API 文档</option>
                    <option value="readme">README</option>
                    <option value="summary">摘要</option>
                  </select>
                </div>
                <div>
                  <label class="text-xs text-muted block mb-1.5">输出格式</label>
                  <select v-model="submitFormat" class="select-glass w-full">
                    <option value="md">Markdown</option>
                    <option value="html">HTML</option>
                  </select>
                </div>
              </div>

              <button @click="doSubmitTask" :disabled="submitLoading || !submitUrl"
                class="btn-gradient w-full py-3 text-sm"
              >
                <span v-if="submitLoading" class="flex items-center justify-center gap-2">
                  <span class="w-4 h-4 border-2 border-base/30 border-t-base rounded-full animate-spin" />
                  提交中...
                </span>
                <span v-else>提交任务</span>
              </button>
            </div>
          </Transition>
        </div>
      </section>

      <!-- Task List -->
      <section class="animate-slide-up stagger-2">
        <div class="card-glass p-6 md:p-8">
          <div class="flex items-center justify-between mb-5">
            <h2 class="text-lg font-semibold text-white tracking-tight">任务列表</h2>
            <div class="flex items-center gap-2">
              <select v-model="taskFilter" class="select-glass text-xs py-1.5 px-2" @change="loadTasks">
                <option value="">全部</option>
                <option value="pending">等待中</option>
                <option value="running">执行中</option>
                <option value="completed">已完成</option>
                <option value="failed">失败</option>
              </select>
              <button @click="loadTasks" :disabled="tasksLoading" class="btn-outline text-xs py-1.5 px-3">
                <svg class="w-3 h-3" :class="{ 'animate-spin': tasksLoading }" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
              </button>
            </div>
          </div>

          <!-- Loading -->
          <div v-if="tasksLoading && !tasks.length" class="text-center py-8">
            <div class="relative w-10 h-10 mx-auto mb-3">
              <div class="absolute inset-0 rounded-full border-2 border-neon-green/10" />
              <div class="absolute inset-1 rounded-full border-2 border-transparent border-t-neon-green animate-spin" />
            </div>
            <p class="text-sm text-muted">加载任务列表...</p>
          </div>

          <!-- Empty -->
          <div v-else-if="!tasks.length" class="text-center py-8">
            <div class="w-10 h-10 rounded-2xl bg-neon-green/[0.04] border border-neon-green/[0.08] flex items-center justify-center mx-auto mb-3">
              <svg class="w-5 h-5 text-neon-green/40" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
            </div>
            <p class="text-sm text-muted">暂无任务，提交一个任务开始吧</p>
          </div>

          <!-- Task Items -->
          <div v-else class="space-y-2">
            <div v-for="task in tasks" :key="task.id"
              class="p-4 rounded-lg bg-white/[0.02] border transition-all duration-300 cursor-pointer"
              :class="task.status === 'running' ? 'border-neon-green/[0.2]' : 'border-white/[0.04] hover:border-white/[0.1]'"
              @click="selectedTask = selectedTask?.id === task.id ? null : task"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3 min-w-0">
                  <span class="w-2 h-2 rounded-full shrink-0"
                    :class="statusColor(task.status)"
                  />
                  <span class="text-sm text-white truncate max-w-[280px]">{{ task.payload?.url || task.id }}</span>
                  <span class="tag text-[11px] shrink-0">{{ typeLabel(task.type) }}</span>
                  <span class="tag text-[11px] shrink-0" :class="priorityTag(task.priority)">{{ priorityLabel(task.priority) }}</span>
                </div>
                <div class="flex items-center gap-2 shrink-0 ml-3">
                  <span class="text-xs text-muted font-mono">{{ formatTime(task.created_at) }}</span>
                  <button v-if="task.status === 'pending' || task.status === 'running'"
                    @click.stop="doCancelTask(task.id)"
                    class="text-xs text-red-400 hover:text-red-300 transition-colors"
                  >取消</button>
                </div>
              </div>

              <!-- Expanded Detail -->
              <Transition name="collapse">
                <div v-if="selectedTask?.id === task.id" class="mt-4 pt-4 border-t border-white/[0.04] space-y-2">
                  <div class="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span class="text-muted">任务ID: </span>
                      <span class="text-white font-mono">{{ task.id }}</span>
                    </div>
                    <div>
                      <span class="text-muted">重试: </span>
                      <span class="text-white">{{ task.retry_count || 0 }}/{{ task.max_retries || 3 }}</span>
                    </div>
                    <div>
                      <span class="text-muted">开始时间: </span>
                      <span class="text-white">{{ formatTime(task.started_at) || '-' }}</span>
                    </div>
                    <div>
                      <span class="text-muted">完成时间: </span>
                      <span class="text-white">{{ formatTime(task.completed_at) || '-' }}</span>
                    </div>
                  </div>
                  <div v-if="task.error_message" class="p-2 rounded bg-red-500/[0.06] border border-red-500/[0.1]">
                    <p class="text-xs text-red-400">{{ task.error_message }}</p>
                  </div>
                  <div v-if="task.result" class="p-2 rounded bg-neon-green/[0.04] border border-neon-green/[0.08]">
                    <p class="text-xs text-muted">结果预览:</p>
                    <p class="text-xs text-white mt-1">{{ JSON.stringify(task.result).slice(0, 200) }}{{ JSON.stringify(task.result).length > 200 ? '...' : '' }}</p>
                  </div>
                </div>
              </Transition>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- Auto-refresh -->
    <div class="fixed bottom-6 right-6 z-40 flex gap-2">
      <button @click="loadTasks" :disabled="tasksLoading"
        class="btn-outline text-xs flex items-center gap-1.5 bg-base/80 backdrop-blur-md"
      >
        <svg class="w-3 h-3" :class="{ 'animate-spin': tasksLoading }" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
        <span>{{ tasksLoading ? '刷新中...' : '刷新' }}</span>
      </button>
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
import { ref, onMounted, onUnmounted } from 'vue'

const errorMessage = ref('')
const stats = ref(null)
const tasks = ref([])
const tasksLoading = ref(false)
const selectedTask = ref(null)
const taskFilter = ref('')
let autoRefreshTimer = null

// --- Submit ---
const showSubmitForm = ref(false)
const submitType = ref('generate_document')
const submitPriority = ref('normal')
const submitUrl = ref('')
const submitDocType = ref('tech_doc')
const submitFormat = ref('md')
const submitLoading = ref(false)

async function doSubmitTask() {
  submitLoading.value = true
  try {
    const payload = { url: submitUrl.value }
    if (submitType.value === 'generate_document') {
      payload.doc_type = submitDocType.value
      payload.format = submitFormat.value
      payload.use_qwen = true
    }

    const resp = await fetch('/api/tasks/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: submitType.value,
        priority: submitPriority.value,
        payload,
      }),
    })
    if (!resp.ok) {
      const err = await resp.json()
      throw new Error(err.detail || `HTTP ${resp.status}`)
    }
    const data = await resp.json()
    submitUrl.value = ''
    showSubmitForm.value = false
    await loadTasks()
  } catch (e) {
    errorMessage.value = e.message
  } finally {
    submitLoading.value = false
  }
}

// --- Load ---
async function loadTasks() {
  tasksLoading.value = true
  try {
    const params = new URLSearchParams()
    if (taskFilter.value) params.set('status', taskFilter.value)
    params.set('limit', '50')

    const resp = await fetch(`/api/tasks?${params}`)
    if (!resp.ok) {
      const err = await resp.json()
      throw new Error(err.detail || `HTTP ${resp.status}`)
    }
    const data = await resp.json()
    tasks.value = data.tasks || []
  } catch (e) {
    errorMessage.value = e.message
  } finally {
    tasksLoading.value = false
  }
}

async function loadStats() {
  try {
    const resp = await fetch('/api/tasks/stats')
    if (!resp.ok) return
    stats.value = await resp.json()
  } catch {}
}

async function doCancelTask(taskId) {
  try {
    const resp = await fetch(`/api/tasks/${taskId}/cancel`, { method: 'POST' })
    if (!resp.ok) {
      const err = await resp.json()
      throw new Error(err.detail || `HTTP ${resp.status}`)
    }
    await loadTasks()
  } catch (e) {
    errorMessage.value = e.message
  }
}

// --- helpers ---
function statusColor(status) {
  const m = { pending: 'bg-amber-warm animate-pulse', running: 'bg-neon-green animate-pulse', completed: 'bg-neon-green', failed: 'bg-red-400', cancelled: 'bg-muted' }
  return m[status] || 'bg-muted'
}

function typeLabel(type) {
  const m = { generate_document: '文档生成', batch_crawl: '批量爬取', build_rag: '知识库', analyze_topics: '热点分析' }
  return m[type] || type
}

function priorityLabel(p) {
  const m = { low: '低', normal: '普通', high: '高', urgent: '紧急' }
  return m[p] || p
}

function priorityTag(p) {
  const m = { urgent: 'tag-amber', high: 'tag-green', normal: '', low: '' }
  return m[p] || ''
}

function formatTime(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  loadTasks()
  loadStats()
  autoRefreshTimer = setInterval(() => { loadTasks(); loadStats() }, 10000)
})

onUnmounted(() => {
  if (autoRefreshTimer) clearInterval(autoRefreshTimer)
})
</script>

<style scoped>
.overlay-enter-active, .overlay-leave-active { transition: opacity 0.25s ease; }
.overlay-enter-from, .overlay-leave-to { opacity: 0; }
.collapse-enter-active, .collapse-leave-active { transition: all 0.25s ease; overflow: hidden; }
.collapse-enter-from, .collapse-leave-to { opacity: 0; max-height: 0; }
.collapse-enter-to, .collapse-leave-from { opacity: 1; max-height: 500px; }
</style>
