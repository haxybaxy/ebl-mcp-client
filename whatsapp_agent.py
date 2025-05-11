import asyncio
from fastapi import FastAPI, Request
from twilio.rest import Client
from dotenv import load_dotenv
import os
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

# Initialize MCP App
mcp_app = MCPApp(name="whatsapp_agent")

async def process_with_agent(message: str) -> str:
    async with mcp_app.run() as agent_app:
        context = agent_app.context
        logger = agent_app.logger

        monsieur = Agent(
            name="monsieur",
            instruction="""
            You are a helpful assistant that acts as a front desk worker for a hotel. please start your answer with "Hello Huzz" everytime
            """,
        )
        
        async with monsieur:
            llm = await monsieur.attach_llm(OpenAIAugmentedLLM)
            result = await llm.generate_str(message=message)
            return result

@app.post("/webhook")
async def webhook(request: Request):
    """
    Webhook endpoint to receive incoming WhatsApp messages and process them with the agent
    """
    form_data = await request.form()
    message_body = form_data.get('Body', '')
    from_number = form_data.get('From', '')
    
    # Process the message with the agent
    agent_response = await process_with_agent(message_body)
    
    # Send the response back via WhatsApp
    try:
        message = client.messages.create(
            body=agent_response,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=from_number
        )
        return {
            "status": "success",
            "message_sid": message.sid,
            "agent_response": agent_response
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 