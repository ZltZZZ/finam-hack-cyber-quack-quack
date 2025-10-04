#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Рендер интерактивных визуализаций из JSON-спеки:
- candlestick, line, bar, scatter, pie, heatmap, orderbook, table
- st.plotly_chart(..., width="stretch") — без deprecated use_container_width
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


#  Парсер блока VISUALIZE в тексте 

def parse_visualize_spec(text: str) -> Optional[Dict[str, Any]]:
    """Извлекает JSON после 'VISUALIZE:' (поддерживает ```json ... ``` и голый JSON)."""
    if not text:
        return None
    up = text.upper()
    pos = up.find("VISUALIZE:")
    if pos == -1:
        return None

    tail = text[pos + len("VISUALIZE:") :].strip()
    # вырежем fenced ```json
    if tail.startswith("```"):
        fence_end = tail.find("```", 3)
        if fence_end != -1:
            tail = tail[3:fence_end].strip()

    # попытаемся распарсить первый JSON-объект
    start = tail.find("{")
    if start == -1:
        return None
    depth, in_str, esc = 0, False, False
    end = None
    for i in range(start, len(tail)):
        ch = tail[i]
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
                end = i + 1
                break
    if end is None:
        return None
    try:
        return json.loads(tail[start:end])
    except Exception:
        return None


#  Рендеры 

def _height(options: Dict[str, Any] | None, default: int = 520) -> int:
    try:
        return int((options or {}).get("height", default))
    except Exception:
        return default

def _norm_ohlc_row(row: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(row)
    for k in ("open", "high", "low", "close"):
        v = out.get(k)
        if isinstance(v, dict) and "value" in v:
            v = v["value"]
        if isinstance(v, str):
            try:
                v = float(v.replace(",", "."))
            except Exception:
                pass
        out[k] = v
    return out

def _ensure_x(data: List[Dict[str, Any]], x_key: Optional[str]) -> str:
    """Если нет time и не задан x, создаём индексную ось."""
    if x_key:
        return x_key
    has_time = any("time" in d and d["time"] is not None for d in data)
    return "time" if has_time else "__idx"

def _to_df(data: List[Dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(data)
    if "__idx" not in df.columns:
        df["__idx"] = range(len(df))
    return df


def _render_candlestick(spec: Dict[str, Any]) -> None:
    data = [ _norm_ohlc_row(r) for r in (spec.get("data") or []) ]
    x_key = _ensure_x(data, spec.get("x"))
    df = _to_df(data)

    fig = go.Figure(data=[go.Candlestick(
        x=df[x_key],
        open=df[spec.get("open", "open")],
        high=df[spec.get("high", "high")],
        low =df[spec.get("low", "low")],
        close=df[spec.get("close", "close")],
        name="OHLC",
    )])
    fig.update_layout(
        title=spec.get("title") or "",
        xaxis_rangeslider_visible=False,
        height=_height(spec.get("options")),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    st.plotly_chart(fig, width="stretch")


def _render_line(spec: Dict[str, Any]) -> None:
    data = spec.get("data") or []
    x_key = _ensure_x(data, spec.get("x"))
    y_key = spec.get("y") or "value"
    df = _to_df(data)
    fig = px.line(df, x=x_key, y=y_key, title=spec.get("title") or "")
    fig.update_layout(height=_height(spec.get("options")), margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, width="stretch")


def _render_bar(spec: Dict[str, Any]) -> None:
    data = spec.get("data") or []
    x_key = _ensure_x(data, spec.get("x"))
    y_key = spec.get("y") or "value"
    df = _to_df(data)
    fig = px.bar(df, x=x_key, y=y_key, title=spec.get("title") or "")
    fig.update_layout(height=_height(spec.get("options")), margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, width="stretch")


def _render_scatter(spec: Dict[str, Any]) -> None:
    data = spec.get("data") or []
    x_key = _ensure_x(data, spec.get("x"))
    y_key = spec.get("y") or "value"
    df = _to_df(data)
    fig = px.scatter(df, x=x_key, y=y_key, title=spec.get("title") or "", hover_data=df.columns)
    fig.update_layout(height=_height(spec.get("options")), margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, width="stretch")


def _render_pie(spec: Dict[str, Any]) -> None:
    data = spec.get("data") or []
    names = spec.get("names") or spec.get("x") or "name"
    values = spec.get("values") or spec.get("y") or "value"
    df = _to_df(data)
    fig = px.pie(df, names=names, values=values, title=spec.get("title") or "")
    fig.update_layout(height=_height(spec.get("options")), margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, width="stretch")


def _render_heatmap(spec: Dict[str, Any]) -> None:
    z = spec.get("z") or []
    x = spec.get("x_labels") or None
    y = spec.get("y_labels") or None
    fig = go.Figure(data=go.Heatmap(z=z, x=x, y=y, colorbar=dict(title="")))
    fig.update_layout(title=spec.get("title") or "", height=_height(spec.get("options")),
                      margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, width="stretch")


def _render_orderbook(spec: Dict[str, Any]) -> None:
    bids: List[List[float]] = spec.get("bids") or []
    asks: List[List[float]] = spec.get("asks") or []
    # Превратим в DataFrame ради сортировки/подсветки
    bdf = pd.DataFrame(bids, columns=["price", "size"]).sort_values("price", ascending=False)
    adf = pd.DataFrame(asks, columns=["price", "size"]).sort_values("price", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=bdf["size"], y=bdf["price"], name="Bids", orientation="h"))
    fig.add_trace(go.Bar(x=adf["size"], y=adf["price"], name="Asks", orientation="h"))
    fig.update_layout(
        barmode="overlay",
        title=spec.get("title") or "",
        height=_height(spec.get("options")),
        margin=dict(l=10, r=10, t=40, b=10),
        yaxis_title="Price",
        xaxis_title="Size",
    )
    st.plotly_chart(fig, width="stretch")

    # Табличка для взаимодействия (сортировка/фильтры встроены в dataframe)
    st.subheader("Стакан (таблица)")
    two_col = pd.concat(
        {
            "Bids": bdf.reset_index(drop=True),
            "Asks": adf.reset_index(drop=True),
        },
        axis=1,
    )
    st.dataframe(two_col, use_container_width=True)


def _render_table(spec: Dict[str, Any]) -> None:
    data = spec.get("data") or []
    df = pd.DataFrame(data)
    st.subheader(spec.get("title") or "Таблица")
    st.dataframe(df, use_container_width=True)


def render_visualization(spec: Dict[str, Any]) -> None:
    """Главная точка входа."""
    if not isinstance(spec, dict):
        st.warning("Некорректная спецификация визуализации.")
        return

    vtype = (spec.get("type") or "").lower()
    if vtype in ("candlestick", "ohlc"):
        _render_candlestick(spec)
    elif vtype == "line":
        _render_line(spec)
    elif vtype == "bar":
        _render_bar(spec)
    elif vtype == "scatter":
        _render_scatter(spec)
    elif vtype == "pie":
        _render_pie(spec)
    elif vtype == "heatmap":
        _render_heatmap(spec)
    elif vtype == "orderbook":
        _render_orderbook(spec)
    elif vtype == "table":
        _render_table(spec)
    else:
        st.info(f"Пока не знаю тип '{vtype}'. Покажу сырой JSON.")
        st.code(json.dumps(spec, ensure_ascii=False, indent=2), language="json")
