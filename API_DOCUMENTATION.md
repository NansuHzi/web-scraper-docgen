# Web Scraper Document Generator API Documentation

## Overview
This API provides intelligent webpage scraping and Markdown document generation capabilities using CrewAI agents and multiple LLM models.

**Base URL:** `http://localhost:8000`
**API Version:** `1.0.0`

---

## Authentication
Currently, the API does not require authentication. All endpoints are publicly accessible.

---

## Endpoints

### 1. Root Endpoint
Get API information and available endpoints.

**Endpoint:** `GET /`

**Response:**
```json
{
  "message": "欢迎使用网页信息抓取与文档生成系统",
  "endpoints": [
    {
      "path": "/api/scrape",
      "method": "POST",
      "description": "提交网页URL生成文档"
    }
  ]
}
```

---

### 2. Validate URL and Document Type
Validate the provided URL and document type before processing.

**Endpoint:** `POST /api/validate`

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "url": "https://example.com",
  "doc_type": "tech_doc"
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| url | string | Yes | The target webpage URL to scrape |
| doc_type | string | Yes | Type of document to generate |

**Document Types:**
- `tech_doc` - Technical documentation
- `api_doc` - API documentation
- `readme` - README file
- `summary` - Summary document

**Success Response (200 OK):**
```json
{
  "valid": true,
  "message": "URL and document type are valid"
}
```

**Error Response (400 Bad Request):**
```json
{
  "valid": false,
  "message": "Invalid URL format"
}
```

**Error Response (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "loc": ["body", "url"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

### 3. Generate Document
Initiate the document generation process for a given URL and document type.

**Endpoint:** `POST /api/generate`

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "url": "https://example.com",
  "doc_type": "tech_doc"
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| url | string | Yes | The target webpage URL to scrape |
| doc_type | string | Yes | Type of document to generate |

**Success Response (200 OK):**
```json
{
  "success": true,
  "document_id": "doc_1234567890",
  "message": "Document generation started successfully",
  "estimated_time": 30
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "message": "Invalid URL or document type"
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "success": false,
  "message": "Document generation failed: [error details]"
}
```

---

### 4. Get Generated Document
Retrieve the generated Markdown document by document ID.

**Endpoint:** `GET /api/document/{document_id}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| document_id | string | Yes | Unique identifier of the document |

**Success Response (200 OK):**
```json
{
  "document_id": "doc_1234567890",
  "content": "# Document Title\n\nDocument content in Markdown format...",
  "url": "https://example.com",
  "doc_type": "tech_doc",
  "created_at": "2024-01-15T10:30:00Z",
  "filename": "example_com_20240115_103000.md"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Document not found"
}
```

---

### 5. Scrape Webpage (Legacy)
Legacy endpoint that performs scraping and document generation in a single request.

**Endpoint:** `POST /api/scrape`

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "url": "https://example.com",
  "document_type": "技术报告"
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| url | string | Yes | The target webpage URL to scrape |
| document_type | string | No | Type of document to generate (default: "技术报告") |

**Success Response (200 OK):**
```json
{
  "status": "success",
  "document": "# Document Title\n\nDocument content...",
  "url": "https://example.com",
  "document_type": "技术报告",
  "saved_file": "/path/to/output/file.md",
  "filename": "example_com_20240115_103000.md"
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "detail": "处理失败: [error details]"
}
```

---

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error - Server error |

---

## Common Error Messages

| Error Message | Cause | Solution |
|---------------|-------|----------|
| "Invalid URL format" | URL is malformed | Check URL format and protocol |
| "URL and document type are invalid" | Validation failed | Verify URL accessibility and document type |
| "网页抓取失败" | Webpage scraping failed | Check if URL is accessible and not blocked |
| "生成的文档为空" | Document generation failed | Check LLM API keys and configuration |
| "Document not found" | Document ID doesn't exist | Verify document ID is correct |

---

## Rate Limiting
Currently, there is no rate limiting implemented.

---

## CORS
The API supports CORS for cross-origin requests from the frontend.

---

## Example Usage

### Example 1: Complete Workflow

```bash
# 1. Validate URL and document type
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "doc_type": "tech_doc"}'

# 2. Generate document
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "doc_type": "tech_doc"}'

# Response: {"success": true, "document_id": "doc_1234567890", ...}

# 3. Retrieve document
curl http://localhost:8000/api/document/doc_1234567890
```

### Example 2: Legacy Single Request

```bash
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "document_type": "技术报告"}'
```

---

## Notes

1. **Processing Time:** Document generation may take 10-60 seconds depending on webpage complexity and LLM response time.
2. **Document Storage:** Generated documents are saved to the `output/` directory.
3. **LLM Models:** The system uses multiple LLM models (DeepSeek, Qwen, GLM) for different agents.
4. **JavaScript Rendering:** The scraper uses Playwright to handle JavaScript-rendered content.
5. **Content Limits:** Scraped content is limited to 5000 characters to optimize token usage.

---

## Environment Variables

Required environment variables for the backend:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
QWEN_API_KEY=your_qwen_api_key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
ANTHROPIC_AUTH_API=your_glm_api_key
ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/paas/v4
```

---

## Support

For issues or questions, please contact the development team.
