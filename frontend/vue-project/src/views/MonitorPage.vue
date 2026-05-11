<template>
  <div>
    <div class="max-w-3xl mx-auto px-6 md:px-10 pb-24">
      <!-- Hero -->
      <section class="pt-8 pb-12 animate-slide-down">
        <p class="text-xs text-muted tracking-[0.2em] mb-3 font-mono">MONITOR</p>
        <h1 class="text-2xl md:text-3xl font-bold text-white tracking-tight leading-tight">
          系统监控
          <span class="text-muted font-normal">&</span>
          运行统计
        </h1>
        <p class="text-sm text-muted mt-2 max-w-lg">
          实时查看系统运行状态、文档生成统计和定时任务执行情况
        </p>
      </section>

      <!-- Loading -->
      <section v-if="isLoading" class="animate-slide-up stagger-1">
        <div class="card-glass p-12 text-center">
          <div class="relative w-14 h-14 mx-auto mb-5">
            <div class="absolute inset-0 rounded-full border-2 border-neon-green/10" />
            <div class="absolute inset-1 rounded-full border-2 border-transparent border-t-neon-green animate-spin" />
          </div>
          <p class="text-sm text-white font-medium">加载监控数据...</p>
        </div>
      </section>

      <template v-if="!isLoading && data">
        <!-- System Info Bar -->
        <section class="mb-6 animate-slide-up stagger-1">
          <div class="card-glass p-4 flex items-center gap-3">
            <span class="w-2 h-2 rounded-full bg-neon-green animate-pulse" />
            <span class="text-sm text-white">运行中</span>
            <span class="text-xs text-muted ml-auto">
              已运行 {{ data.system?.uptime_display || '-' }} | 启动于 {{ formatTime(data.system?.started_at) }}
            </span>
          </div>
        </section>

        <!-- Stat Cards Row -->
        <section class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8 animate-slide-up stagger-1">
          <div class="card-glass p-4 text-center">
            <p class="text-2xl font-bold text-neon-green">{{ data.documents?.total || 0 }}</p>
            <p class="text-xs text-muted mt-1">文档总数</p>
            <p class="text-[11px] text-muted/60 mt-0.5">{{ data.documents?.completed || 0 }} 完成 / {{ data.documents?.failed || 0 }} 失败</p>
          </div>
          <div class="card-glass p-4 text-center">
            <p class="text-2xl font-bold text-cyan-blue">{{ data.scheduler?.active_jobs || 0 }}</p>
            <p class="text-xs text-muted mt-1">活跃任务</p>
            <p class="text-[11px] text-muted/60 mt-0.5">共 {{ data.scheduler?.total_jobs || 0 }} 个任务</p>
          </div>
          <div class="card-glass p-4 text-center">
            <p class="text-2xl font-bold" style="color: #f59e0b;">{{ data.cache?.total_entries || 0 }}</p>
            <p class="text-xs text-muted mt-1">缓存条目</p>
            <p class="text-[11px] text-muted/60 mt-0.5">最大 {{ data.cache?.max_entries || 0 }}</p>
          </div>
          <div class="card-glass p-4 text-center">
            <p class="text-2xl font-bold text-white">{{ data.sessions?.active_24h || 0 }}</p>
            <p class="text-xs text-muted mt-1">活跃会话</p>
            <p class="text-[11px] text-muted/60 mt-0.5">{{ data.sessions?.unique_ips || 0 }} 独立 IP</p>
          </div>
        </section>

        <!-- Second Stats Row -->
        <section class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8 animate-slide-up stagger-2">
          <div class="card-glass p-4 text-center">
            <p class="text-xl font-bold text-neon-green">{{ data.scheduler?.total_executions || 0 }}</p>
            <p class="text-xs text-muted mt-1">总执行次数</p>
          </div>
          <div class="card-glass p-4 text-center">
            <p class="text-xl font-bold text-neon-green">{{ data.scheduler?.success_executions || 0 }}</p>
            <p class="text-xs text-muted mt-1">执行成功</p>
          </div>
          <div class="card-glass p-4 text-center">
            <p class="text-xl font-bold text-red-400">{{ data.scheduler?.failed_executions || 0 }}</p>
            <p class="text-xs text-muted mt-1">执行失败</p>
          </div>
          <div class="card-glass p-4 text-center">
            <p class="text-xl font-bold text-white">{{ data.rag?.total_stores || 0 }}</p>
            <p class="text-xs text-muted mt-1">知识库</p>
          </div>
        </section>

        <!-- Doc Type Distribution -->
        <section v-if="data.documents?.doc_types" class="mb-8 animate-slide-up stagger-2">
          <div class="card-glass p-6 md:p-8">
            <h2 class="text-lg font-semibold text-white tracking-tight mb-5">文档类型分布</h2>
            <div class="space-y-3">
              <div v-for="(count, type) in data.documents.doc_types" :key="type" class="flex items-center gap-3">
                <span class="text-xs text-muted w-20 shrink-0">{{ docLabel(type) }}</span>
                <div class="flex-1 h-2 rounded-full bg-white/[0.04] overflow-hidden">
                  <div class="h-full rounded-full bg-gradient-to-r from-neon-green to-cyan-blue transition-all duration-700"
                    :style="{ width: percentOf(count, data.documents.total) + '%' }" />
                </div>
                <span class="text-xs text-white font-mono w-8 text-right">{{ count }}</span>
              </div>
            </div>
          </div>
        </section>

        <!-- Recent Documents -->
        <section v-if="data.recent?.recent_documents?.length" class="mb-8 animate-slide-up stagger-3">
          <div class="card-glass p-6 md:p-8">
            <h2 class="text-lg font-semibold text-white tracking-tight mb-5">最近文档</h2>
            <div class="space-y-2">
              <div v-for="doc in data.recent.recent_documents" :key="doc.document_id"
                class="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]"
              >
                <div class="flex items-center gap-3 min-w-0">
                  <span class="w-2 h-2 rounded-full shrink-0"
                    :class="doc.status === 'completed' ? 'bg-neon-green' : doc.status === 'failed' ? 'bg-red-400' : 'bg-amber-warm animate-pulse'"
                  />
                  <span class="text-sm text-white truncate max-w-[300px]">{{ doc.url }}</span>
                  <span class="tag text-[11px] shrink-0">{{ docLabel(doc.doc_type) }}</span>
                </div>
                <span class="text-xs text-muted shrink-0 ml-3 font-mono">{{ formatTime(doc.created_at) }}</span>
              </div>
            </div>
          </div>
        </section>

        <!-- Recent Executions -->
        <section v-if="data.recent?.recent_executions?.length" class="mb-8 animate-slide-up stagger-3">
          <div class="card-glass p-6 md:p-8">
            <h2 class="text-lg font-semibold text-white tracking-tight mb-5">最近执行</h2>
            <div class="space-y-2">
              <div v-for="exe in data.recent.recent_executions" :key="exe.started_at"
                class="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]"
              >
                <div class="flex items-center gap-3 min-w-0">
                  <span class="w-2 h-2 rounded-full shrink-0"
                    :class="exe.status === 'success' ? 'bg-neon-green' : exe.status === 'failed' ? 'bg-red-400' : 'bg-amber-warm'"
                  />
                  <span class="text-sm text-white truncate max-w-[200px]">{{ exe.job_name }}</span>
                  <span v-if="exe.error_message" class="text-xs text-red-400 truncate max-w-[200px]">{{ exe.error_message }}</span>
                </div>
                <div class="flex items-center gap-3 shrink-0">
                  <span v-if="exe.duration_ms" class="text-xs text-muted font-mono">{{ (exe.duration_ms / 1000).toFixed(1) }}s</span>
                  <span class="text-xs text-muted font-mono">{{ formatTime(exe.started_at) }}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Empty State -->
        <section v-if="isEmpty" class="animate-slide-up stagger-1">
          <div class="card-glass p-12 text-center">
            <div class="w-12 h-12 rounded-2xl bg-neon-green/[0.04] border border-neon-green/[0.08] flex items-center justify-center mx-auto mb-4">
              <svg class="w-5 h-5 text-neon-green/40" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
            </div>
            <p class="text-sm text-muted">暂无运行数据，系统启动后会在此显示统计</p>
          </div>
        </section>
      </template>
    </div>

    <!-- Auto-refresh -->
    <div class="fixed bottom-6 right-6 z-40">
      <button @click="refresh" :disabled="isLoading"
        class="btn-outline text-xs flex items-center gap-1.5 bg-base/80 backdrop-blur-md"
      >
        <svg class="w-3 h-3" :class="{ 'animate-spin': isLoading }" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
        <span>{{ isLoading ? '刷新中...' : '刷新' }}</span>
      </button>
    </div>

    <!-- Error Modal -->
    <Transition name="overlay">
      <div v-if="errorMessage" class="fixed inset-0 z-50 flex items-center justify-center" style="background: rgba(6,6,8,0.7); backdrop-filter: blur(4px);" @click="errorMessage = ''">
        <div class="card-glass p-6 max-w-sm mx-4 text-center animate-scale-in" @click.stop>
          <div class="w-10 h-10 rounded-full bg-red-500/[0.08] border border-red-500/[0.15] flex items-center justify-center mx-auto mb-4">
            <svg class="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          </div>
          <p class="text-white font-semibold mb-1">加载失败</p>
          <p class="text-sm text-muted mb-5">{{ errorMessage }}</p>
          <button @click="errorMessage = ''" class="btn-gradient w-full py-2.5 text-sm">确定</button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const data = ref(null)
const isLoading = ref(false)
const errorMessage = ref('')
let autoRefreshTimer = null

const isEmpty = computed(() => {
  if (!data.value) return false
  const d = data.value
  return (d.documents?.total || 0) === 0
    && (d.scheduler?.total_jobs || 0) === 0
    && (d.cache?.total_entries || 0) === 0
    && (d.rag?.total_stores || 0) === 0
})

const docLabel = (type) => {
  const m = { tech_doc: '技术文档', api_doc: 'API', readme: 'README', summary: '摘要' }
  return m[type] || type
}

const formatTime = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const percentOf = (count, total) => {
  if (!total) return 0
  return Math.round((count / total) * 100)
}

const refresh = async () => {
  isLoading.value = true
  try {
    const resp = await fetch('/api/monitor/dashboard')
    if (!resp.ok) {
      const err = await resp.json()
      throw new Error(err.detail || `HTTP ${resp.status}`)
    }
    data.value = await resp.json()
  } catch (e) {
    errorMessage.value = e.message
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  refresh()
  autoRefreshTimer = setInterval(refresh, 30000)
})

import { onUnmounted } from 'vue'
onUnmounted(() => {
  if (autoRefreshTimer) clearInterval(autoRefreshTimer)
})
</script>

<style scoped>
.overlay-enter-active, .overlay-leave-active { transition: opacity 0.25s ease; }
.overlay-enter-from, .overlay-leave-to { opacity: 0; }
</style>
