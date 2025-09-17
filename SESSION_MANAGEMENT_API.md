# Session Management API Documentation

## Overview
Added session management for single-user chat system with the ability to create new chats, switch between previous chat sessions, and delete specific chats.

## Key Behavior Changes
- **No New Session on Refresh**: When you refresh the webapp, it now loads the most recent existing session instead of creating a new one
- **Persistent Sessions**: Your chat history persists across browser refreshes
- **Auto-Resume**: The system automatically resumes your most recent conversation

## New API Endpoints

### 1. Create New Session
```
POST /api/sessions/new
Content-Type: application/json

Request Body:
{
  "session_name": "My New Chat"  // Optional, auto-generates if not provided
}

Response:
{
  "success": true,
  "session_id": "My_New_Chat",
  "message": "New session created successfully"
}
```

### 2. Switch to Existing Session
```
POST /api/sessions/switch
Content-Type: application/json

Request Body:
{
  "session_id": "Chat_09_16_11_11"
}

Response:
{
  "success": true,
  "session_id": "Chat_09_16_11_11",
  "message": "Session switched successfully"
}
```

### 3. Get Current Session Info
```
GET /api/sessions/current

Response:
{
  "session_id": "main_session",
  "message_count": 5,
  "has_user_messages": true
}
```

### 4. Save Current Chat (Updated)
```
POST /api/save-chat

Response:
{
  "success": true,
  "blob_name": "chat_session_My_Chat_20250916_141500.json",
  "message": "Session 'My_Chat' saved successfully"
}
```

### 5. List All Chat Sessions (Existing)
```
GET /api/chat-sessions

Response:
{
  "sessions": [
    {
      "session_id": "Chat_09_16_11_11",
      "latest_timestamp": "20250916_111100",
      "latest_blob": "chat_session_Chat_09_16_11_11_20250916_111100.json",
      "last_modified": "2025-09-16T11:11:00.000Z",
      "size": 1024
    }
  ]
}
```

### 6. Delete Chat Session (Existing)
```
DELETE /api/chat-sessions/{blob_name}

Response:
{
  "success": true,
  "message": "Chat session deleted successfully"
}
```

## Frontend Integration Examples

### JavaScript Implementation:

```javascript
// Create new chat session
const createNewChat = async (sessionName = null) => {
  const response = await fetch('http://localhost:8000/api/sessions/new', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_name: sessionName })
  });
  return response.json();
};

// Switch to existing chat
const switchToChat = async (sessionId) => {
  const response = await fetch('http://localhost:8000/api/sessions/switch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId })
  });
  return response.json();
};

// Get current session
const getCurrentSession = async () => {
  const response = await fetch('http://localhost:8000/api/sessions/current');
  return response.json();
};

// Save current chat
const saveCurrentChat = async () => {
  const response = await fetch('http://localhost:8000/api/save-chat', {
    method: 'POST'
  });
  return response.json();
};

// Get all chat sessions
const getAllChats = async () => {
  const response = await fetch('http://localhost:8000/api/chat-sessions');
  return response.json();
};

// Delete a chat session
const deleteChat = async (blobName) => {
  const response = await fetch(`http://localhost:8000/api/chat-sessions/${blobName}`, {
    method: 'DELETE'
  });
  return response.json();
};
```

## Key Features Implemented

✅ **Multiple Chat Sessions**: Each session maintains separate conversation history
✅ **Auto-naming**: Sessions get automatic names like "Chat 09/16 14:15" if no name provided
✅ **Session Switching**: Seamless switching between different chat sessions
✅ **Auto-save**: Current session saves when switching or on app shutdown
✅ **Delete Support**: Individual chat sessions can be deleted
✅ **Single User**: No user authentication needed, all sessions belong to one user
✅ **Minimal Code**: Only essential functionality, no unnecessary complexity
✅ **No Refresh Sessions**: Browser refresh loads most recent session instead of creating new ones
✅ **Persistent Resume**: Conversation history persists across browser refreshes

## UI Integration

Your "Previous Chats" sidebar can now:
1. **"+ New Chat" button** → Calls `POST /api/sessions/new`
2. **Chat list items** → Calls `POST /api/sessions/switch` when clicked
3. **Delete buttons** → Calls `DELETE /api/chat-sessions/{blob_name}`
4. **Current session indicator** → Shows active session from `GET /api/sessions/current`

The system automatically handles saving the current session when switching, so users don't lose their work!