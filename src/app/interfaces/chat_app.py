#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, Optional, Tuple

import httpx
import streamlit as st

#  Импорт визуализаций 
try:
    from src.app.interfaces.viz import render_visualization  # стандартный путь
except Exception:
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    for p in [
        os.path.abspath(os.path.join(here, "..", "..")),      # /src/app
        os.path.abspath(os.path.join(here, "..", "..", "..")) # /src
    ]:
        if p not in sys.path:
            sys.path.insert(0, p)
    try:
        from src.app.interfaces.viz import render_visualization  # type: ignore
    except Exception:
        from viz import render_visualization  # type: ignore

DEFAULT_MCP_AGENT_URL = os.environ.get("MCP_AGENT_URL", "http://mcp-agent:8003/generate_str")

# HELP

def build_system_prompt() -> str:
    """Системные правила для модели. Важное: всегда присылать VISUALIZE для графиков/таблиц."""
    return (
        "Ты — AI-ассистент трейдера. Отвечай кратко и по делу, на русском языке.\n\n"
        "Правила визуализаций:\n"
        "1) Если ответ подразумевает график или таблицу, ВСЕГДА добавляй в конце сообщения блок:\n"
        "VISUALIZE:\n"
        "{\n"
        '  "type": "<candlestick|line|bar|scatter|pie|heatmap|orderbook|table>",\n'
        '  "title": "Заголовок",\n'
        '  "data": [ { ... } ],\n'
        '  "x": "имя_поля_по_X",\n'
        '  "y": "имя_поля_по_Y",\n'
        '  "open": "open", "high": "high", "low": "low", "close": "close",\n'
        '  "options": { "height": 520 }\n'
        "}\n"
        "2) Для свечных данных присылай ПЛОСКИЕ числовые поля (без вложенных {\"value\":...}).\n"
        "3) Для стакана используй: bids=[[price,size],...], asks=[[price,size],...].\n"
        "4) Данные должны быть самодостаточными (фронт не делает доп. запросов).\n"
        "5) Если нужны реальные данные — сперва вызови инструмент (viz_candles, viz_orderbook, viz_latest_trades).\n"
        "   Если пользователь не указал биржу — используй mic='MISX' для тикеров MOEX.\n"
        "   При ошибке инструмента верни её детали пользователю (код/сообщение).\n"
    )

def _extract_text_from_response(resp: httpx.Response) -> str:
    """Достаём текст ассистента из ответа mcp-agent (под разные форматы)."""
    try:
        data = resp.json()
    except Exception:
        return resp.text
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        for k in ("result", "message", "content", "text", "output"):
            v = data.get(k)
            if isinstance(v, str):
                return v
        return json.dumps(data, ensure_ascii=False, indent=2)
    return str(data)

def _find_first_json_object(text: str) -> Tuple[Optional[int], Optional[int]]:
    """Ищем первый СБАЛАНСИРОВАННЫЙ JSON-объект { ... } и возвращаем (start, end)."""
    if not text:
        return None, None
    start = text.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return start, i + 1
        start = text.find("{", start + 1)
    return None, None

def _extract_visualize_block(text: str) -> Optional[Dict[str, Any]]:
    """Достаём ПЕРВЫЙ JSON после 'VISUALIZE:' (без учёта регистра)."""
    if not text:
        return None
    pos = text.upper().find("VISUALIZE:")
    if pos == -1:
        return None
    tail = text[pos + len("VISUALIZE:") :]
    s, e = _find_first_json_object(tail)
    if s is None or e is None:
        return None
    try:
        return json.loads(tail[s:e])
    except Exception:
        return None

def _extract_any_json_spec(text: str) -> Optional[Dict[str, Any]]:
    """Фолбэк: достаём первый JSON-объект из текста (если нет VISUALIZE)."""
    s, e = _find_first_json_object(text or "")
    if s is None or e is None:
        return None
    try:
        return json.loads(text[s:e])
    except Exception:
        return None

def _strip_visualize_json(text: str) -> str:
    """Удаляем из текста JSON, следующий сразу за 'VISUALIZE:'."""
    if not text:
        return text
    pos = text.upper().find("VISUALIZE:")
    if pos == -1:
        return text
    head, tail = text[:pos], text[pos + len("VISUALIZE:") :]
    s, e = _find_first_json_object(tail)
    if s is None or e is None:
        return text
    # выкидываем 'VISUALIZE:' и сам JSON
    return (head + tail[:s] + tail[e:]).replace("VISUALIZE:", "").strip()

def _strip_first_json(text: str) -> str:
    """Удаляем первый JSON-объект из текста (для фолбэка)."""
    s, e = _find_first_json_object(text or "")
    if s is None or e is None:
        return text
    return (text[:s] + text[e:]).strip()

def _normalize_visual_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Приводим спеку к формату, понятному рендерам:
    - Свечи: строки/{"value":"…"} → float; если нет time — x='__idx'.
    """
    if not isinstance(spec, dict):
        return spec
    t = (spec.get("type") or "").lower()
    if t in ("candlestick", "ohlc") and isinstance(spec.get("data"), list):
        have_time = False
        for idx, row in enumerate(spec["data"]):
            # извлечь числовые OHLC
            for k in ("open", "high", "low", "close"):
                v = row.get(k)
                if isinstance(v, dict) and "value" in v:
                    v = v["value"]
                if isinstance(v, str):
                    try:
                        v = float(v.replace(",", "."))
                    except Exception:
                        pass
                row[k] = v
            if row.get("time") is not None:
                have_time = True
            else:
                row["__idx"] = idx
        if not have_time:
            spec["x"] = spec.get("x") or "__idx"
    return spec

def _parse_or_extract_visual_spec(text: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Универсальный парсер визуализаций:
    1) Пробуем ПЕРВЫЙ JSON после 'VISUALIZE:'.
    2) Если нет — берём первый «голый JSON».
    Возвращаем (display_text, viz_spec).
    """
    spec = _extract_visualize_block(text)
    if spec:
        return _strip_visualize_json(text), _normalize_visual_spec(spec)

    cand = _extract_any_json_spec(text)
    if isinstance(cand, dict) and cand.get("type"):
        return _strip_first_json(text), _normalize_visual_spec(cand)

    return text, None



async def main() -> None:
    st.set_page_config(page_title="AI Трейдер (Finam)", page_icon="🤖", layout="wide")
    st.title("🤖 AI Ассистент Трейдера")
    st.caption("Интерактивные графики и таблицы прямо в чате (Plotly + Streamlit).")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Настройки")
        mcp_url = st.text_input(
            "MCP Agent URL",
            value=DEFAULT_MCP_AGENT_URL,
            help="Эндпоинт генерации текста (по умолчанию mcp-agent:8003/generate_str)",
        )
        use_system_prompt = st.checkbox(
            "Добавлять системный промпт",
            value=True,
            help="Включает правило про ОБЯЗАТЕЛЬНЫЙ VISUALIZE для графиков/таблиц",
        )
        st.markdown("---")
        if st.button("🗑️ Очистить историю"):
            st.session_state.messages = []
            st.rerun()
        st.markdown("### 💡 Примеры:")
        st.markdown(
            "- Нарисуй свечной график **SBER** за 2 месяца (верни VISUALIZE).\n"
            "- Покажи стакан **GAZP** (depth=15) — VISUALIZE orderbook.\n"
            "- Таблицей последние сделки **YNDX** — VISUALIZE table."
        )

    # История
    if "messages" not in st.session_state:
        st.session_state.messages = []  # элементы: {"role": "...", "content": str, "viz_spec"?: dict}

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("viz_spec"):
                render_visualization(msg["viz_spec"])
            else:
                try:
                    _, spec = _parse_or_extract_visual_spec(msg["content"])
                    if spec:
                        render_visualization(spec)
                except Exception:
                    pass

    # Ввод пользователя
    if user_text := st.chat_input("Напишите ваш вопрос…"):
        disp_user, user_spec = _parse_or_extract_visual_spec(user_text)
        st.session_state.messages.append(
            {"role": "user", "content": disp_user, **({"viz_spec": user_spec} if user_spec else {})}
        )
        with st.chat_message("user"):
            st.markdown(disp_user)
            if user_spec:
                render_visualization(user_spec)

        # Итоговый промпт → MCP Agent
        final_prompt = user_text
        if use_system_prompt:
            final_prompt = f"{build_system_prompt().strip()}\n\nПОЛЬЗОВАТЕЛЬ:\n{user_text}"

        with st.chat_message("assistant"), st.spinner("Думаю…"):
            try:
                async with httpx.AsyncClient(timeout=180) as client:
                    resp = await client.post(mcp_url, json={"prompt": final_prompt})
                    resp.raise_for_status()
                assistant_text = _extract_text_from_response(resp)

                display_text, viz_spec = _parse_or_extract_visual_spec(assistant_text)
                st.markdown(display_text)
                if viz_spec:
                    render_visualization(viz_spec)

                st.session_state.messages.append(
                    {"role": "assistant", "content": display_text, **({"viz_spec": viz_spec} if viz_spec else {})}
                )

            except httpx.HTTPStatusError as e:
                msg = f"HTTP {e.response.status_code} от MCP: {e.response.text}"
                st.error(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
            except httpx.RequestError as e:
                msg = f"Сетевая ошибка до MCP: {e}"
                st.error(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
            except Exception as e:
                msg = f"Неожиданная ошибка: {e!r}"
                st.error(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})


if __name__ == "__main__":
    asyncio.run(main())
