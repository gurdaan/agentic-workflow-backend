# Azure Boards AI Agent API - OpenAPI Documentation

This directory contains comprehensive OpenAPI 3.0.3 documentation for the Azure Boards AI Agent backend API.

## 📋 Files

- **`OpenAPISchema.json`** - Complete OpenAPI specification in JSON format
- **`api-docs.html`** - Interactive Swagger UI documentation viewer
- **`README-API.md`** - This documentation file

## 🚀 Viewing the Documentation

### Option 1: Interactive Swagger UI (Recommended)
1. Open `api-docs.html` in your web browser
2. The documentation will load with an interactive interface
3. You can test API endpoints directly from the browser
4. View request/response examples and schemas

### Option 2: Online Swagger Editor
1. Go to [editor.swagger.io](https://editor.swagger.io/)
2. Copy the contents of `OpenAPISchema.json` 
3. Paste into the editor to view and edit

### Option 3: VS Code Extension
1. Install the "OpenAPI (Swagger) Editor" extension in VS Code
2. Open `OpenAPISchema.json` in VS Code
3. Use Ctrl/Cmd + Shift + P and search for "OpenAPI Preview"

## 🌐 API Overview

### Base URLs
- **Production**: https://jonas.victorioussmoke-3dca34aa.westus2.azurecontainerapps.io
- **Development**: http://localhost:8000

### API Categories

#### 🤖 Chat Endpoints
- `POST /api/chat` - Process AI queries for generating work items
- Supports user story, test case, and development task generation
- Intelligent routing to specialized AI agents

#### 📁 Session Management  
- `POST /api/sessions/new` - Create new chat sessions
- `POST /api/sessions/switch` - Switch between sessions
- `GET /api/sessions/current` - Get current session info
- `POST /api/save-chat` - Manually save chat history

#### 📚 Session Storage
- `GET /api/chat-sessions` - List all saved sessions
- `GET /api/chat-sessions/{blob_name}` - Load specific session
- `DELETE /api/chat-sessions/{blob_name}` - Delete session

#### ❤️ Health Check
- `GET /health` - Service health status

## 🔧 Key Features

### AI Agent Types
1. **User Story Agent** - Generates Agile user stories with acceptance criteria
2. **Test Cases Agent** - Creates comprehensive test scenarios
3. **Development Tasks Agent** - Breaks features into actionable tasks
4. **Azure DevOps Agent** - Manages work items in Azure Boards

### Response Metadata
All chat responses include metadata flags:
- `userstory` - Contains generated user story
- `testcase` - Contains test cases
- `devtask` - Contains development tasks
- `needs_clarification` - Requires more info
- `needs_save_confirmation` - Ready to save to Azure Boards

### Session Persistence
- Automatic saving after each message exchange
- Azure Blob Storage integration
- Session switching with conversation history
- Manual save capability

## 📝 Example Usage

### Generate a User Story
```bash
curl -X POST "https://jonas.victorioussmoke-3dca34aa.westus2.azurecontainerapps.io/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Create a user story for implementing two-factor authentication in our web application"
  }'
```

### Create New Session
```bash
curl -X POST "https://jonas.victorioussmoke-3dca34aa.westus2.azurecontainerapps.io/api/sessions/new" \
  -H "Content-Type: application/json" \
  -d '{
    "session_name": "Security Features Sprint"
  }'
```

### List All Sessions
```bash
curl -X GET "https://jonas.victorioussmoke-3dca34aa.westus2.azurecontainerapps.io/api/chat-sessions"
```

## 🔐 Authentication & Environment

The API requires proper Azure service configuration:
- Azure OpenAI endpoint and API key
- Azure AI Foundry assistants
- Azure DevOps Personal Access Token
- Azure Blob Storage connection string

## 📊 Response Format

All chat responses follow this structure:
```json
{
  "content": "Generated markdown content...",
  "metadata": {
    "userstory": true,
    "testcase": false,
    "devtask": false,
    "needs_clarification": false,
    "needs_save_confirmation": true,
    "content_complete": true,
    "sections_count": 5,
    "word_count": 243,
    "azure_boards_ready": false
  }
}
```

## 🚀 Integration Examples

### Frontend Integration (JavaScript)
```javascript
// Send chat query
const response = await fetch('/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'Create a user story for user login feature'
  })
});

const result = await response.json();
console.log('Generated content:', result.content);
console.log('Is user story?', result.metadata.userstory);
```

### Python Integration
```python
import requests

# Generate user story
response = requests.post(
    'https://jonas.victorioussmoke-3dca34aa.westus2.azurecontainerapps.io/api/chat',
    json={'query': 'Create test cases for login functionality'},
    headers={'Content-Type': 'application/json'}
)

result = response.json()
print(f"Generated: {result['content']}")
print(f"Metadata: {result['metadata']}")
```

## 🛠️ Development & Testing

### Local Development
1. Run the API locally: `uvicorn app:app --host 0.0.0.0 --port 8000`
2. Open `api-docs.html` in your browser
3. Change the server URL to `http://localhost:8000` in the Swagger UI

### Testing with Swagger UI
1. Select an endpoint in the documentation
2. Click "Try it out"
3. Fill in the required parameters
4. Click "Execute" to test the API
5. View the response and curl command

## 📄 License

This API documentation is part of the Azure Boards AI Agent project and is licensed under the MIT License.

---

For more information about the backend implementation, see the main project repository at [gurdaan/agentic-workflow-backend](https://github.com/gurdaan/agentic-workflow-backend).