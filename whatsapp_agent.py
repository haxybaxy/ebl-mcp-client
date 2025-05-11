import asyncio
from fastapi import FastAPI, Request
from twilio.rest import Client
from dotenv import load_dotenv
import os
from typing import Optional, Dict
from contextlib import AsyncExitStack
from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

# Load environment variables
load_dotenv()

app = FastAPI(title="WhatsApp Agent Integration")

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

class WhatsAppSession:
    def __init__(self, phone_number: str):
        self.phone_number = phone_number
        self.app: Optional[MCPApp] = None
        self.agent: Optional[Agent] = None
        self.llm = None
        self.exit_stack = AsyncExitStack()
        self.message_count = 0

    async def initialize(self):
        """Initialize the session with MCP app and agent"""
        self.app = MCPApp(name="whatsapp_agent")
        await self.app.initialize()

        self.agent = Agent(
            name="monsieur",
            instruction="""
            You are a helpful assistant that acts as a front desk worker for a hotel. 
            Please start your answer with "Hello Huzz" everytime.
            If you need more information from the user, please use ask the user for human feedback, especially if it needs a room number.
            """,
            server_names=["Demo"]
        )
        await self.agent.initialize()
        self.llm = await self.agent.attach_llm(OpenAIAugmentedLLM)

    async def process_message(self, message: str) -> str:
        """Process a message and return the response"""
        self.message_count += 1
        response = await self.llm.generate_str(message=message)
        return response

    async def cleanup(self):
        """Clean up resources"""
        if self.agent:
            await self.agent.cleanup()
        if self.app:
            await self.app.cleanup()
        await self.exit_stack.aclose()

# Store active sessions
active_sessions: Dict[str, WhatsAppSession] = {}

async def get_or_create_session(phone_number: str) -> WhatsAppSession:
    """Get an existing session or create a new one"""
    if phone_number not in active_sessions:
        session = WhatsAppSession(phone_number)
        await session.initialize()
        active_sessions[phone_number] = session
    return active_sessions[phone_number]

@app.post("/webhook")
async def webhook(request: Request):
    """Webhook endpoint to receive incoming WhatsApp messages"""
    form_data = await request.form()
    message_body = form_data.get('Body', '')
    from_number = form_data.get('From', '')
    
    try:
        # Get or create session
        session = await get_or_create_session(from_number)
        
        # Process message
        response = await session.process_message(message_body)
        
        # Send response via WhatsApp
        message = client.messages.create(
            body=response,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=from_number
        )
        
        # Clean up session after 4 messages
        if session.message_count >= 4:
            await session.cleanup()
            del active_sessions[from_number]
        
        return {
            "status": "success",
            "message_sid": message.sid,
            "agent_response": response
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up all active sessions when the application shuts down"""
    for session in active_sessions.values():
        await session.cleanup()
    active_sessions.clear()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 