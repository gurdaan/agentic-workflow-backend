#!/usr/bin/env python3
"""
Minimal AI Foundry Agent Test
"""

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import MessageRole
from azure.identity import DefaultAzureCredential

def test_agent(user_message):
    """Send message to AI Foundry agent and get response"""
    
    agents_client = AgentsClient(
        endpoint="https://agenticflowflow.services.ai.azure.com/api/projects/agenticflow",
        credential=DefaultAzureCredential()
    )
    
    with agents_client:
        # Get agent
        agent = agents_client.get_agent("asst_3xVRVj7AUWAzRJmNYII4TKJW")
        
        # Create thread and message
        thread = agents_client.threads.create()
        agents_client.messages.create(
            thread_id=thread.id,
            role=MessageRole.USER,
            content=user_message
        )
        
        # Run agent
        run = agents_client.runs.create_and_process(
            thread_id=thread.id, 
            agent_id=agent.id
        )
        
        # Get response
        messages = agents_client.messages.list(thread_id=thread.id)
        for msg in messages:
            if msg.text_messages and msg.role.lower() == "assistant":
                return msg.text_messages[-1].text.value
        
        return None

if __name__ == "__main__":
    response = test_agent("Create a user story for user authentication with MFA for project agentic-workflow")
    if response:
        print("🤖 Agent Response:")
        print("=" * 50)
        print(response)
    else:
        print("❌ No response received")