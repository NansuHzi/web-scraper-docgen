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
}

export default new ApiService()
