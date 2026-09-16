"""Microsoft Foundry Responses-protocol entrypoint."""

from __future__ import annotations

import asyncio
import os

from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import FoundryToolbox, ResponsesHostServer
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

from realestate_agent.agent import build_realestate_agent
from realestate_agent.config import Settings


async def main() -> None:
    load_dotenv(override=False)
    settings = Settings()
    settings.validate_hosted_requirements()
    credential = DefaultAzureCredential()
    toolbox = FoundryToolbox(
        credential,
        url=settings.toolbox_endpoint,
        name=settings.toolbox_name,
    )
    client = FoundryChatClient(
        project_endpoint=settings.foundry_project_endpoint,
        model=settings.azure_ai_model_deployment_name,
        credential=credential,
    )
    agent = build_realestate_agent(client=client, toolbox=toolbox)
    await ResponsesHostServer(agent).run_async()


if __name__ == "__main__":
    asyncio.run(main())
