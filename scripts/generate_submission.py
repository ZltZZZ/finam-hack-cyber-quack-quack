#!/usr/bin/env python3
"""
Скрипт для генерации submission.csv на основе test.csv
с мониторингом Docker контейнеров в реальном времени и перезагрузкой каждые 15 запросов.
"""

import csv
import asyncio
import json
import time
import threading
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import re

import click
import httpx
import docker
from tqdm import tqdm

# Глобальные переменные для хранения последнего запроса
last_method = ""
last_url = ""
monitoring_active = True
request_counter = 0

def clean_url(url: str) -> str:
    """Очищает URL от префикса https://api.finam.ru"""
    if url.startswith("https://api.finam.ru"):
        return url.replace("https://api.finam.ru", "")
    return url

class LogMonitor:
    """Мониторинг логов контейнеров в реальном времени"""
    
    def __init__(self):
        self.client = docker.from_env()
        self.requests_log: List[Dict[str, Any]] = []
        
    def monitor_mcp_server_logs(self, container_name: str = "mcp-server2"):
        """Мониторинг логов MCP сервера в отдельном потоке"""
        global last_method, last_url, monitoring_active
        
        try:
            container = self.client.containers.get(container_name)
            print(f"🔍 Мониторинг логов контейнера: {container_name}")
            
            # Мониторинг в реальном времени
            for line in container.logs(stream=True, follow=True):
                if not monitoring_active:
                    break
                    
                line = line.decode('utf-8').strip()
                self._process_log_line(line)
                
        except docker.errors.NotFound:
            print(f"❌ Контейнер {container_name} не найден")
        except Exception as e:
            print(f"❌ Ошибка мониторинга: {e}")
            
    def _process_log_line(self, line: str):
        """Обработка строки лога"""
        global last_method, last_url
        
        if "MAKING REQUEST:" in line:
            print(f"📡 НАЙДЕН ЗАПРОС: {line}")
            
            # Извлекаем метод и URL
            match = re.search(r"MAKING REQUEST: (\w+) (https?://[^\s]+)", line)
            if match:
                original_url = match.group(2)
                cleaned_url = clean_url(original_url)
                
                request_data = {
                    'timestamp': datetime.now().isoformat(),
                    'method': match.group(1),
                    'url': cleaned_url,
                    'original_url': original_url,
                    'full_log': line
                }
                self.requests_log.append(request_data)
                
                # Обновляем глобальные переменные
                last_method = request_data['method']
                last_url = request_data['url']  # Сохраняем очищенный URL
                print(f"🎯 Метод: {last_method}, URL: {last_url}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Получение собранных метрик"""
        method_counts = {}
        for req in self.requests_log:
            method_counts[req['method']] = method_counts.get(req['method'], 0) + 1
            
        return {
            'total_requests': len(self.requests_log),
            'method_counts': method_counts,
            'requests': self.requests_log
        }

class DockerManager:
    """Управление Docker контейнеров"""
    
    def __init__(self):
        self.client = docker.from_env()
        
    def start_containers(self):
        """Запуск контейнеров через docker-compose"""
        import subprocess
        try:
            # Пробуем разные варианты команды
            commands = [
                ["docker", "compose", "up", "-d"],
                ["docker-compose", "up", "-d"]
            ]
            
            for cmd in commands:
                try:
                    result = subprocess.run(
                        cmd,
                        cwd=Path(__file__).parent,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    if result.returncode == 0:
                        print("✅ Контейнеры успешно запущены")
                        return True
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            
            print("❌ Не удалось запустить контейнеры")
            return False
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False
            
    def stop_containers(self):
        """Остановка контейнеров"""
        import subprocess
        try:
            commands = [
                ["docker", "compose", "down"],
                ["docker-compose", "down"]
            ]
            
            for cmd in commands:
                try:
                    subprocess.run(cmd, cwd=Path(__file__).parent, timeout=30)
                    break
                except FileNotFoundError:
                    continue
                    
            print("✅ Контейнеры остановлены")
        except Exception as e:
            print(f"⚠️ Предупреждение при остановке: {e}")
    
    def restart_containers(self):
        """Перезапуск контейнеров"""
        print("🔄 Перезапуск контейнеров...")
        self.stop_containers()
        time.sleep(5)  # Пауза перед запуском
        success = self.start_containers()
        if success:
            print("⏳ Ожидание запуска сервисов после перезагрузки (10 секунд)...")
            time.sleep(10)
        return success

class AIClient:
    """Клиент для взаимодействия с AI агентом"""
    
    def __init__(self, base_url: str = "http://localhost:8003"):
        self.base_url = base_url
        
    async def ask_question(self, question: str, uid: str):
        """Отправка вопроса AI агенту"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/generate_str",
                    json={"prompt": question}
                )
                print(f"📨 Ответ от AI агента для {uid}: {response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка запроса к AI агенту: {e}")

async def process_questions(
    test_questions: List[Dict[str, str]],
    output_file: Path,
    docker_manager: DockerManager,
    log_monitor: LogMonitor
):
    """Обработка вопросов с перезагрузкой контейнеров каждые 15 запросов"""
    
    global request_counter, monitoring_active
    
    ai_client = AIClient()
    results = []
    
    # Обрабатываем вопросы с перезагрузкой каждые 15 запросов
    for i, item in enumerate(tqdm(test_questions, desc="Обработка вопросов")):
        try:
            # Проверяем, не пора ли перезагрузить контейнеры
            if i > 0 and i % 15 == 0:
                print(f"\n🔄 Достигнуто {i} запросов, перезагружаем контейнеры...")
                
                # Останавливаем мониторинг
                monitoring_active = False
                time.sleep(2)
                
                # Перезагружаем контейнеры
                if not docker_manager.restart_containers():
                    print("❌ Не удалось перезагрузить контейнеры, продолжаем...")
                
                # Перезапускаем мониторинг
                monitoring_active = True
                monitoring_thread = start_log_monitoring(log_monitor)
                time.sleep(3)
                
                print("✅ Контейнеры перезагружены, продолжаем обработку...")
            
            # Отправляем вопрос AI агенту
            await ai_client.ask_question(
                question=item["question"],
                uid=item["uid"]
            )
            
            # Увеличиваем счетчик запросов
            request_counter += 1
            
            # Используем последние зафиксированные метод и URL (уже очищенный)
            current_method = last_method if last_method else "GET"
            current_url = last_url if last_url else ""
            
            results.append({
                "uid": item["uid"],
                "type": current_method,
                "request": current_url
            })
            
            print(f"✅ Обработан вопрос {item['uid']} ({i+1}/{len(test_questions)}): {current_method} {current_url}")
            
            # Небольшая пауза между запросами
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"❌ Ошибка обработки вопроса {item['uid']}: {e}")
            results.append({
                "uid": item["uid"],
                "type": "error",
                "request": ""
            })
    
    return results

def start_log_monitoring(log_monitor: LogMonitor):
    """Запуск мониторинга логов в отдельном потоке"""
    def monitoring_thread():
        log_monitor.monitor_mcp_server_logs()
    
    thread = threading.Thread(target=monitoring_thread, daemon=True)
    thread.start()
    return thread

@click.command()
@click.option(
    "--test-file",
    type=click.Path(exists=True, path_type=Path),
    default="../data/processed/test.csv",
    help="Путь к test.csv",
)
@click.option(
    "--output-file", 
    type=click.Path(path_type=Path),
    default="submission.csv",
    help="Путь к submission.csv",
)
@click.option(
    "--keep-containers",
    is_flag=True,
    help="Не останавливать контейнеры после завершения",
)
@click.option(
    "--restart-interval",
    type=int,
    default=15,
    help="Количество запросов между перезагрузками контейнеров",
)
def main(test_file: Path, output_file: Path, keep_containers: bool, restart_interval: int) -> None:
    """Генерация submission.csv с мониторингом Docker контейнеров и перезагрузкой"""
    global monitoring_active
    
    # Инициализация менеджеров
    docker_manager = DockerManager()
    log_monitor = LogMonitor()
    
    try:
        # Запуск контейнеров
        click.echo("🚀 Запуск Docker контейнеров...")
        if not docker_manager.start_containers():
            click.echo("❌ Не удалось запустить контейнеры")
            return
            
        # Ждем запуска сервисов
        click.echo("⏳ Ожидание запуска сервисов (15 секунд)...")
        time.sleep(15)
        
        # Запуск мониторинга логов в отдельном потоке
        click.echo("🔍 Запуск мониторинга логов...")
        monitoring_thread = start_log_monitoring(log_monitor)
        
        # Даем время на запуск мониторинга
        time.sleep(3)
        
        # Чтение тестовых вопросов
        click.echo(f"📖 Чтение {test_file}...")
        test_questions = []
        try:
            with open(test_file, encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    test_questions.append({
                        "uid": row["uid"], 
                        "question": row["question"]
                    })
            click.echo(f"✅ Найдено {len(test_questions)} вопросов")
        except Exception as e:
            click.echo(f"❌ Ошибка чтения файла: {e}")
            return
        
        # Обработка вопросов с перезагрузкой
        click.echo(f"\n🤖 Запуск обработки вопросов с перезагрузкой каждые {restart_interval} запросов...")
        
        results = asyncio.run(process_questions(test_questions, output_file, docker_manager, log_monitor))
        
        # Сохранение результатов
        click.echo(f"💾 Сохранение результатов в {output_file}...")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["uid", "type", "request"], delimiter=";")
            writer.writeheader()
            writer.writerows(results)
        
        # Вывод метрик
        metrics = log_monitor.get_metrics()
        click.echo(f"\n📊 Собранные метрики API вызовов:")
        click.echo(f"   Всего запросов: {metrics['total_requests']}")
        for method, count in metrics['method_counts'].items():
            click.echo(f"   {method}: {count}")
        
        # Статистика по типам ответов
        type_counts = {}
        for r in results:
            type_counts[r["type"]] = type_counts.get(r["type"], 0) + 1
        
        click.echo(f"\n📈 Статистика по типам ответов:")
        for method, count in sorted(type_counts.items()):
            click.echo(f"   {method}: {count}")
            
        # Сохранение детальных метрик
        metrics_file = output_file.parent / "api_metrics.json"
        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        click.echo(f"📄 Детальные метрики сохранены в {metrics_file}")
        
        click.echo(f"✅ Готово! Создано {len(results)} записей в {output_file}")
        
    except KeyboardInterrupt:
        click.echo("\n🛑 Прерывание пользователем")
    except Exception as e:
        click.echo(f"❌ Критическая ошибка: {e}")
    finally:
        # Остановка мониторинга
        monitoring_active = False
        
        # Остановка контейнеров если не указано иное
        if not keep_containers:
            click.echo("\n🛑 Остановка контейнеров...")
            docker_manager.stop_containers()

if __name__ == "__main__":
    main()