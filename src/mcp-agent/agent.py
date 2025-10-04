from typing import List, Dict, Optional
from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate_str")
async def generate_str(prompt: PromptRequest) -> str:
    app = MCPApp(name="trader_agent")

    async with app.run() as mcp_agent_app:
        agent = Agent(
            name="security_scanner",
            instruction='''You are an AI Cybersecurity Specialist.
            Perform security analysis using available tools (You are connected to MCP server, so, choose tools).
            Tools can't be run as root user. 
            ''',
            server_names=["pentest_tools"]
        )

        async with agent:
            llm = await agent.attach_llm(
                OpenAIAugmentedLLM
            )
            llm.history = None
            result = await llm.generate_str(prompt, params=RequestParams(
                        temperature=0.1,
                        max_tokens=1000
                    ))

    return result


@app.get("/health")
async def health_check():
    return {"status": "ok"}

