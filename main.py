import asyncio

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
# from mcp_agent.mcp.mcp_agent_client_session import MCPAgentClientSession
# from mcp_agent.mcp.mcp_connection_manager import MCPConnectionManager

app = MCPApp(name="mcp_hello_world")


async def example_usage():
    async with app.run() as hello_world_app:
        context = hello_world_app.context
        logger = hello_world_app.logger

        logger.info("Hello, world!")
        logger.info("Current config:", data=context.config.model_dump())

        # Use an async context manager to connect to the fetch server
        # At the end of the block, the connection will be closed automatically
        monsieur = Agent(
            name="monsieur",
            instruction="""
            You are a helpful assistant that acts as a front desk worker for a hotel.
            """,
            server_names=["Demo"],
        )
        async with monsieur:
            logger.info("monsieur: Connected to server, calling list_tools...")
            result = await monsieur.list_tools()
            logger.info("Tools available:", data=result.model_dump())

            llm = await monsieur.attach_llm(OpenAIAugmentedLLM)
            result = await llm.generate_str(
                message="Can you create a new for a guest called Zaid Alsaheb with email zaid@gmail.com in room 101 who needs a new key, no need to assign a check in and check out date?",
            )
            logger.info(f"tickets: {result}")


        
if __name__ == "__main__":
    asyncio.run(example_usage())