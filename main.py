import asyncio

from mcp_agent.app import MCPApp
from mcp_agent.mcp.gen_client import gen_client
from mcp_agent.mcp.mcp_agent_client_session import MCPAgentClientSession
from mcp_agent.mcp.mcp_connection_manager import MCPConnectionManager

app = MCPApp(name="mcp_hello_world")


async def example_usage():
    async with app.run() as hello_world_app:
        context = hello_world_app.context
        logger = hello_world_app.logger

        logger.info("Hello, world!")
        logger.info("Current config:", data=context.config.model_dump())

        # Use an async context manager to connect to the fetch server
        # At the end of the block, the connection will be closed automatically
        async with gen_client(
            "Demo", server_registry=context.server_registry
        ) as demo_client:
            logger.info("Demo: Connected to server, calling list_tools...")
            result = await demo_client.list_tools()
            logger.info("Tools available:", data=result.model_dump())

            # Connect to the filesystem server using a persistent connection via connect/disconnect
            # This is useful when you need to make multiple requests to the same server

            connection_manager = MCPConnectionManager(context.server_registry)
            await connection_manager.__aenter__()

            try:
                demo_client = await connection_manager.get_server(
                    server_name="Demo",
                    client_session_factory=MCPAgentClientSession,
                )
                logger.info(
                    "Demo: Connected to server with persistent connection."
                )

                result = await demo_client.session.list_tools()
                logger.info("Demo: Tools available:", data=result.model_dump())

            finally:
                await connection_manager.disconnect_server(server_name="Demo")
                logger.info("Demo: Disconnected from server.")
                await connection_manager.__aexit__(None, None, None)


if __name__ == "__main__":
    asyncio.run(example_usage())