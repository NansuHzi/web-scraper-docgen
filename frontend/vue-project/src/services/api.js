const API_BASE_URL = '/api'

class ApiService {
  async validateRequest(url, docType) {
    try {
      const response = await fetch(`${API_BASE_URL}/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url, doc_type: docType })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Validation error:', error)
      throw error
    }
  }

  async generateDocument(url, docType, format = 'md') {
    try {
      const response = await fetch(`${API_BASE_URL}/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url, doc_type: docType, format })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Generate error:', error)
      throw error
    }
  }

  async getDocument(documentId) {
    try {
      const response = await fetch(`${API_BASE_URL}/document/${documentId}`)

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Get document error:', error)
      throw error
    }
  }

  async pollDocumentStatus(documentId, maxAttempts = 120) {
    let attempts = 0
    let interval = 2000
    const maxInterval = 10000

    while (attempts < maxAttempts) {
      try {
        const result = await this.getDocument(documentId)

        if (result.status === 'completed' || result.content) {
          return result
        }

        if (result.status === 'failed') {
          throw new Error(result.error || 'Document generation failed')
        }

        attempts++
        await new Promise(resolve => setTimeout(resolve, interval))
        interval = Math.min(interval * 1.5, maxInterval)
      } catch (error) {
        if (error.message.includes('Document not found') || error.message.includes('404')) {
          attempts++
          await new Promise(resolve => setTimeout(resolve, interval))
          interval = Math.min(interval * 1.5, maxInterval)
          continue
        }
        throw error
      }
    }

    throw new Error('Document generation timeout')
  }

  async searchWeb(query, maxResults = 10) {
    try {
      const response = await fetch(`${API_BASE_URL}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query, max_results: maxResults })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Search error:', error)
      throw error
    }
  }

  async buildRag(urls, docType) {
    try {
      const response = await fetch(`${API_BASE_URL}/build-rag`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ urls, doc_type: docType })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Build RAG error:', error)
      throw error
    }
  }

  async getRagStatus(ragId) {
    try {
      const response = await fetch(`${API_BASE_URL}/rag/${ragId}`)

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Get RAG status error:', error)
      throw error
    }
  }

  async pollRagStatus(ragId, maxAttempts = 60) {
    let attempts = 0
    let interval = 3000
    const maxInterval = 15000

    while (attempts < maxAttempts) {
      try {
        const result = await this.getRagStatus(ragId)

        if (result.status === 'ready') {
          return result
        }

        if (result.status === 'failed') {
          throw new Error(result.error || '知识库构建失败')
        }

        attempts++
        await new Promise(resolve => setTimeout(resolve, interval))
        interval = Math.min(interval * 1.5, maxInterval)
      } catch (error) {
        if (error.message.includes('not found') || error.message.includes('404')) {
          attempts++
          await new Promise(resolve => setTimeout(resolve, interval))
          interval = Math.min(interval * 1.5, maxInterval)
          continue
        }
        throw error
      }
    }

    throw new Error('知识库构建超时')
  }

  async generateFromRag(ragId, docType, mode, format = 'md', topic = '') {
    try {
      const response = await fetch(`${API_BASE_URL}/generate-from-rag`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ rag_id: ragId, doc_type: docType, mode, format, topic })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Generate from RAG error:', error)
      throw error
    }
  }

  async getHistory(limit = 20) {
    try {
      const response = await fetch(`${API_BASE_URL}/history?limit=${limit}`)

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Get history error:', error)
      throw error
    }
  }

  async startLogin(site = 'zhihu') {
    try {
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ site })
      })
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }

  async getLoginStatus() {
    try {
      const response = await fetch(`${API_BASE_URL}/login/status`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Get login status error:', error)
      throw error
    }
  }

  async getLoginState() {
    try {
      const response = await fetch(`${API_BASE_URL}/login/state`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Get login state error:', error)
      throw error
    }
  }

  // Scheduler endpoints
  async getSchedulerJobs() {
    try {
      const response = await fetch(`${API_BASE_URL}/scheduler/jobs`)
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Get scheduler jobs error:', error)
      throw error
    }
  }

  async createSchedulerJob(data) {
    try {
      const response = await fetch(`${API_BASE_URL}/scheduler/jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Create scheduler job error:', error)
      throw error
    }
  }

  async updateSchedulerJob(jobId, data) {
    try {
      const response = await fetch(`${API_BASE_URL}/scheduler/jobs/${jobId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Update scheduler job error:', error)
      throw error
    }
  }

  async deleteSchedulerJob(jobId) {
    try {
      const response = await fetch(`${API_BASE_URL}/scheduler/jobs/${jobId}`, {
        method: 'DELETE'
      })
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Delete scheduler job error:', error)
      throw error
    }
  }

  async triggerSchedulerJob(jobId) {
    try {
      const response = await fetch(`${API_BASE_URL}/scheduler/jobs/${jobId}/trigger`, {
        method: 'POST'
      })
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Trigger scheduler job error:', error)
      throw error
    }
  }

  async getSchedulerJobHistory(jobId, limit = 20) {
    try {
      const response = await fetch(`${API_BASE_URL}/scheduler/jobs/${jobId}/history?limit=${limit}`)
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Get scheduler job history error:', error)
      throw error
    }
  }

  async getSchedulerStats() {
    try {
      const response = await fetch(`${API_BASE_URL}/scheduler/stats`)
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Get scheduler stats error:', error)
      throw error
    }
  }

  // Topic endpoints
  async getHotTopics(source = 'all') {
    try {
      const response = await fetch(`${API_BASE_URL}/topics/hot?source=${source}`)
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Get hot topics error:', error)
      throw error
    }
  }

  async getWeiboHotTopics() {
    try {
      const response = await fetch(`${API_BASE_URL}/topics/hot/weibo`)
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Get Weibo hot topics error:', error)
      throw error
    }
  }

  async getZhihuHotTopics() {
    try {
      const response = await fetch(`${API_BASE_URL}/topics/hot/zhihu`)
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Get Zhihu hot topics error:', error)
      throw error
    }
  }

  async analyzeTopics(topics) {
    try {
      const response = await fetch(`${API_BASE_URL}/topics/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topics })
      })
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Analyze topics error:', error)
      throw error
    }
  }
}

export default new ApiService()
