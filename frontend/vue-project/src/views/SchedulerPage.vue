<template>
  <div>
    <div class="max-w-3xl mx-auto px-6 md:px-10 pb-24">
      <!-- Hero -->
      <section class="pt-8 pb-12 animate-slide-down">
        <p class="text-xs text-muted tracking-[0.2em] mb-3 font-mono">SCHEDULER</p>
        <h1 class="text-2xl md:text-3xl font-bold text-white tracking-tight leading-tight">
          定时任务
          <span class="text-muted font-normal">&</span>
          自动化管理
        </h1>
        <p class="text-sm text-muted mt-2 max-w-lg">
          创建和管理定时抓取与文档生成任务，支持 Cron 表达式和固定间隔
        </p>
      </section>

      <!-- Stats Bar -->
      <section v-if="stats" class="mb-6 animate-slide-up stagger-1">
        <div class="card-glass p-4 flex gap-6 justify-center flex-wrap">
          <div class="text-center">
            <p class="text-lg font-bold text-white">{{ stats.total_jobs }}</p>
            <p class="text-xs text-muted">总任务</p>
          </div>
          <div class="text-center">
            <p class="text-lg font-bold text-neon-green">{{ stats.active_jobs }}</p>
            <p class="text-xs text-muted">活跃</p>
          </div>
          <div class="text-center">
            <p class="text-lg font-bold text-cyan-blue">{{ stats.total_executions }}</p>
            <p class="text-xs text-muted">总执行</p>
          </div>
          <div class="text-center">
            <p class="text-lg font-bold text-neon-green">{{ stats.success_executions }}</p>
            <p class="text-xs text-muted">成功</p>
          </div>
        </div>
      </section>

      <!-- Create/Edit Form -->
      <section class="animate-slide-up stagger-1">
        <div class="card-glass p-6 md:p-8 space-y-6">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-white">{{ editingJob ? '编辑任务' : '创建新任务' }}</h2>
            <button v-if="editingJob" @click="cancelEdit" class="text-xs text-muted hover:text-white transition-colors">取消</button>
          </div>

          <!-- Job Name -->
          <div>
            <label class="block text-xs font-medium text-muted mb-2 tracking-wide">任务名称</label>
            <input v-model="form.name" type="text" placeholder="例如：每日技术日报" class="input-glass" />
          </div>

          <!-- URL -->
          <div>
            <label class="block text-xs font-medium text-muted mb-2 tracking-wide">目标网址</label>
            <input v-model="form.url" type="text" placeholder="https://example.com" class="input-glass" />
          </div>

          <!-- Doc Type -->
          <div>
            <label class="block text-xs font-medium text-muted mb-3 tracking-wide">文档类型</label>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
              <label
                v-for="doc in docTypes"
                :key="doc.value"
                class="relative flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer transition-all duration-300 border"
                :class="form.doc_type === doc.value
                  ? 'border-neon-green/[0.25] bg-neon-green/[0.04]'
                  : 'border-white/[0.05] bg-white/[0.02] hover:border-white/[0.1]'"
              >
                <input type="radio" :value="doc.value" v-model="form.doc_type" class="sr-only" />
                <span class="text-base">{{ doc.icon }}</span>
                <span class="text-sm font-medium" :class="form.doc_type === doc.value ? 'text-neon-green' : 'text-muted'">{{ doc.label }}</span>
              </label>
            </div>
          </div>

          <!-- Export Format -->
          <div>
            <label class="block text-xs font-medium text-muted mb-3 tracking-wide">导出格式</label>
            <div class="flex gap-2">
              <label v-for="fmt in exportFormats" :key="fmt.value"
                class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-lg cursor-pointer transition-all duration-300 border text-sm font-medium"
                :class="form.format === fmt.value
                  ? 'border-cyan-blue/[0.3] bg-cyan-blue/[0.05] text-cyan-blue'
                  : 'border-white/[0.05] bg-white/[0.02] text-muted hover:border-white/[0.1]'"
              >
                <input type="radio" :value="fmt.value" v-model="form.format" class="sr-only" />
                {{ fmt.label }}
              </label>
            </div>
          </div>

          <!-- Schedule Type -->
          <div>
            <label class="block text-xs font-medium text-muted mb-3 tracking-wide">调度方式</label>
            <div class="flex gap-2 mb-4">
              <button @click="form.schedule_type = 'interval'"
                class="flex-1 py-2.5 rounded-lg text-sm font-medium transition-all border"
                :class="form.schedule_type === 'interval'
                  ? 'border-neon-green/[0.25] bg-neon-green/[0.04] text-neon-green'
                  : 'border-white/[0.05] bg-white/[0.02] text-muted hover:border-white/[0.1]'"
              >固定间隔</button>
              <button @click="form.schedule_type = 'cron'"
                class="flex-1 py-2.5 rounded-lg text-sm font-medium transition-all border"
                :class="form.schedule_type === 'cron'
                  ? 'border-neon-green/[0.25] bg-neon-green/[0.04] text-neon-green'
                  : 'border-white/[0.05] bg-white/[0.02] text-muted hover:border-white/[0.1]'"
              >Cron 表达式</button>
            </div>

            <!-- Interval presets -->
            <div v-if="form.schedule_type === 'interval'" class="space-y-3">
              <div class="flex flex-wrap gap-2">
                <button v-for="p in intervalPresets" :key="p.value" @click="form.interval_seconds = p.value"
                  class="px-3 py-1.5 rounded-md text-xs transition-all border"
                  :class="form.interval_seconds === p.value
                    ? 'border-cyan-blue/[0.25] bg-cyan-blue/[0.05] text-cyan-blue'
                    : 'border-white/[0.05] bg-white/[0.02] text-muted hover:border-white/[0.1]'"
                >{{ p.label }}</button>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-xs text-muted">自定义（秒）：</span>
                <input v-model.number="form.interval_seconds" type="number" min="60" placeholder="3600"
                  class="input-glass w-32 text-sm" />
              </div>
            </div>

            <!-- Cron input -->
            <div v-if="form.schedule_type === 'cron'" class="space-y-2">
              <input v-model="form.cron_expression" type="text" placeholder="0 9 * * * (每天9点)"
                class="input-glass font-mono text-sm" />
              <p class="text-xs text-muted">格式：分 时 日 月 周 (例: */30 * * * * 每30分钟, 0 9 * * 1-5 工作日9点)</p>
            </div>
          </div>

          <!-- Enabled toggle -->
          <div class="flex items-center gap-3">
            <button @click="form.enabled = !form.enabled"
              class="relative w-10 h-5.5 rounded-full transition-colors duration-300"
              :class="form.enabled ? 'bg-neon-green/30' : 'bg-white/[0.06]'"
            >
              <span class="absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform duration-300 shadow-sm"
                :class="form.enabled ? 'translate-x-[18px]' : 'translate-x-0'" />
            </button>
            <span class="text-sm" :class="form.enabled ? 'text-neon-green' : 'text-muted'">
              {{ form.enabled ? '已启用' : '已禁用' }}
            </span>
          </div>

          <!-- Submit -->
          <button @click="submitJob" :disabled="submitting"
            class="btn-gradient w-full py-3.5 text-base flex items-center justify-center gap-2.5"
          >
            <svg v-if="submitting" class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3.5" />
              <path class="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span>{{ editingJob ? '更新任务' : '创建任务' }}</span>
          </button>
        </div>
      </section>

      <!-- Job List -->
      <section class="pt-10 animate-slide-up stagger-2">
        <div class="card-glass p-6 md:p-8">
          <div class="flex items-center justify-between mb-5">
            <h2 class="text-lg font-semibold text-white tracking-tight">任务列表</h2>
            <button @click="loadJobs" class="btn-outline text-xs" :disabled="loadingJobs">
              <svg class="w-3 h-3" :class="{ 'animate-spin': loadingJobs }" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
              <span>刷新</span>
            </button>
          </div>

          <!-- Empty state -->
          <div v-if="jobs.length === 0" class="py-16 text-center">
            <div class="w-12 h-12 rounded-2xl bg-neon-green/[0.04] border border-neon-green/[0.08] flex items-center justify-center mx-auto mb-4">
              <svg class="w-5 h-5 text-neon-green/40" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            </div>
            <p class="text-sm text-muted">暂无定时任务，填写表单创建第一个任务</p>
          </div>

          <!-- Job cards -->
          <div v-else class="grid gap-3">
            <div v-for="(job, i) in jobs" :key="job.id"
              class="group bg-white/[0.02] border rounded-xl p-4 transition-all"
              :class="job.enabled ? 'border-white/[0.04] hover:bg-white/[0.04] hover:border-white/[0.08]' : 'border-white/[0.02] opacity-50'"
              :style="{ animationDelay: `${0.2 + i * 0.03}s` }"
            >
              <div class="flex items-start justify-between gap-4">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-1.5">
                    <span class="text-sm font-semibold text-white truncate">{{ job.name }}</span>
                    <span v-if="job.enabled" class="tag tag-green">运行中</span>
                    <span v-else class="tag">已暂停</span>
                  </div>
                  <p class="text-xs text-muted truncate mb-2">{{ job.url }}</p>
                  <div class="flex items-center gap-3 text-xs text-muted">
                    <span class="font-mono">{{ job.schedule_type === 'cron' ? job.cron_expression : `${job.interval_seconds}s` }}</span>
                    <span>{{ docLabel(job.doc_type) }}</span>
                    <span>{{ job.format }}</span>
                    <span v-if="job.next_run" class="text-neon-green/60">下次: {{ formatDate(job.next_run) }}</span>
                  </div>
                </div>
                <div class="flex items-center gap-1.5 shrink-0">
                  <button @click="triggerJob(job.id)" class="px-2.5 py-1.5 rounded-md text-xs text-cyan-blue hover:bg-cyan-blue/[0.06] transition-all" title="立即执行">
                    <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                  </button>
                  <button @click="viewHistory(job)" class="px-2.5 py-1.5 rounded-md text-xs text-muted hover:text-white hover:bg-white/[0.04] transition-all" title="历史记录">
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                  </button>
                  <button @click="editJob(job)" class="px-2.5 py-1.5 rounded-md text-xs text-muted hover:text-white hover:bg-white/[0.04] transition-all" title="编辑">
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                  </button>
                  <button @click="deleteJob(job.id)" class="px-2.5 py-1.5 rounded-md text-xs text-muted hover:text-red-400 hover:bg-red-500/[0.06] transition-all" title="删除">
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                  </button>
                </div>
              </div>
              <!-- Stats row -->
              <div class="flex gap-4 mt-3 pt-3 border-t border-white/[0.03]">
                <span class="text-xs text-muted">总执行: <span class="text-white">{{ job.total_runs }}</span></span>
                <span class="text-xs text-muted">成功: <span class="text-neon-green">{{ job.success_runs }}</span></span>
                <span class="text-xs text-muted">失败: <span class="text-red-400">{{ job.failed_runs }}</span></span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- History Modal -->
    <Transition name="overlay">
      <div v-if="historyJob" class="fixed inset-0 z-50 flex items-center justify-center" style="background: rgba(6,6,8,0.7); backdrop-filter: blur(4px);" @click="historyJob = null">
        <div class="card-glass p-6 max-w-lg w-full mx-4 max-h-[70vh] overflow-y-auto animate-scale-in" @click.stop>
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-white">执行历史 - {{ historyJob.name }}</h3>
            <button @click="historyJob = null" class="text-muted hover:text-white transition-colors">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
          </div>
          <div v-if="historyRecords.length === 0" class="py-8 text-center">
            <p class="text-sm text-muted">暂无执行记录</p>
          </div>
          <div v-else class="space-y-2">
            <div v-for="rec in historyRecords" :key="rec.id"
              class="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]"
            >
              <div class="flex items-center gap-3">
                <span class="w-2 h-2 rounded-full"
                  :class="rec.status === 'success' ? 'bg-neon-green' : rec.status === 'failed' ? 'bg-red-400' : 'bg-amber-warm animate-pulse'"
                />
                <div>
                  <p class="text-xs text-white font-mono">{{ rec.started_at ? formatDate(rec.started_at) : '-' }}</p>
                  <p v-if="rec.error_message" class="text-xs text-red-400 mt-0.5">{{ rec.error_message }}</p>
                </div>
              </div>
              <div class="flex items-center gap-3 text-xs text-muted">
                <span v-if="rec.duration_ms">{{ (rec.duration_ms / 1000).toFixed(1) }}s</span>
                <span class="tag" :class="rec.status === 'success' ? 'tag-green' : rec.status === 'failed' ? 'bg-red-500/10 text-red-400 border-red-500/20' : ''">
                  {{ rec.status === 'success' ? '成功' : rec.status === 'failed' ? '失败' : '运行中' }}
                </span>
              </div>
            </div>
          </div>
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
import { ref, reactive, onMounted, watch } from 'vue'
import apiService from '../services/api'

// 状态持久化键名
const STORAGE_KEY = 'docgen_scheduler_state'

// 从sessionStorage恢复状态
const loadFormState = () => {
  try {
    const saved = sessionStorage.getItem(STORAGE_KEY)
    if (saved) {
      const data = JSON.parse(saved)
      return {
        name: data.name || '',
        url: data.url || '',
        doc_type: data.doc_type || 'tech_doc',
        format: data.format || 'md',
        schedule_type: data.schedule_type || 'interval',
        cron_expression: data.cron_expression || '',
        interval_seconds: data.interval_seconds || 3600,
        enabled: data.enabled !== undefined ? data.enabled : true,
      }
    }
  } catch (e) {
    console.warn('Failed to load form state from sessionStorage:', e)
  }
  return { name: '', url: '', doc_type: 'tech_doc', format: 'md', schedule_type: 'interval', cron_expression: '', interval_seconds: 3600, enabled: true }
}

const savedForm = loadFormState()

const jobs = ref([])
const stats = ref(null)
const errorMessage = ref('')
const submitting = ref(false)
const loadingJobs = ref(false)
const editingJob = ref(null)
const historyJob = ref(null)
const historyRecords = ref([])

const form = reactive({
  name: savedForm.name,
  url: savedForm.url,
  doc_type: savedForm.doc_type,
  format: savedForm.format,
  schedule_type: savedForm.schedule_type,
  cron_expression: savedForm.cron_expression,
  interval_seconds: savedForm.interval_seconds,
  enabled: savedForm.enabled,
})

// 保存表单状态到sessionStorage
const saveFormState = () => {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
      name: form.name,
      url: form.url,
      doc_type: form.doc_type,
      format: form.format,
      schedule_type: form.schedule_type,
      cron_expression: form.cron_expression,
      interval_seconds: form.interval_seconds,
      enabled: form.enabled,
    }))
  } catch (e) {
    console.warn('Failed to save form state to sessionStorage:', e)
  }
}

// 监听表单变化并保存
const formKeys = ['name', 'url', 'doc_type', 'format', 'schedule_type', 'cron_expression', 'interval_seconds', 'enabled']
let saveTimeout = null
const debouncedSave = () => {
  if (saveTimeout) clearTimeout(saveTimeout)
  saveTimeout = setTimeout(saveFormState, 300)
}

formKeys.forEach(key => {
  Object.defineProperty(form, key, {
    get() { return form['_' + key] },
    set(value) {
      form['_' + key] = value
      debouncedSave()
    }
  })
})

// 初始化私有属性
formKeys.forEach(key => {
  form['_' + key] = savedForm[key]
})

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

const intervalPresets = [
  { value: 300, label: '5分钟' },
  { value: 900, label: '15分钟' },
  { value: 1800, label: '30分钟' },
  { value: 3600, label: '1小时' },
  { value: 21600, label: '6小时' },
  { value: 86400, label: '24小时' },
]

const docLabel = (type) => {
  const m = { tech_doc: '技术文档', api_doc: 'API 文档', readme: 'README', summary: '摘要总结' }
  return m[type] || type
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const resetForm = () => {
  form.name = ''
  form.url = ''
  form.doc_type = 'tech_doc'
  form.format = 'md'
  form.schedule_type = 'interval'
  form.cron_expression = ''
  form.interval_seconds = 3600
  form.enabled = true
  editingJob.value = null
}

const loadJobs = async () => {
  loadingJobs.value = true
  try {
    const [jobsRes, statsRes] = await Promise.all([
      apiService.getSchedulerJobs(),
      apiService.getSchedulerStats()
    ])
    jobs.value = jobsRes.jobs || []
    stats.value = statsRes
  } catch (e) {
    errorMessage.value = '加载任务列表失败: ' + e.message
  } finally {
    loadingJobs.value = false
  }
}

const submitJob = async () => {
  if (!form.name.trim() || !form.url.trim()) {
    errorMessage.value = '请填写任务名称和URL'
    return
  }
  if (form.schedule_type === 'cron' && !form.cron_expression.trim()) {
    errorMessage.value = '请填写Cron表达式'
    return
  }
  if (form.schedule_type === 'interval' && (!form.interval_seconds || form.interval_seconds < 60)) {
    errorMessage.value = '间隔时间不能少于60秒'
    return
  }

  submitting.value = true
  try {
    const data = {
      name: form.name,
      url: form.url,
      doc_type: form.doc_type,
      format: form.format,
      schedule_type: form.schedule_type,
      cron_expression: form.schedule_type === 'cron' ? form.cron_expression : null,
      interval_seconds: form.schedule_type === 'interval' ? form.interval_seconds : null,
      enabled: form.enabled,
    }

    if (editingJob.value) {
      await apiService.updateSchedulerJob(editingJob.value.id, data)
    } else {
      await apiService.createSchedulerJob(data)
    }
    resetForm()
    await loadJobs()
  } catch (e) {
    errorMessage.value = e.message
  } finally {
    submitting.value = false
  }
}

const editJob = (job) => {
  editingJob.value = job
  form.name = job.name
  form.url = job.url
  form.doc_type = job.doc_type
  form.format = job.format
  form.schedule_type = job.schedule_type
  form.cron_expression = job.cron_expression || ''
  form.interval_seconds = job.interval_seconds || 3600
  form.enabled = job.enabled
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const cancelEdit = () => {
  resetForm()
}

const deleteJob = async (jobId) => {
  if (!confirm('确定要删除这个定时任务吗？')) return
  try {
    await apiService.deleteSchedulerJob(jobId)
    await loadJobs()
  } catch (e) {
    errorMessage.value = e.message
  }
}

const triggerJob = async (jobId) => {
  try {
    await apiService.triggerSchedulerJob(jobId)
    await loadJobs()
  } catch (e) {
    errorMessage.value = e.message
  }
}

const viewHistory = async (job) => {
  historyJob.value = job
  try {
    const res = await apiService.getSchedulerJobHistory(job.id)
    historyRecords.value = (res.history || []).reverse()
  } catch (e) {
    errorMessage.value = e.message
  }
}

onMounted(() => {
  loadJobs()
})
</script>

<style scoped>
.overlay-enter-active, .overlay-leave-active { transition: opacity 0.25s ease; }
.overlay-enter-from, .overlay-leave-to { opacity: 0; }
</style>
