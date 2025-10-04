import logging
from typing import List, Dict
from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from schemas import AgentConfig
import asyncio
from pythonjsonlogger import jsonlogger

# Этот логгер используется для общих сообщений agent.py
agent_logger = logging.getLogger(__name__)
agent_logger.setLevel(logging.INFO)
# Оставьте этот StreamHandler, чтобы видеть логи в консоли Docker
if not agent_logger.handlers:
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    agent_logger.addHandler(handler)


class QueueHandler(logging.Handler):
    def __init__(self, queue: asyncio.Queue):
        super().__init__()
        self.queue = queue
        # Форматируем сообщение здесь, чтобы оно попадало в очередь уже отформатированным
        self.setFormatter(jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s'))

    def emit(self, record):
        try:
            message = self.format(record)
            # Используем put_nowait, чтобы не блокировать логгер,
            # и чтобы сообщение сразу попадало в очередь
            self.queue.put_nowait(message)
        except Exception:
            self.handleError(record)


class GeminiAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.app = MCPApp(
            name="pentest_agent"
        )


    async def generate_report(self, prompt: str, log_queue: asyncio.Queue) -> Dict:
        # Получаем корневой логгер 'mcp_agent'
        mcp_agent_root_logger = logging.getLogger('mcp_agent')
        # Создаем обработчик очереди
        queue_handler = QueueHandler(log_queue)

        mcp_agent_root_logger.setLevel(logging.DEBUG)  # Убедитесь, что DEBUG логи включены
        mcp_agent_root_logger.addHandler(queue_handler)

        # Настройка логгера для Docker-контейнера
        container_name = "mcp-server"
        docker_logger = logging.getLogger(f"docker.{container_name}")
        docker_logger.setLevel(logging.DEBUG)  # Можно установить другой уровень
        docker_logger.addHandler(queue_handler)
        docker_logger.propagate = False  # Важно: отключаем распространение к родителям

        async def monitor_docker_logs():
            proc = await asyncio.create_subprocess_exec(
                "docker", "logs", "-f", container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            while True:
                stdout = await proc.stdout.readline()
                stderr = await proc.stderr.readline()

                if stdout:
                    docker_logger.info(f"[{container_name} stdout] {stdout.decode().strip()}")
                if stderr:
                    docker_logger.error(f"[{container_name} stderr] {stderr.decode().strip()}")

        log_monitor_task = asyncio.create_task(monitor_docker_logs())

        try:
            mcp_agent_root_logger.info("Starting security scan...")

            docker_logger.info("-------------------------------------------------------Тест docker логгера")

            async with self.app.run() as mcp_agent_app:
                self.agent = Agent(
                    name="security_scanner",
                    instruction='''You are an AI Cybersecurity Specialist.
                    Perform security analysis using available tools (You are connected to MCP server, so, choose tools).
                    Tools can't be run as root user. 
                    ''',
                    server_names=["pentest_tools"]
                )

                async with self.agent:
                    tools = await self.agent.list_tools()
                    mcp_agent_root_logger.info(f"Tools available: {tools}")

                    llm = await self.agent.attach_llm(
                        OpenAIAugmentedLLM
                    )
                    mcp_agent_root_logger.info("Generating report with LLM...")
                    result = await llm.generate_str(prompt)
                    mcp_agent_root_logger.info("Report generation completed. Cleaning up...")
                    return {"status": "completed", "report": result}

        except Exception as e:
            mcp_agent_root_logger.error(f"Generation failed: {str(e)}", exc_info=True)
            # mcp_agent_root_logger.error(f"Generation failed: {str(e)}") # Уже будет отформатировано
            return {"status": "failed", "error": str(e)}
        finally:
            # Важно: удалить обработчик после завершения сессии, чтобы избежать дублирования
            # и утечек памяти, если сессий много.
            mcp_agent_root_logger.removeHandler(queue_handler)
            queue_handler.close()
            log_monitor_task.cancel()  # Остановить мониторинг при завершении
            # Отправляем None в очередь, чтобы сигнализировать о завершении потока
            await log_queue.put(None)
            # logging.info(f"Log stream for session {session_id} closed.") # Это уже в session_manager