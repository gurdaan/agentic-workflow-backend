"""
Azure Blob Storage Service for Chat History Persistence
Handles saving, loading, and managing chat history data in Azure Blob Storage.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from azure.storage.blob.aio import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
import os


class ChatStorageService:
    """
    Async service for managing chat history in Azure Blob Storage.
    Handles single-user chat persistence with automatic timestamping.
    """
    
    def __init__(self, container_name: str = "chat-history"):
        """
        Initialize the chat storage service.
        
        Args:
            container_name: Blob container name for chat storage
        """
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.container_name = container_name
        self.blob_service_client = None
        self.logger = logging.getLogger(__name__)
        
        if not self.connection_string:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING environment variable is required")
    
    async def initialize(self) -> None:
        """Initialize the blob service client and ensure container exists."""
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
            
            # Ensure container exists
            await self._ensure_container_exists()
            self.logger.info(f"✅ Chat storage initialized with container: {self.container_name}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize chat storage: {e}")
            raise
    
    async def _ensure_container_exists(self) -> None:
        """Ensure the chat history container exists, create if it doesn't."""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            await container_client.get_container_properties()
            self.logger.debug(f"Container {self.container_name} already exists")
        except ResourceNotFoundError:
            # Container doesn't exist, create it
            await self.blob_service_client.create_container(self.container_name)
            self.logger.info(f"📁 Created container: {self.container_name}")
        except Exception as e:
            self.logger.error(f"❌ Error checking/creating container: {e}")
            raise
    
    async def save_chat_history(self, 
                              chat_data: List[Dict[str, Any]], 
                              session_id: Optional[str] = None) -> str:
        """
        Save chat history to blob storage.
        
        Args:
            chat_data: List of chat messages/interactions
            session_id: Optional session identifier (timestamp used if not provided)
            
        Returns:
            The blob name where the chat was saved
        """
        try:
            # Generate blob name with timestamp
            if not session_id:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                session_id = f"chat_session_{timestamp}"
            
            blob_name = f"{session_id}.json"
            
            # Prepare chat data with metadata
            chat_document = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "message_count": len(chat_data),
                "chat_history": chat_data
            }
            
            # Convert to JSON
            json_data = json.dumps(chat_document, indent=2, ensure_ascii=False)
            
            # Upload to blob storage
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            await blob_client.upload_blob(
                json_data,
                overwrite=True,
                content_type="application/json"
            )
            
            self.logger.info(f"💾 Chat history saved: {blob_name} ({len(chat_data)} messages)")
            return blob_name
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save chat history: {e}")
            raise
    
    async def load_chat_history(self, blob_name: str) -> Optional[Dict[str, Any]]:
        """
        Load chat history from blob storage.
        
        Args:
            blob_name: Name of the blob to load
            
        Returns:
            Chat document with history and metadata, or None if not found
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Download blob content
            download_stream = await blob_client.download_blob()
            json_data = await download_stream.readall()
            
            # Parse JSON
            chat_document = json.loads(json_data.decode('utf-8'))
            
            self.logger.info(f"📖 Chat history loaded: {blob_name}")
            return chat_document
            
        except ResourceNotFoundError:
            self.logger.warning(f"⚠️ Chat history not found: {blob_name}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Failed to load chat history: {e}")
            raise
    
    async def list_chat_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List available chat sessions with metadata.
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of session metadata dictionaries
        """
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            sessions = []
            
            async for blob in container_client.list_blobs():
                if len(sessions) >= limit:
                    break
                
                # Only process .json files
                if blob.name.endswith(".json"):
                    sessions.append({
                        "blob_name": blob.name,
                        "session_id": blob.name.replace(".json", ""),
                        "last_modified": blob.last_modified.isoformat() if blob.last_modified else None,
                        "size": blob.size
                    })
            
            # Sort by last modified (newest first)
            sessions.sort(key=lambda x: x.get("last_modified", ""), reverse=True)
            
            self.logger.info(f"📋 Found {len(sessions)} chat sessions")
            return sessions
            
        except Exception as e:
            self.logger.error(f"❌ Failed to list chat sessions: {e}")
            raise
    
    async def delete_chat_session(self, blob_name: str) -> bool:
        """
        Delete a chat session from storage.
        
        Args:
            blob_name: Name of the blob to delete
            
        Returns:
            True if deleted successfully, False if not found
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            await blob_client.delete_blob()
            self.logger.info(f"🗑️ Chat session deleted: {blob_name}")
            return True
            
        except ResourceNotFoundError:
            self.logger.warning(f"⚠️ Chat session not found for deletion: {blob_name}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Failed to delete chat session: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up resources and close connections."""
        try:
            if self.blob_service_client:
                await self.blob_service_client.close()
                self.logger.info("🧹 Chat storage service cleaned up")
        except Exception as e:
            self.logger.warning(f"⚠️ Chat storage cleanup warning: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()


# Utility functions for easy integration
async def save_chat_on_app_close(chat_data: List[Dict[str, Any]], 
                                storage_service: ChatStorageService) -> str:
    """
    Convenience function to save chat history when app closes.
    
    Args:
        chat_data: Chat messages to save
        storage_service: Initialized storage service
        
    Returns:
        Blob name where chat was saved
    """
    try:
        return await storage_service.save_chat_history(chat_data)
    except Exception as e:
        logging.error(f"❌ Failed to save chat on app close: {e}")
        raise


async def create_chat_storage_service(account_name: Optional[str] = None) -> ChatStorageService:
    """
    Factory function to create and initialize a chat storage service.
    
    Args:
        account_name: Azure Storage account name
        
    Returns:
        Initialized ChatStorageService
    """
    service = ChatStorageService(account_name=account_name)
    await service.initialize()
    return service