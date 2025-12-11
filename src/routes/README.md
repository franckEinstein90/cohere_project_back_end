# Routes API Documentation

## Overview
This documentation covers all API endpoints in the application, organized by blueprint. The API provides functionality for querying tools with conversational context and managing document libraries.

---

# Query Blueprint

## Overview
The Query Blueprint provides endpoints for submitting queries to various tools with optional conversation history. It supports tool-specific processing and conversation context management.

**Base URL:** `/api/v1/<tool_id>/query`

---

## Endpoints

### Query Tool
**POST** `/api/v1/<tool_id>/query`

Submits a query to a specific tool with optional conversation history. For the "system" tool, additional system information is required and processed specially.

#### URL Parameters
- `tool_id` (string, required) - Identifier for the tool (e.g., "system", "playbooks")

#### Request Body (JSON)
```json
{
  "user_prompt": "Your question or request here",
  "conversation": [
    {
      "role": "user",
      "content": "Previous user message"
    },
    {
      "role": "assistant",
      "content": "Previous assistant response"
    }
  ],
  "system": {
    "name": "System Name",
    "description": "System description",
    "components": ["component1", "component2"]
  }
}
```

#### Request Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_prompt` | String | ✓ | The user's query or prompt |
| `conversation` | Array | ✗ | Previous conversation turns |
| `conversation[].role` | String | ✓ | Either "user" or "assistant" |
| `conversation[].content` | String | ✓ | Message content |
| `system` | Object | ✗* | System information (*required when tool_id="system") |

#### Success Response - System Tool (200 OK)
```json
{
  "tool_id": "system",
  "status": "processed",
  "result": {
    "answer": "Response from system processor",
    "context": "Additional context"
  },
  "conversation": [
    {
      "role": "user",
      "content": "Previous message"
    }
  ]
}
```

#### Success Response - Other Tools (200 OK)
```json
{
  "tool_id": "playbooks",
  "received": {
    "user_prompt": "Your question here"
  },
  "status": "queued",
  "conversation": [
    {
      "role": "user",
      "content": "Previous message"
    }
  ]
}
```

#### Error Responses

**400 Bad Request - Not JSON**
```json
{
  "error": "Request body must be JSON"
}
```

**400 Bad Request - Invalid JSON**
```json
{
  "error": "Invalid JSON payload"
}
```

**422 Unprocessable Entity - Validation Error**
```json
{
  "error": "validation_error",
  "details": [
    {
      "loc": ["user_prompt"],
      "msg": "Field required",
      "type": "missing"
    }
  ]
}
```

**422 Unprocessable Entity - Missing System Info**
```json
{
  "error": "validation_error",
  "details": [
    {
      "loc": ["system"],
      "msg": "Field required",
      "type": "missing"
    }
  ]
}
```

---

## Example Usage

### cURL Examples

#### Basic Query
```bash
curl -X POST http://localhost:5000/api/v1/playbooks/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_prompt": "How do I deploy the application?"
  }'
```

#### Query with Conversation History
```bash
curl -X POST http://localhost:5000/api/v1/system/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_prompt": "What are the main features?",
    "conversation": [
      {
        "role": "user",
        "content": "Tell me about the system"
      },
      {
        "role": "assistant",
        "content": "This is a document management system..."
      }
    ],
    "system": {
      "name": "DocuManager",
      "description": "Document management and retrieval system",
      "components": ["storage", "search", "api"]
    }
  }'
```

### JavaScript/Fetch Example

```javascript
// Query with conversation history
const response = await fetch('http://localhost:5000/api/v1/system/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    user_prompt: 'How does the search feature work?',
    conversation: [
      {
        role: 'user',
        content: 'What features are available?'
      },
      {
        role: 'assistant',
        content: 'The system includes document upload, search, and retrieval features.'
      }
    ],
    system: {
      name: 'DocumentSystem',
      description: 'Enterprise document management',
      components: ['upload', 'search', 'retrieval']
    }
  })
});

const result = await response.json();
console.log(result);
```

### Python Example

```python
import requests

# Query with system information
payload = {
    "user_prompt": "Explain the architecture",
    "conversation": [
        {
            "role": "user",
            "content": "What is this system?"
        },
        {
            "role": "assistant",
            "content": "This is a document processing system."
        }
    ],
    "system": {
        "name": "DocProcessor",
        "description": "Automated document processing",
        "components": ["parser", "analyzer", "storage"]
    }
}

response = requests.post(
    'http://localhost:5000/api/v1/system/query',
    json=payload
)

print(response.json())
```

---

## Tool-Specific Behavior

### System Tool (`tool_id="system"`)
- **Requires** `system` object in request body
- Processes query using system-specific logic
- Returns processed result with status "processed"
- Supports conversation context for multi-turn interactions

### Other Tools
- Optional `system` object (ignored)
- Echoes the user prompt back with status "queued"
- Intended for future processing implementation
- Conversation history is preserved in response

---

## Conversation Context

The conversation array maintains the context of multi-turn interactions:
- Each turn has a `role` ("user" or "assistant") and `content`
- Conversation history is passed to processors for context-aware responses
- Order is preserved (oldest to newest)
- Maximum recommended turns: 20 (for performance)

---

# Libraries Blueprint

## Overview
The Libraries Blueprint provides endpoints for managing document libraries within the system. It supports uploading documents with metadata, chunking content for vectorization, and retrieving library information.

**Base URL:** `/api/v1/<tool_id>/libraries`

---

## Endpoints

### 1. List Libraries
**GET** `/api/v1/<tool_id>/libraries`

Retrieves all document libraries associated with a specific tool.

#### URL Parameters
- `tool_id` (string, required) - Identifier for the tool (e.g., "system", "playbooks")

#### Success Response (200 OK)
```json
{
  "tool_id": "system",
  "libraries": [
    {
      "id": 1,
      "filename": "manual.pdf",
      "tool_id": "system",
      "uploaded_at": "2025-12-10T10:30:00Z",
      "metadata": {...}
    }
  ]
}
```

#### Error Response (500 Internal Server Error)
```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred",
  "details": "Error details here"
}
```

---

### 2. Upload Library File
**POST** `/api/v1/<tool_id>/libraries`

Uploads a document file with optional metadata. The file is processed, chunked, and stored for vectorization.

#### URL Parameters
- `tool_id` (string, required) - Identifier for the tool

#### Request (multipart/form-data)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file` | File | ✓ | - | Document file (PDF, DOCX, TXT) |
| `metadata` | JSON String | ✗ | null | Document metadata as JSON |
| `chunk_size` | Integer | ✗ | 1000 | Maximum characters per chunk |
| `chunk_overlap` | Integer | ✗ | 200 | Character overlap between chunks |
| `uploaded_by` | String | ✗ | "anonymous" | Username or identifier |

#### Metadata Schema (Optional)
```json
{
  "title": "Document Title",
  "description": "Document description",
  "topic": "Main topic",
  "keywords": ["keyword1", "keyword2"],
  "category": "Category name",
  "author": "Author name",
  "organization": "Organization name",
  "version": "1.0",
  "document_date": "2025-12-10",
  "last_updated": "2025-12-10",
  "language": "en",
  "source_url": "https://example.com/doc",
  "notes": "Additional notes",
  "visibility": "public",
  "department": "Engineering"
}
```

#### Success Response (201 Created)
```json
{
  "status": "success",
  "file_path": "data/libraries/system/manual.pdf",
  "metadata_path": "data/libraries/system/manual.pdf.metadata.json",
  "num_chunks": 42
}
```

#### Error Responses

**400 Bad Request - No File**
```json
{
  "error": "no_file",
  "message": "No file part in the request"
}
```

**400 Bad Request - Invalid JSON**
```json
{
  "error": "invalid_json",
  "message": "metadata must be valid JSON string",
  "details": "Expecting property name enclosed in double quotes: line 1 column 2 (char 1)"
}
```

**400 Bad Request - Invalid Parameters**
```json
{
  "error": "invalid_parameters",
  "message": "chunk_size and chunk_overlap must be integers",
  "details": "invalid literal for int() with base 10: 'abc'"
}
```

**400 Bad Request - Invalid File**
```json
{
  "error": "invalid_file",
  "message": "File must be UTF-8 encoded text"
}
```

**422 Unprocessable Entity - Metadata Validation Error**
```json
{
  "error": "metadata_validation_error",
  "message": "Metadata validation failed",
  "details": [
    {
      "loc": ["keywords"],
      "msg": "Input should be a valid list",
      "type": "list_type"
    }
  ]
}
```

**500 Internal Server Error - Storage Error**
```json
{
  "error": "storage_error",
  "message": "Failed to save file data/libraries/system/manual.pdf: Permission denied"
}
```

**500 Internal Server Error - Processing Error**
```json
{
  "error": "processing_error",
  "message": "Failed to chunk file content: Unsupported file type"
}
```

---

## Example Usage

### cURL Examples

#### List Libraries
```bash
curl -X GET http://localhost:5000/api/v1/system/libraries
```

#### Upload File (Basic)
```bash
curl -X POST http://localhost:5000/api/v1/system/libraries \
  -F "file=@/path/to/document.pdf"
```

#### Upload File with Metadata
```bash
curl -X POST http://localhost:5000/api/v1/system/libraries \
  -F "file=@/path/to/manual.pdf" \
  -F 'metadata={"title":"User Manual","keywords":["guide","reference"],"category":"Documentation"}' \
  -F "chunk_size=1500" \
  -F "chunk_overlap=300" \
  -F "uploaded_by=john.doe"
```

### JavaScript/Fetch Example

```javascript
// Upload file with metadata
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('metadata', JSON.stringify({
  title: 'System Manual',
  keywords: ['manual', 'system', 'documentation'],
  category: 'Technical Documentation'
}));
formData.append('chunk_size', '1000');
formData.append('chunk_overlap', '200');
formData.append('uploaded_by', 'user@example.com');

const response = await fetch('http://localhost:5000/api/v1/system/libraries', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(result);
```

### Python Example

```python
import requests

# Upload file
files = {'file': open('document.pdf', 'rb')}
data = {
    'metadata': '{"title":"Technical Guide","keywords":["technical","guide"]}',
    'chunk_size': '1000',
    'chunk_overlap': '200',
    'uploaded_by': 'admin'
}

response = requests.post(
    'http://localhost:5000/api/v1/system/libraries',
    files=files,
    data=data
)

print(response.json())
```

---

## File Processing Pipeline

1. **Validation** - File presence and metadata validation
2. **Reading** - UTF-8 decoding of file content
3. **Sanitization** - Filename sanitization to prevent path traversal
4. **Metadata Enrichment** - System fields added (uploaded_by, saved_at, etc.)
5. **Storage** - File and metadata saved to disk
6. **Chunking** - Content split into chunks based on size/overlap parameters
7. **Vectorization** - Chunks processed for semantic search (future feature)

---

## Supported File Types

- **PDF** - Portable Document Format (.pdf)
- **DOCX** - Microsoft Word Document (.docx)
- **TXT** - Plain Text (.txt)

---

## Error Handling

The API uses standard HTTP status codes and returns structured error responses:

- **400** - Client errors (invalid input, missing file, etc.)
- **422** - Validation errors (metadata schema violations)
- **500** - Server errors (storage failures, processing errors)

All error responses include:
- `error`: Error code (machine-readable)
- `message`: Human-readable error description
- `details`: Additional context (optional)

---

## Notes

- Maximum file size: Determined by Flask configuration (default: 16MB)
- Chunk size recommended range: 500-2000 characters
- Chunk overlap recommended range: 50-400 characters
- Files are stored in: `data/libraries/<tool_id>/<filename>`
- Metadata sidecars: `data/libraries/<tool_id>/<filename>.metadata.json`
