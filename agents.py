"""
Simplified Azure Boards AI Agent Service
"""

import os
import re
import json
import logging
from typing import Dict, Any, List
import semantic_kernel as sk
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.mcp import MCPStdioPlugin
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.contents.chat_history import ChatHistory
from dotenv import load_dotenv
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import MessageRole
from azure.identity import DefaultAzureCredential
from blob_storage_service import ChatStorageService
import markdown2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_service.log'),
        logging.StreamHandler()
    ]
)

# Disable verbose Azure SDK logging
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logging.getLogger("azure.identity").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("semantic_kernel.connectors.ai.open_ai.services.open_ai_handler").setLevel(logging.WARNING)
logging.getLogger("semantic_kernel.connectors.ai.chat_completion_client_base").setLevel(logging.WARNING)
logging.getLogger("semantic_kernel.functions.kernel_function").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

load_dotenv()

class MarkdownConverterPlugin:
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MarkdownConverterPlugin")
    
    @kernel_function(
        name="convert_markdown_to_html",
        description="Convert markdown content to HTML format suitable for Azure Boards."
    )
    async def convert_markdown_to_html_func(self, markdown_content: str) -> str:
        """Convert markdown content to HTML."""
        try:
            if not markdown_content:
                return ""
            
            html_content = markdown2.markdown(markdown_content)
            self.logger.info(f"🔄 Converted markdown to HTML ({len(html_content)} chars)")
            return html_content
        except Exception as e:
            self.logger.error(f"❌ Markdown conversion error: {e}")
            return markdown_content  # Return original if conversion fails

class AIFoundryPlugin:
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AIFoundryPlugin")
    
    @kernel_function(
        name="run_ai_foundry_agent",
        description="Generate formal Agile user stories with acceptance criteria."
    )
    async def run_ai_foundry_agent_func(self, user_request: str) -> str:
        self.logger.info("🚀 User Story Agent called")
        self.logger.info(f"📝 Request: {user_request}")
        
        try:
            endpoint = os.getenv("AI_FOUNDRY_ENDPOINT")
            assistant_id = os.getenv("AI_FOUNDRY_ASSISTANT_ID")
            
            agents_client = AgentsClient(
                endpoint=endpoint,
                credential=DefaultAzureCredential()
            )

            with agents_client:
                agent = agents_client.get_agent(assistant_id)
                self.logger.info(f"📋 Agent: {agent.name if hasattr(agent, 'name') else 'User Story Agent'}")
                
                thread = agents_client.threads.create()
                
                agents_client.messages.create(
                    thread_id=thread.id,
                    role=MessageRole.USER,
                    content=user_request
                )
                
                self.logger.info("⚡ Processing request...")
                run = agents_client.runs.create_and_process(
                    thread_id=thread.id, 
                    agent_id=agent.id
                )
                
                messages = agents_client.messages.list(thread_id=thread.id)
                # Convert ItemPaged to list to get count
                message_list = list(messages)
                
                for msg in message_list:
                    if msg.text_messages and msg.role.lower() == "assistant":
                        response_content = msg.text_messages[-1].text.value
                        self.logger.info(f"✅ User Story Generated ({len(response_content)} chars)")
                        self.logger.info(f"� Preview: {response_content[:150]}...")
                        return response_content
                
                self.logger.warning("⚠️ No response received")
                return "No response from AI Foundry agent"
                
        except Exception as e:
            self.logger.error(f"❌ User Story Agent error: {e}")
            return f"Error: {e}"

    @kernel_function(
        name="run_ai_foundry_testcases_agent",
        description="Generate test cases for user stories."
    )
    async def run_ai_foundry_testcases_agent(self, user_request: str) -> str:
        self.logger.info("🚀 Test Cases Agent called")
        self.logger.info(f"📝 Request: {user_request}")
        
        try:
            endpoint = os.getenv("AI_FOUNDRY_ENDPOINT")
            assistant_id = os.getenv("AI_FOUNDRY_TESTCASES_ASSISTANT_ID")
            
            agents_client = AgentsClient(
                endpoint=endpoint,
                credential=DefaultAzureCredential()
            )

            with agents_client:
                agent = agents_client.get_agent(assistant_id)
                self.logger.info(f"📋 Agent: {agent.name if hasattr(agent, 'name') else 'Test Cases Agent'}")
                
                thread = agents_client.threads.create()
                
                agents_client.messages.create(
                    thread_id=thread.id,
                    role=MessageRole.USER,
                    content=user_request
                )
                
                self.logger.info("⚡ Processing request...")
                run = agents_client.runs.create_and_process(
                    thread_id=thread.id, 
                    agent_id=agent.id
                )
                
                messages = agents_client.messages.list(thread_id=thread.id)
                # Convert ItemPaged to list to get count
                message_list = list(messages)
                
                for msg in message_list:
                    if msg.text_messages and msg.role.lower() == "assistant":
                        response_content = msg.text_messages[-1].text.value
                        self.logger.info(f"✅ Test Cases Generated ({len(response_content)} chars)")
                        self.logger.info(f"� Preview: {response_content[:150]}...")
                        return response_content
                
                self.logger.warning("⚠️ No response received")
                return "No response from AI Foundry agent"
                
        except Exception as e:
            self.logger.error(f"❌ Test Cases Agent error: {e}")
            return f"Error: {e}"

    @kernel_function(
        name="run_ai_foundry_dev_tasks_agent",
        description="Generate development tasks for user stories."
    )
    async def run_ai_foundry_dev_tasks_agent(self, user_request: str) -> str:
        self.logger.info("🚀 Dev Tasks Agent called")
        self.logger.info(f"📝 Request: {user_request}")

        try:
            endpoint = os.getenv("AI_FOUNDRY_ENDPOINT")
            assistant_id = os.getenv("AI_FOUNDRY_DEV_TASKS_ASSISTANT_ID")

            agents_client = AgentsClient(
                endpoint=endpoint,
                credential=DefaultAzureCredential()
            )

            with agents_client:
                agent = agents_client.get_agent(assistant_id)
                self.logger.info(f"📋 Agent: {agent.name if hasattr(agent, 'name') else 'Dev Tasks Agent'}")

                thread = agents_client.threads.create()

                agents_client.messages.create(
                    thread_id=thread.id,
                    role=MessageRole.USER,
                    content=user_request
                )

                self.logger.info("⚡ Processing request...")
                run = agents_client.runs.create_and_process(
                    thread_id=thread.id,
                    agent_id=agent.id
                )

                messages = agents_client.messages.list(thread_id=thread.id)
                # Convert ItemPaged to list to get count
                message_list = list(messages)

                for msg in message_list:
                    if msg.text_messages and msg.role.lower() == "assistant":
                        response_content = msg.text_messages[-1].text.value
                        self.logger.info(f"✅ Dev Tasks Generated ({len(response_content)} chars)")
                        self.logger.info(f"� Preview: {response_content[:150]}...")
                        return response_content

                self.logger.warning("⚠️ No response received")
                return "No response from AI Foundry agent"

        except Exception as e:
            self.logger.error(f"❌ Dev Tasks Agent error: {e}")
            return f"Error: {e}"

class AgentService:
    def __init__(self):
        self.kernel = None
        self.chat_service = None
        self.conversation = None
        self.mcp_plugin = None  # Track MCP plugin for cleanup
        self.chat_storage = None  # Initialize as None, will be set up in initialize()
        self.current_session_id = "main_session"  # Track current session
        self.logger = logging.getLogger(f"{__name__}.AgentService")
        self.logger.info("🏗️ AgentService initialized")
        
    async def cleanup(self):
        """Properly cleanup MCP connections and chat storage"""
        if self.mcp_plugin:
            try:
                await self.mcp_plugin.disconnect()
                self.logger.info("🧹 MCP plugin disconnected")
            except Exception as e:
                self.logger.warning(f"⚠️ MCP cleanup warning: {e}")
        
        if self.chat_storage:
            try:
                await self.chat_storage.cleanup()
                self.logger.info("🧹 Chat storage cleaned up")
            except Exception as e:
                self.logger.warning(f"⚠️ Chat storage cleanup warning: {e}")
        
    async def __aenter__(self):
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
        
    async def initialize(self):
        if self.kernel:
            self.logger.info("♻️ Service already initialized")
            return
            
        self.logger.info("🚀 Initializing Agent Service...")
        
        # Setup kernel
        self.kernel = sk.Kernel()
        
        # Add Azure OpenAI
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        
        self.chat_service = AzureChatCompletion(
            deployment_name=deployment,
            endpoint=endpoint,
            api_key=api_key
        )
        self.kernel.add_service(self.chat_service)
        self.logger.info("✅ Azure OpenAI connected")
        
        # Add MCP plugin
        try:
            # Create environment for MCP subprocess with proper configuration
            mcp_env = os.environ.copy()
            mcp_env.update({
                "AZURE_DEVOPS_PAT": os.getenv("AZURE_DEVOPS_PAT"),
                "AZURE_DEVOPS_ORGANIZATION_URL": os.getenv("AZURE_DEVOPS_ORGANIZATION_URL"),
                "AZURE_DEVOPS_PROJECT": "agentic-workflow"
            })
            
            mcp_plugin = MCPStdioPlugin(
                name="AzureBoardsTools",
                command=".venv/bin/python",
                args=["-m", "mcp_azure_devops.server"],
                env=mcp_env
            )
            await mcp_plugin.connect()
            self.mcp_plugin = mcp_plugin  # Store for cleanup
            self.kernel.add_plugin(mcp_plugin, "AzureBoardsTools")
            self.logger.info("✅ Azure DevOps MCP connected")
            
        except Exception as e:
            self.logger.error(f"❌ MCP connection failed: {e}")
        
        # Add AI Foundry plugin
        try:
            ai_foundry_plugin = AIFoundryPlugin()
            self.kernel.add_plugin(ai_foundry_plugin, "AIFoundryTools")
            self.logger.info("✅ AI Foundry agents connected")
        except Exception as e:
            self.logger.error(f"❌ AI Foundry plugin failed: {e}")

        # Add Markdown Converter plugin
        try:
            markdown_plugin = MarkdownConverterPlugin()
            self.kernel.add_plugin(markdown_plugin, "MarkdownTools")
            self.logger.info("✅ Markdown converter plugin added")
        except Exception as e:
            self.logger.error(f"❌ Markdown plugin failed: {e}")
        
        # Initialize conversation
        self.conversation = ChatHistory()
        self.conversation.add_system_message("""
            You are the **Orchestrator AI Assistant**, a highly skilled and adaptable AI responsible for managing project-related tasks. Your primary function is to understand user intent, build a complete context for the request, and route it to the correct specialized tool.

            ### **1. Intent Mapping & Context Building**

            * **Analyze Request:** Upon receiving a new user request, analyze it to determine the user's core intent.
            * **Build Full Context:** Combine all relevant project details from the conversation history into a single, comprehensive context. This includes the project name, feature description, requirements, and any previously generated artifacts (e.g., user stories, dev tasks).
            * **Identify Intent:** Map the user's intent to one of the following actions:
                * **"create/generate user story"**: The user wants to generate a user story.
                * **"create/generate test cases"**: The user wants to generate test cases.
                * **"create/generate dev tasks"**: The user wants to generate development tasks.
                * **"save to Azure Boards"**: The user explicitly wants to save a generated artifact to Azure Boards.
                * **"show work items"**: The user wants to query or view items in Azure Boards.
                * **"unknown/other"**: The user's intent is unclear or does not match a known action.

            ### **2. Action Rules & Conversation Flow**. 
            * **CORE DIRECTIVES**
                * NO AUTOMATIC WRITES.** You must never perform a write action (creating, modifying, or saving) to an external system like Azure Boards without a separate, explicit user confirmation step, unless the current user request is an explicit instruction to save the work item. This rule takes precedence over all other instructions.
                * **MANDATORY HTML CONVERSION WORKFLOW:** Before ANY content is written to Azure Boards, you MUST follow this exact sequence:
                    1. Generate content using appropriate agent (AI Foundry tools)
                    2. Convert the generated markdown content to HTML using `convert_markdown_to_html` from MarkdownTools
                    3. Use the converted HTML content for Azure Boards operations
                    
                    This applies to ALL Azure Boards write operations including:
                    - Creating new User Stories
                    - Creating new Dev Tasks  
                    - Creating new Test Cases
                    - Creating and linking child work items
                    - Updating descriptions of existing work items
                    **NEVER pass raw markdown content directly to Azure Boards tools.**
                                             
            * **Markdown to HTML Conversion:** Before saving any content to Azure Boards, always convert markdown content to HTML using the `convert_markdown_to_html` function from MarkdownTools. Azure Boards requires HTML format for rich text fields.
            * **Tool Usage:** Always use the designated tool to perform a task. Never perform a task manually.
            * **Avoid Repetition:** If a tool's output indicates missing information, you must ask the user for the details. Do not attempt to fill in the gaps yourself. Once the user provides the information, make a new, complete request with the added details.
            * **Crucial Rule: Generation vs. Saving:**
                * Generating a user story, test case, or dev task is **a distinct and separate action** from saving it to an external system.
                * You **must not** save any item to an external system like Azure Boards unless the user has **explicitly and unequivocally** requested to "save" or "create" it in that system.
                * The generation of an artifact (`create/generate user story`, etc.) is a "read-only" process for the external system. The save action is a "write" process.
            * **Confirmation:**
                * For any action that modifies or creates a permanent record in an external system (like Azure Boards), you **must** ask for explicit user confirmation before proceeding.
                * **Example Flow:**
                    1.  User: "Generate a user story for X."
                    2.  You: Generate the user story.
                    3.  You: "I have generated the user story. Would you like me to save it to Azure Boards?"
                    4.  User: "Yes, please save it."
                    5.  You: Proceed with the save action.
            * **Tool Chaining:**
                * If a user asks to save something that hasn't been generated, politely explain the process and ask if they'd like to generate it first.
                * The `AI Foundry Dev Task Agent` must be used before saving dev tasks.

            ### **3. Response Structure & Metadata**

            * **Strictly JSON Output:** All of your responses **must** be in a valid JSON format.
                ```json
                {
                "content": "A clear, conversational message to the user. This is where you acknowledge requests, ask clarifying questions, or provide results.",
                "metadata": {
                    "userstory": true/false, (true if the final JSON output's 'content' field contains the complete user story; otherwise 'false')
                    "testcase": true/false, (true if the final JSON output's 'content' field contains the complete test cases; otherwise 'false')
                    "devtask": true/false, (true if the final JSON output's 'content' field contains the complete dev tasks; otherwise 'false')
                    "needs_clarification": true/false, (true if required details are missing and you need to ask the user for them; otherwise `false`)
                    "needs_save_confirmation": true/false (true if the user's request requires confirmation before saving to an external system; otherwise `false`)
                }
                }```
            """)

        # Initialize chat storage
        try:
            if not self.chat_storage:
                self.chat_storage = ChatStorageService()
                await self.chat_storage.initialize()
                self.logger.info("✅ Chat storage initialized")
                
                # Load most recent session instead of creating new one
                await self._load_most_recent_session()
        except Exception as e:
            self.logger.warning(f"⚠️ Chat storage initialization failed: {e}")
            # Continue without chat storage if it fails
            self.chat_storage = None

        self.logger.info("🎉 Agent Service ready!")
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        self.logger.info("="*50)
        self.logger.info(f"🎯 NEW QUERY: {query}")
        self.logger.info("="*50)
        
        await self.initialize()
        
        self.conversation.add_user_message(query)
        
        # Auto-save after adding user message
        try:
            await self.save_chat_history()
            self.logger.info("💾 Auto-saved after user message")
        except Exception as e:
            self.logger.warning(f"Auto-save failed after user message: {e}")
        
        # Configure LLM settings
        settings = self.chat_service.instantiate_prompt_execution_settings()
        settings.max_tokens = 2000
        settings.temperature = 0.1
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
        
        self.logger.info("🤖 Processing with LLM and function calling...")
        
        response = await self.chat_service.get_chat_message_content(
            self.conversation,
            settings,
            kernel=self.kernel
        )
        
        # Ensure response content is properly formatted
        response_content = self._ensure_string_content(response.content)
        
        self.logger.info(f"📨 Response received ({len(response_content)} chars)")
        
        # Log function calls if any
        if hasattr(response, 'function_call_results') and response.function_call_results:
            function_count = len(response.function_call_results)
            self.logger.info(f"🔧 Function calls made: {function_count}")
            
            # Log each function call and check for duplicates
            tool_names = []
            for i, func_result in enumerate(response.function_call_results):
                func_name = func_result.function_name if hasattr(func_result, 'function_name') else 'Unknown'
                tool_names.append(func_name)
                self.logger.info(f"  {i+1}. {func_name}")
            
            # Warn about multiple function calls
            if function_count > 1:
                self.logger.warning(f"⚠️ MULTIPLE FUNCTION CALLS DETECTED ({function_count})")
                unique_tools = set(tool_names)
                if len(unique_tools) < len(tool_names):
                    self.logger.error(f"❌ DUPLICATE TOOL CALLS: {tool_names}")
        
        # Add the processed response content to conversation
        self.conversation.add_assistant_message(response_content)
        
        # Auto-save after adding assistant response
        try:
            await self.save_chat_history()
            self.logger.info("💾 Auto-saved after assistant response")
        except Exception as e:
            self.logger.warning(f"Auto-save failed after assistant response: {e}")
        
        # Parse the response with the cleaned content
        parsed_response = self._parse_response(response_content)
        
        self.logger.info(f"✅ Query completed - Metadata: {parsed_response['metadata']}")
        
        return parsed_response
    
    def _parse_response(self, content: str) -> Dict[str, Any]:
        """
        Highly robust response parsing with comprehensive error handling
        Handles all possible content types and formats
        """
        
        # Step 1: Ensure content is always a string
        processed_content = self._ensure_string_content(content)
        
        # Step 2: Try to extract and parse JSON
        parsed_json = self._try_parse_json(processed_content)
        if parsed_json:
            return self._validate_and_normalize_json(parsed_json, processed_content)
        
        # Step 3: Fallback to content analysis
        return self._fallback_content_analysis(processed_content)

    def _ensure_string_content(self, content: Any) -> str:
        """Convert any content type to a valid string"""
        try:
            if content is None:
                return "No response received"
            
            if isinstance(content, str):
                return content
            
            if isinstance(content, list):
                # Handle list of various types
                string_items = []
                for item in content:
                    if isinstance(item, dict):
                        # Convert dict to readable format
                        if 'content' in item:
                            string_items.append(str(item['content']))
                        else:
                            string_items.append(json.dumps(item, indent=2))
                    elif isinstance(item, str):
                        string_items.append(item)
                    else:
                        string_items.append(str(item))
                return '\n'.join(string_items)
            
            if isinstance(content, dict):
                # If it's a dict, try to extract content field or stringify
                if 'content' in content:
                    return self._ensure_string_content(content['content'])
                else:
                    return json.dumps(content, indent=2)
            
            # For any other type, convert to string
            return str(content)
            
        except Exception as e:
            self.logger.warning(f"⚠️ Content conversion error: {e}")
            return f"Error processing content: {str(e)}"

    def _try_parse_json(self, content: str) -> Dict[str, Any] | None:
        """Try multiple JSON parsing strategies"""
        
        # Strategy 1: Look for ```json blocks
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{[^{}]*"content"[^{}]*\})',
            r'(\{.*?"metadata".*?\})'
        ]
        
        for pattern in json_patterns:
            try:
                match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                if match:
                    json_str = match.group(1)
                    parsed = json.loads(json_str)
                    if isinstance(parsed, dict):
                        return parsed
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # Strategy 2: Try parsing the entire content as JSON
        try:
            if content.strip().startswith('{') and content.strip().endswith('}'):
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    return parsed
        except json.JSONDecodeError:
            pass
        
        # Strategy 3: Look for JSON-like structures and attempt to fix common issues
        try:
            # Fix common JSON issues
            fixed_content = content
            fixed_content = re.sub(r'```json\s*|\s*```', '', fixed_content)
            fixed_content = re.sub(r'^\s*```\s*|\s*```\s*$', '', fixed_content)
            
            if fixed_content.strip().startswith('{') and fixed_content.strip().endswith('}'):
                parsed = json.loads(fixed_content)
                if isinstance(parsed, dict):
                    return parsed
        except json.JSONDecodeError:
            pass
        
        return None

    def _validate_and_normalize_json(self, parsed_json: Dict[str, Any], fallback_content: str) -> Dict[str, Any]:
        """Validate and normalize JSON response"""
        try:
            # Ensure content field exists and is a string
            if 'content' not in parsed_json:
                parsed_json['content'] = fallback_content
            else:
                parsed_json['content'] = self._ensure_string_content(parsed_json['content'])
            
            # Ensure metadata exists with defaults
            if 'metadata' not in parsed_json:
                parsed_json['metadata'] = {}
            
            metadata = parsed_json['metadata']
            if not isinstance(metadata, dict):
                metadata = {}
                parsed_json['metadata'] = metadata
            
            # Set default metadata values
            metadata.setdefault('userstory', False)
            metadata.setdefault('testcase', False)
            metadata.setdefault('devtask', False)
            metadata.setdefault('needs_clarification', False)
            metadata.setdefault('needs_save_confirmation', False)
            
            return parsed_json
            
        except Exception as e:
            self.logger.warning(f"⚠️ JSON validation error: {e}")
            return self._fallback_content_analysis(fallback_content)

    def _fallback_content_analysis(self, content: str) -> Dict[str, Any]:
        """Analyze content and create metadata when JSON parsing fails"""
        try:
            content_lower = content.lower()
            
            # Enhanced pattern matching for metadata detection
            metadata = {
                "userstory": bool(re.search(r"user story|as a .+?i want.+?so that|story.*:", content, re.IGNORECASE)),
                "testcase": bool(re.search(r"test case|test scenario|given.+?when.+?then|test.*:", content, re.IGNORECASE)),
                "devtask": bool(re.search(r"development task|dev task|task.*:|implementation|work item.*created|task.*title", content, re.IGNORECASE)),
                "needs_clarification": bool(re.search(r"need.*more.*info|clarification|missing.*detail|please.*provide", content, re.IGNORECASE)),
                "needs_save_confirmation": bool(re.search(r"save.*azure|create.*work.*item|add.*to.*board", content, re.IGNORECASE))
            }
            
            return {
                "content": content,
                "metadata": metadata
            }
            
        except Exception as e:
            self.logger.error(f"❌ Fallback analysis error: {e}")
            # Return absolute fallback with safe defaults
            return {
                "content": content if isinstance(content, str) else str(content),
                "metadata": {
                    "userstory": False,
                    "testcase": False,
                    "devtask": False,
                    "needs_clarification": False,
                    "needs_save_confirmation": False
                }
            }
    
    async def save_chat_history(self) -> str:
        """Save current chat history to blob storage"""
        try:
            if not self.chat_storage:
                raise ValueError("Chat storage not initialized")
            
            # Convert conversation to serializable format
            chat_data = []
            for message in self.conversation.messages:
                chat_data.append({
                    "role": str(message.role),
                    "content": str(message.content),
                    "timestamp": getattr(message, 'timestamp', None)
                })
            
            blob_name = await self.chat_storage.save_chat_history(chat_data, self.current_session_id)
            self.logger.info(f"💾 Chat history saved: {blob_name}")
            return blob_name
        except Exception as e:
            self.logger.error(f"❌ Failed to save chat history: {e}")
            raise

    async def get_chat_sessions(self) -> List[Dict[str, Any]]:
        """Get list of all chat sessions"""
        try:
            if not self.chat_storage:
                raise ValueError("Chat storage not initialized")
            return await self.chat_storage.list_chat_sessions()
        except Exception as e:
            self.logger.error(f"❌ Failed to get chat sessions: {e}")
            raise

    async def load_chat_history(self, blob_name: str) -> Dict[str, Any]:
        """Load a specific chat session"""
        try:
            if not self.chat_storage:
                raise ValueError("Chat storage not initialized")
            return await self.chat_storage.load_chat_history(blob_name)
        except Exception as e:
            self.logger.error(f"❌ Failed to load chat history: {e}")
            raise

    async def delete_chat_session(self, blob_name: str) -> bool:
        """Delete a chat session"""
        try:
            if not self.chat_storage:
                raise ValueError("Chat storage not initialized")
            return await self.chat_storage.delete_chat_session(blob_name)
        except Exception as e:
            self.logger.error(f"❌ Failed to delete chat session: {e}")
            raise

    async def create_new_session(self, session_name: str = None) -> str:
        """Create a new chat session"""
        try:
            if not session_name:
                from datetime import datetime
                timestamp = datetime.now().strftime("%m/%d %H:%M")
                session_name = f"Chat {timestamp}"
            
            # Save current session if it has messages
            if self.has_user_messages:
                await self.save_chat_history()
                self.logger.info(f"💾 Saved previous session: {self.current_session_id}")
            
            # Start new session
            self.current_session_id = session_name.replace(" ", "_").replace("/", "_")
            self.conversation = ChatHistory()
            self.conversation.add_system_message("""
            You are the **Orchestrator AI Assistant**, a highly skilled and adaptable AI responsible for managing project-related tasks. Your primary function is to understand user intent, build a complete context for the request, and route it to the correct specialized tool.

            ### **1. Intent Mapping & Context Building**

            * **Analyze Request:** Upon receiving a new user request, analyze it to determine the user's core intent.
            * **Build Full Context:** Combine all relevant project details from the conversation history into a single, comprehensive context. This includes the project name, feature description, requirements, and any previously generated artifacts (e.g., user stories, dev tasks).
            * **Identify Intent:** Map the user's intent to one of the following actions:
                * **"create/generate user story"**: The user wants to generate a user story.
                * **"create/generate test cases"**: The user wants to generate test cases.
                * **"create/generate dev tasks"**: The user wants to generate development tasks.
                * **"save to Azure Boards"**: The user explicitly wants to save a generated artifact to Azure Boards.
                * **"show work items"**: The user wants to query or view items in Azure Boards.
                * **"unknown/other"**: The user's intent is unclear or does not match a known action.

            ### **2. Action Rules & Conversation Flow**
            * **CORE DIRECTIVES**
                * NO AUTOMATIC WRITES.** You must never perform a write action (creating, modifying, or saving) to an external system like Azure Boards without a separate, explicit user confirmation step, unless the current user request is an explicit instruction to save the work item. This rule takes precedence over all other instructions.
                * **MANDATORY HTML CONVERSION WORKFLOW:** Before ANY content is written to Azure Boards, you MUST follow this exact sequence:
                    1. Generate content using appropriate agent (AI Foundry tools)
                    2. Convert the generated markdown content to HTML using `convert_markdown_to_html` from MarkdownTools
                    3. Use the converted HTML content for Azure Boards operations
                    
                    This applies to ALL Azure Boards write operations including:
                    - Creating new User Stories
                    - Creating new Dev Tasks  
                    - Creating new Test Cases
                    - Creating and linking child work items
                    - Updating descriptions of existing work items
                    **NEVER pass raw markdown content directly to Azure Boards tools.**
                                                 
            * **Markdown to HTML Conversion:** Before saving any content to Azure Boards, always convert markdown content to HTML using the `convert_markdown_to_html` function from MarkdownTools. Azure Boards requires HTML format for rich text fields.
            * **Tool Usage:** Always use the designated tool to perform a task. Never perform a task manually.
            * **Avoid Repetition:** If a tool's output indicates missing information, you must ask the user for the details. Do not attempt to fill in the gaps yourself. Once the user provides the information, make a new, complete request with the added details.
            * **Crucial Rule: Generation vs. Saving:**
                * Generating a user story, test case, or dev task is **a distinct and separate action** from saving it to an external system.
                * You **must not** save any item to an external system like Azure Boards unless the user has **explicitly and unequivocally** requested to "save" or "create" it in that system.
                * The generation of an artifact (`create/generate user story`, etc.) is a "read-only" process for the external system. The save action is a "write" process.
            * **Confirmation:**
                * For any action that modifies or creates a permanent record in an external system (like Azure Boards), you **must** ask for explicit user confirmation before proceeding.
                * **Example Flow:**
                    1.  User: "Generate a user story for X."
                    2.  You: Generate the user story.
                    3.  You: "I have generated the user story. Would you like me to save it to Azure Boards?"
                    4.  User: "Yes, please save it."
                    5.  You: Proceed with the save action.
            * **Tool Chaining:**
                * If a user asks to save something that hasn't been generated, politely explain the process and ask if they'd like to generate it first.
                * The `AI Foundry Dev Task Agent` must be used before saving dev tasks.

            ### **3. Response Structure & Metadata**

            * **Strictly JSON Output:** All of your responses **must** be in a valid JSON format.
                ```json
                {
                "content": "A clear, conversational message to the user. This is where you acknowledge requests, ask clarifying questions, or provide results.",
                "metadata": {
                    "userstory": true/false, (true if the final JSON output's 'content' field contains the complete user story; otherwise 'false')
                    "testcase": true/false, (true if the final JSON output's 'content' field contains the complete test cases; otherwise 'false')
                    "devtask": true/false, (true if the final JSON output's 'content' field contains the complete dev tasks; otherwise 'false')
                    "needs_clarification": true/false, (true if required details are missing and you need to ask the user for them; otherwise `false`)
                    "needs_save_confirmation": true/false (true if the user's request requires confirmation before saving to an external system; otherwise `false`)
                }
                }```   
           """)
            
            # Immediately save the new session to blob storage
            try:
                await self.save_chat_history()
                self.logger.info(f"💾 Immediately saved new session: {self.current_session_id}")
            except Exception as e:
                self.logger.warning(f"Failed to immediately save new session: {e}")
            
            self.logger.info(f"🆕 Created new session: {self.current_session_id}")
            return self.current_session_id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create new session: {e}")
            raise

    async def switch_session(self, session_id: str) -> bool:
        """Switch to an existing chat session by loading its latest conversation"""
        try:
            # Save current session if it has messages
            if self.has_user_messages:
                await self.save_chat_history()
                self.logger.info(f"💾 Saved current session: {self.current_session_id}")
            
            # Find the latest blob for this session
            sessions = await self.get_chat_sessions()
            session_found = False
            latest_blob = None
            
            for session in sessions:
                if session_id in session.get('blob_name', ''):
                    latest_blob = session['blob_name']
                    session_found = True
                    break
            
            if not session_found:
                # Create new session with this ID
                self.current_session_id = session_id
                self.conversation = ChatHistory()
                self.conversation.add_system_message("""
            You are the **Orchestrator AI Assistant**, a highly skilled and adaptable AI responsible for managing project-related tasks. Your primary function is to understand user intent, build a complete context for the request, and route it to the correct specialized tool.

            ### **1. Intent Mapping & Context Building**

            * **Analyze Request:** Upon receiving a new user request, analyze it to determine the user's core intent.
            * **Build Full Context:** Combine all relevant project details from the conversation history into a single, comprehensive context. This includes the project name, feature description, requirements, and any previously generated artifacts (e.g., user stories, dev tasks).
            * **Identify Intent:** Map the user's intent to one of the following actions:
                * **"create/generate user story"**: The user wants to generate a user story.
                * **"create/generate test cases"**: The user wants to generate test cases.
                * **"create/generate dev tasks"**: The user wants to generate development tasks.
                * **"save to Azure Boards"**: The user explicitly wants to save a generated artifact to Azure Boards.
                * **"show work items"**: The user wants to query or view items in Azure Boards.
                * **"unknown/other"**: The user's intent is unclear or does not match a known action.

            ### **2. Action Rules & Conversation Flow**.
            * **CORE DIRECTIVES**
                * NO AUTOMATIC WRITES.** You must never perform a write action (creating, modifying, or saving) to an external system like Azure Boards without a separate, explicit user confirmation step, unless the current user request is an explicit instruction to save the work item. This rule takes precedence over all other instructions.
                * **MANDATORY HTML CONVERSION WORKFLOW:** Before ANY content is written to Azure Boards, you MUST follow this exact sequence:
                    1. Generate content using appropriate agent (AI Foundry tools)
                    2. Convert the generated markdown content to HTML using `convert_markdown_to_html` from MarkdownTools
                    3. Use the converted HTML content for Azure Boards operations
                    
                    This applies to ALL Azure Boards write operations including:
                    - Creating new User Stories
                    - Creating new Dev Tasks  
                    - Creating new Test Cases
                    - Creating and linking child work items
                    - Updating descriptions of existing work items
                    **NEVER pass raw markdown content directly to Azure Boards tools.**
                                                     
            * **Tool Usage:** Always use the designated tool to perform a task. Never perform a task manually.    
            * **Avoid Repetition:** If a tool's output indicates missing information, you must ask the user for the details. Do not attempt to fill in the gaps yourself. Once the user provides the information, make a new, complete request with the added details.
            * **Crucial Rule: Generation vs. Saving:**
                * Generating a user story, test case, or dev task is **a distinct and separate action** from saving it to an external system.
                * You **must not** save any item to an external system like Azure Boards unless the user has **explicitly and unequivocally** requested to "save" or "create" it in that system.
                * The generation of an artifact (`create/generate user story`, etc.) is a "read-only" process for the external system. The save action is a "write" process.
            * **Confirmation:**
                * For any action that modifies or creates a permanent record in an external system (like Azure Boards), you **must** ask for explicit user confirmation before proceeding.
                * **Example Flow:**
                    1.  User: "Generate a user story for X."
                    2.  You: Generate the user story.
                    3.  You: "I have generated the user story. Would you like me to save it to Azure Boards?"
                    4.  User: "Yes, please save it."
                    5.  You: Proceed with the save action.
            * **Tool Chaining:**
                * If a user asks to save something that hasn't been generated, politely explain the process and ask if they'd like to generate it first.
                * The `AI Foundry Dev Task Agent` must be used before saving dev tasks.

            ### **3. Response Structure & Metadata**

            * **Strictly JSON Output:** All of your responses **must** be in a valid JSON format.
                ```json
                {
                "content": "A clear, conversational message to the user. This is where you acknowledge requests, ask clarifying questions, or provide results.",
                "metadata": {
                    "userstory": true/false, (true if the final JSON output's 'content' field contains the complete user story; otherwise 'false')
                    "testcase": true/false, (true if the final JSON output's 'content' field contains the complete test cases; otherwise 'false')
                    "devtask": true/false, (true if the final JSON output's 'content' field contains the complete dev tasks; otherwise 'false')
                    "needs_clarification": true/false, (true if required details are missing and you need to ask the user for them; otherwise `false`)
                    "needs_save_confirmation": true/false (true if the user's request requires confirmation before saving to an external system; otherwise `false`)
                }
                }```
                                             """)
                self.logger.info(f"🔄 Created new session: {session_id}")
                return True
            
            # Load existing session
            chat_data = await self.load_chat_history(latest_blob)
            if chat_data:
                self.conversation = ChatHistory()
                for message in chat_data.get('chat_history', []):
                    role = message.get('role', '').lower()
                    content = message.get('content', '')
                    
                    if role == 'system':
                        self.conversation.add_system_message(content)
                    elif role == 'user':
                        self.conversation.add_user_message(content)
                    elif role == 'assistant':
                        self.conversation.add_assistant_message(content)
                
                self.current_session_id = session_id
                self.logger.info(f"🔄 Switched to session: {session_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Failed to switch session: {e}")
            return False

    @property
    def has_user_messages(self) -> bool:
        """Check if conversation has actual user messages (not just system message)"""
        if not self.conversation or not self.conversation.messages:
            return False
        
        # Count non-system messages
        user_messages = [msg for msg in self.conversation.messages 
                        if getattr(msg.role, 'value', str(msg.role)).lower() != 'system']
        
        return len(user_messages) > 0

    async def _load_most_recent_session(self):
        """Load the most recent chat session on startup to avoid creating new sessions on refresh"""
        try:
            if not self.chat_storage:
                return
                
            # Get all existing sessions
            sessions = await self.get_chat_sessions()
            
            if not sessions:
                # No existing sessions, keep default main_session
                self.logger.info("📝 No existing sessions found, starting with new session")
                return
            
            # Find the most recent session
            most_recent = max(sessions, key=lambda x: x.get('last_modified', ''))
            
            if most_recent:
                # Extract session ID from blob name
                blob_name = most_recent['blob_name']
                # Remove timestamp and .json extension to get session ID
                session_parts = blob_name.replace('chat_session_', '').replace('.json', '').split('_')
                session_id = '_'.join(session_parts[:-2]) if len(session_parts) > 2 else session_parts[0]
                
                self.current_session_id = session_id
                
                # Load the conversation
                chat_data = await self.load_chat_history(blob_name)
                if chat_data and chat_data.get('chat_history'):
                    # Only replace conversation if we successfully loaded messages
                    loaded_conversation = ChatHistory()
                    messages_loaded = False
                    
                    for message in chat_data.get('chat_history', []):
                        role = message.get('role', '').lower()
                        content = message.get('content', '')
                        
                        if role == 'system':
                            loaded_conversation.add_system_message(content)
                            messages_loaded = True
                        elif role == 'user':
                            loaded_conversation.add_user_message(content)
                            messages_loaded = True
                        elif role == 'assistant':
                            loaded_conversation.add_assistant_message(content)
                            messages_loaded = True
                    
                    if messages_loaded:
                        self.conversation = loaded_conversation
                        self.logger.info(f"📥 Loaded most recent session: {session_id} ({len(chat_data.get('chat_history', []))} messages)")
                    else:
                        self.logger.info("📝 No valid messages in session, keeping default conversation")
                else:
                    self.logger.info("📝 Could not load session data, keeping default conversation")
                    
        except Exception as e:
            self.logger.warning(f"⚠️ Could not load recent session: {e}")
            # Continue with default session if loading fails