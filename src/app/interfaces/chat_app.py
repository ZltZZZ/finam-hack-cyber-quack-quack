#!/usr/bin/env python3
"""
Streamlit веб-интерфейс для AI ассистента трейдера
"""

import asyncio
import json

import httpx
import streamlit as st
from typing import Optional
from contextlib import asynccontextmanager


async def main() -> None:
    """Главная функция Streamlit приложения"""
    st.set_page_config(
        page_title="AI Трейдер (Finam)", 
        page_icon="🤖", 
        layout="wide"
    )

    # Заголовок
    st.title("🤖 AI Ассистент Трейдера")
    st.caption("Интеллектуальный помощник для работы с Finam TradeAPI")

    # Sidebar с настройками
    with st.sidebar:
        st.header("⚙️ Настройки")

        # Finam API настройки
        with st.expander("🔑 Finam API", expanded=False):
            api_token = st.text_input(
                "Access Token",
                type="password",
                help="Токен доступа к Finam TradeAPI (или используйте FINAM_ACCESS_TOKEN)",
            )
            api_base_url = st.text_input(
                "API Base URL", 
                value="https://api.finam.ru", 
                help="Базовый URL API"
            )

        account_id = st.text_input("ID счета", value="", help="Оставьте пустым если не требуется")

        # Статус MCP агента
        st.markdown("---")
        st.subheader("🔧 Статус системы")

        if st.button("🗑️ Очистить историю"):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")
        st.markdown("### 💡 Примеры вопросов:")
        st.markdown("""
        - Какая цена Сбербанка?
        - Покажи мой портфель
        - Что в стакане по Газпрому?
        - Покажи свечи YNDX за последние дни
        - Какие у меня активные ордера?
        - Детали моей сессии
        """)

    # Инициализация состояния чата
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Отображение истории сообщений
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Обработка пользовательского ввода
    if prompt := st.chat_input("Напишите ваш вопрос..."):
        # Добавляем сообщение пользователя
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Получаем ответ от агента
        with st.chat_message("assistant"), st.spinner("Думаю..."):
            try:
                async with httpx.AsyncClient() as client:
                    payload = {
                        "prompt": prompt
                    }
                    response = await client.post(
                        f"http://mcp-agent:8003/generate_str",
                        json=payload,
                        timeout=2*60*60
                    )
                    response.raise_for_status()
                    print(response.json())
                    st.markdown(response.json())

                # Сохраняем сообщение ассистента
                st.session_state.messages.append({"role": "assistant", "content": response.json()})
                
            except Exception as e:
                error_msg = f"❌ Ошибка при получении ответа: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})


if __name__ == "__main__":
    asyncio.run(main())