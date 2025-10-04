from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from .common import DecimalValue, Side, TimeFrame, OrderBookAction, Interval
from .orders import OrderState
from .accounts import AccountTrade
from .marketdata import Quote, Bar, Trade

class OrderTradeAction(str, Enum):
    """Доступные действия для подписки."""
    ACTION_SUBSCRIBE = "ACTION_SUBSCRIBE"
    ACTION_UNSUBSCRIBE = "ACTION_UNSUBSCRIBE"

class OrderTradeDataType(str, Enum):
    """Тип подписки."""
    DATA_TYPE_ALL = "DATA_TYPE_ALL"
    DATA_TYPE_ORDERS = "DATA_TYPE_ORDERS"
    DATA_TYPE_TRADES = "DATA_TYPE_TRADES"

class OrderTradeRequest(BaseModel):
    """Запрос подписки на собственные заявки и сделки."""
    action: OrderTradeAction = Field(description="Изменение статуса подписки: подписка/отписка")
    data_type: OrderTradeDataType = Field(description="Подписка только на заявки/ордера или на все сразу")
    account_id: str = Field(description="Идентификатор аккаунта")

class StreamError(BaseModel):
    """Ошибка стрим сервиса."""
    code: int = Field(description="Код ошибки")
    description: str = Field(description="Описание ошибки")

class SubscribeQuoteResponse(BaseModel):
    """Котировки по инструменту (стрим)."""
    quote: List[Quote] = Field(description="Список котировок")
    error: Optional[StreamError] = Field(None, description="Ошибка стрим сервиса")

class StreamOrderBookRow(BaseModel):
    """Уровень стакана для стрима."""
    price: DecimalValue = Field(description="Цена")
    sell_size: Optional[DecimalValue] = Field(None, description="Размер на продажу")
    buy_size: Optional[DecimalValue] = Field(None, description="Размер на покупку")
    action: OrderBookAction = Field(description="Команда")
    mpid: str = Field(description="Идентификатор участника рынка")
    timestamp: str = Field(description="Метка времени")

class StreamOrderBook(BaseModel):
    """Стакан по инструменту (стрим)."""
    symbol: str = Field(description="Символ инструмента")
    rows: List[StreamOrderBookRow] = Field(description="Уровни стакана")

class SubscribeOrderBookResponse(BaseModel):
    """Стакан по инструменту (стрим)."""
    order_book: List[StreamOrderBook] = Field(description="Список стакан стримов")

class SubscribeBarsResponse(BaseModel):
    """Агрегированные свечи (стрим)."""
    symbol: str = Field(description="Символ инструмента")
    bars: List[Bar] = Field(description="Агрегированная свеча")

class SubscribeLatestTradesResponse(BaseModel):
    """Последние сделки по инструменту (стрим)."""
    symbol: str = Field(description="Символ инструмента")
    trades: List[Trade] = Field(description="Список сделок")

class OrderTradeResponse(BaseModel):
    """Собственные заявки и сделки (стрим)."""
    orders: List[OrderState] = Field(description="Заявки")
    trades: List[AccountTrade] = Field(description="Сделки")

class SubscribeQuoteRequest(BaseModel):
    """Запрос подписки на котировки по инструменту."""
    symbols: List[str] = Field(description="Список символов инструментов")

class SubscribeOrderBookRequest(BaseModel):
    """Запрос подписки на стакан по инструменту."""
    symbol: str = Field(description="Символ инструмента")

class SubscribeBarsRequest(BaseModel):
    """Запрос подписки на агрегированные свечи."""
    symbol: str = Field(description="Символ инструмента")
    timeframe: TimeFrame = Field(description="Необходимый таймфрейм")

class SubscribeLatestTradesRequest(BaseModel):
    """Запрос подписки на последние сделки по инструменту."""
    symbol: str = Field(description="Символ инструмента")