<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-900 via-slate-900 to-gray-900">
    <!-- 导航栏 -->
    <nav class="fixed top-0 left-0 right-0 z-50 glass">
      <div class="container mx-auto px-4 py-4 flex justify-between items-center">
        <div class="text-2xl font-bold bg-gradient-to-r from-neon-green to-neon-blue bg-clip-text text-transparent">
          TechVision
        </div>
        <div class="flex space-x-6">
          <a href="#features" class="text-gray-300 hover:text-neon-green transition-colors">功能</a>
          <a href="#about" class="text-gray-300 hover:text-neon-green transition-colors">关于</a>
          <a href="#contact" class="text-gray-300 hover:text-neon-green transition-colors">联系</a>
        </div>
      </div>
    </nav>

    <!-- 主内容 -->
    <main class="container mx-auto px-4 pt-24 pb-16">
      <!-- Hero 区域 -->
      <section class="min-h-[80vh] flex items-center justify-center">
        <div class="text-center max-w-3xl">
          <h1 class="text-5xl md:text-7xl font-bold mb-6">
            <span class="bg-gradient-to-r from-neon-green to-neon-blue bg-clip-text text-transparent">
              下一代
            </span>
            <br>
            <span class="text-white">智能分析平台</span>
          </h1>
          <p class="text-xl text-gray-400 mb-8">
            利用最先进的人工智能技术，为您的业务提供深度洞察和智能决策支持
          </p>
          <div class="flex flex-col sm:flex-row gap-4 justify-center">
            <button class="px-8 py-4 bg-gradient-to-r from-neon-green to-neon-blue text-gray-900 font-bold rounded-xl hover:from-green-300 hover:to-blue-300 transition-all duration-300 transform hover:scale-105 shadow-neon-green">
              立即开始
            </button>
            <button class="px-8 py-4 bg-transparent border-2 border-neon-green text-neon-green font-bold rounded-xl hover:bg-neon-green/10 transition-all duration-300">
              了解更多
            </button>
          </div>
        </div>
      </section>

      <!-- 功能区域 -->
      <section id="features" class="py-16">
        <h2 class="text-4xl font-bold text-center mb-12 text-white">核心功能</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div class="glass rounded-2xl p-8 hover:shadow-neon-green transition-all duration-300">
            <div class="text-4xl mb-4">🧠</div>
            <h3 class="text-2xl font-bold mb-4 text-neon-green">智能分析</h3>
            <p class="text-gray-400">利用深度学习算法，对复杂数据进行智能分析，提取关键信息</p>
          </div>
          <div class="glass rounded-2xl p-8 hover:shadow-neon-blue transition-all duration-300">
            <div class="text-4xl mb-4">📊</div>
            <h3 class="text-2xl font-bold mb-4 text-neon-blue">数据可视化</h3>
            <p class="text-gray-400">将复杂的数据转化为直观的图表和报告，帮助您快速理解</p>
          </div>
          <div class="glass rounded-2xl p-8 hover:shadow-neon-green transition-all duration-300">
            <div class="text-4xl mb-4">🔒</div>
            <h3 class="text-2xl font-bold mb-4 text-neon-green">安全保障</h3>
            <p class="text-gray-400">采用企业级加密技术，确保您的数据安全和隐私保护</p>
          </div>
        </div>
      </section>

      <!-- 关于区域 -->
      <section id="about" class="py-16">
        <div class="glass rounded-2xl p-12">
          <h2 class="text-4xl font-bold mb-8 text-white">关于我们</h2>
          <p class="text-gray-400 mb-6 text-lg">
            TechVision 是一家专注于人工智能和数据分析的科技公司。我们的使命是通过创新的技术解决方案，帮助企业实现数字化转型，提升运营效率。
          </p>
          <p class="text-gray-400 text-lg">
            我们的团队由来自世界顶尖科技公司的专家组成，拥有丰富的人工智能、大数据和云计算经验。我们致力于为客户提供最先进的技术解决方案和最优质的服务。
          </p>
        </div>
      </section>

      <!-- 联系区域 -->
      <section id="contact" class="py-16">
        <h2 class="text-4xl font-bold text-center mb-12 text-white">联系我们</h2>
        <div class="max-w-2xl mx-auto">
          <form @submit.prevent="submitForm" class="space-y-6">
            <div>
              <input
                v-model="formData.name"
                type="text"
                placeholder="您的姓名"
                class="w-full px-6 py-4 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-neon-green focus:ring-2 focus:ring-neon-green/20 transition-all"
              >
            </div>
            <div>
              <input
                v-model="formData.email"
                type="email"
                placeholder="您的邮箱"
                class="w-full px-6 py-4 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-neon-green focus:ring-2 focus:ring-neon-green/20 transition-all"
              >
            </div>
            <div>
              <textarea
                v-model="formData.message"
                rows="4"
                placeholder="您的消息"
                class="w-full px-6 py-4 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-neon-green focus:ring-2 focus:ring-neon-green/20 transition-all resize-none"
              ></textarea>
            </div>
            <button
              type="submit"
              class="w-full px-8 py-4 bg-gradient-to-r from-neon-green to-neon-blue text-gray-900 font-bold rounded-xl hover:from-green-300 hover:to-blue-300 transition-all duration-300 transform hover:scale-105 shadow-neon-green"
            >
              发送消息
            </button>
          </form>
        </div>
      </section>
    </main>

    <!-- 底部 -->
    <footer class="glass py-8">
      <div class="container mx-auto px-4 text-center text-gray-400">
        <p>&copy; 2024 TechVision. All rights reserved.</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'

// 表单数据
const formData = ref({
  name: '',
  email: '',
  message: ''
})

// 提交表单
const submitForm = () => {
  // 在实际应用中，这里会发送API请求
  alert('感谢您的留言！我们会尽快回复您。')

  // 重置表单
  formData.value = {
    name: '',
    email: '',
    message: ''
  }
}
</script>

<style>
/* 全局样式 */
body {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #1e293b;
}

::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}

/* 玻璃拟态效果 */
.glass {
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  background: rgba(30, 41, 59, 0.3);
}

/* 霓虹效果 */
.neon-glow {
  box-shadow: 0 0 15px rgba(52, 211, 153, 0.3), 0 0 30px rgba(52, 211, 153, 0.1);
}

.neon-glow-blue {
  box-shadow: 0 0 15px rgba(34, 211, 238, 0.3), 0 0 30px rgba(34, 211, 238, 0.1);
}
</style>
