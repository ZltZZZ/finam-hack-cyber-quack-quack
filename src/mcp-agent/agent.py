from typing import List, Dict, Optional
from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class OpenAIAgent:
    def __init__(self):
        self.app = MCPApp(name="trader_agent")
        self.agent: Optional[Agent] = None
        self.llm: Optional[OpenAIAugmentedLLM] = None
        self._initialized = False

    def create_agent(self):
        """Создает агента с инструкциями"""
        self.agent = Agent(
            name="trading_assistant",
            instruction='''You are an Finam Trader Assistant.
            Perform user request using available tools (You are connected to MCP server). 
            You can use ONLY available tools or your own mind for data. 
            ALWAYS Before placing or cancelling order get confirmation from user.
            Answer only on Russian.
            ''',
            server_names=["trader_tools"]
        )
        
    async def attach_llm(self):
        """Прикрепляет LLM к агенту"""
        if not self.agent:
            raise RuntimeError("Агент не создан")
            
        self.llm = await self.agent.attach_llm(OpenAIAugmentedLLM)
        self._initialized = True

    async def initialize(self):
        """Полная инициализация агента"""
        if self._initialized:
            return
            
        self.create_agent()
        await self.attach_llm()

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    async def generate_response(self, prompt: str) -> str:
        """Генерирует ответ на промпт"""
        if not self.llm:
            raise RuntimeError("LLM не инициализирован")
        return await self.llm.generate_str(prompt)
    
class MCPAgentManager:
    """Менеджер для управления MCP агентом"""
    
    def __init__(self):
        self._mcp_agent: Optional[OpenAIAgent] = None
        self._initialized = False
    
    async def initialize(self):
        """Однократная инициализация MCP агента"""
        if self._initialized:
            return
            
        self._mcp_agent = OpenAIAgent()
        
        # Правильное использование асинхронного контекстного менеджера
        self._mcp_app_context = self._mcp_agent.app.run()
        self._mcp_app = await self._mcp_app_context.__aenter__()
        
        self._mcp_agent.create_agent()
        
        # Правильный вызов - await напрямую на асинхронном контекстном менеджере
        self._agent_context = self._mcp_agent.agent
        await self._agent_context.__aenter__()
        
        # Прикрепляем LLM
        await self._mcp_agent.attach_llm()
        
        self._initialized = True
    
    async def cleanup(self):
        """Очистка ресурсов"""
        if self._initialized:
            await self._agent_context.__aexit__(None, None, None)
            await self._mcp_app_context.__aexit__(None, None, None)
            self._initialized = False
    
    @property
    def agent(self) -> OpenAIAgent:
        if not self._initialized:
            raise RuntimeError("MCP агент не инициализирован")
        return self._mcp_agent
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized


# Глобальный менеджер агента
agent_manager = MCPAgentManager()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)




class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate_str")
async def generate_str(prompt: PromptRequest) -> str:
    if not agent_manager.is_initialized:
        await agent_manager.initialize()

    result = await agent_manager.agent.llm.generate_str(prompt.prompt)

    logging.info(f"Result: {result}")

    return result


@app.get("/health")
async def health_check():
    return {"status": "ok"}

