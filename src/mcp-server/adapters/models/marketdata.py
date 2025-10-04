from pydantic import BaseModel, Field
from typing import List, Optional
from .common import DecimalValue, Side, TimeFrame, Interval, OrderBookAction

class Bar(BaseModel):
    """Структура агрегированной свечи."""
    timestamp: str = Field(description="Метка времени")
    open: DecimalValue = Field(description="Цена открытия свечи")
    high: DecimalValue = Field(description="Максимальная цена свечи")
    low: DecimalValue = Field(description="Минимальная цена свечи")
    close: DecimalValue = Field(description="Цена закрытия свечи")
    volume: DecimalValue = Field(description="Объём торгов за свечу в шт.")

class BarsResponse(BaseModel):
    """Структура ответа для получения исторических данных по инструменту."""
    symbol: str = Field(description="Символ инструмента")
    bars: List[Bar] = Field(description="Агрегированная свеча")

class QuoteOption(BaseModel):
    """Информация об опционе в котировке."""
    open_interest: Optional[DecimalValue] = Field(None, description="Открытый интерес")
    implied_volatility: Optional[DecimalValue] = Field(None, description="Подразумеваемая волатильность")
    theoretical_price: Optional[DecimalValue] = Field(None, description="Теоретическая цена")
    delta: Optional[DecimalValue] = Field(None, description="Delta")
    gamma: Optional[DecimalValue] = Field(None, description="Gamma")
    theta: Optional[DecimalValue] = Field(None, description="Theta")
    vega: Optional[DecimalValue] = Field(None, description="Vega")
    rho: Optional[DecimalValue] = Field(None, description="Rho")

class Quote(BaseModel):
    """Структура котировки."""
    symbol: str = Field(description="Символ инструмента")
    timestamp: str = Field(description="Метка времени")
    ask: DecimalValue = Field(description="Аск. 0 при отсутствии активного аска")
    ask_size: DecimalValue = Field(description="Размер аска")
    bid: DecimalValue = Field(description="Бид. 0 при отсутствии активного бида")
    bid_size: DecimalValue = Field(description="Размер бида")
    last: DecimalValue = Field(description="Цена последней сделки")
    last_size: DecimalValue = Field(description="Размер последней сделки")
    volume: DecimalValue = Field(description="Дневной объем сделок")
    turnover: DecimalValue = Field(description="Дневной оборот сделок")
    open: DecimalValue = Field(description="Цена открытия. Дневная")
    high: DecimalValue = Field(description="Максимальная цена. Дневная")
    low: DecimalValue = Field(description="Минимальная цена. Дневная")
    close: DecimalValue = Field(description="Цена закрытия. Дневная")
    change: DecimalValue = Field(description="Изменение цены (last минус close)")
    option: Optional[QuoteOption] = Field(None, description="Информация об опционе")

class LastQuoteResponse(BaseModel):
    """Структура ответа для получения последней котировки по инструменту."""
    symbol: str = Field(description="Символ инструмента")
    quote: Quote = Field(description="Цена последней сделки")

class Trade(BaseModel):
    """Структура сделки."""
    trade_id: str = Field(description="Идентификатор сделки, отправленный биржей")
    mpid: str = Field(description="Идентификатор участника рынка")
    timestamp: str = Field(description="Метка времени")
    price: DecimalValue = Field(description="Цена сделки")
    size: DecimalValue = Field(description="Размер сделки")
    side: Side = Field(description="Сторона сделки (buy или sell)")

class LatestTradesResponse(BaseModel):
    """Структура ответа для получения списка последних сделок по инструменту."""
    symbol: str = Field(description="Символ инструмента")
    trades: List[Trade] = Field(description="Список последних сделок")

class OrderBookRow(BaseModel):
    """Структура уровня стакана."""
    price: DecimalValue = Field(description="Цена уровня")
    sell_size: Optional[DecimalValue] = Field(None, description="Размер продажи")
    buy_size: Optional[DecimalValue] = Field(None, description="Размер покупки")
    action: OrderBookAction = Field(description="Действие")
    mpid: str = Field(description="Идентификатор участника рынка")
    timestamp: str = Field(description="Метка времени")

class OrderBook(BaseModel):
    """Структура стакана."""
    rows: List[OrderBookRow] = Field(description="Уровни стакана")

class OrderBookResponse(BaseModel):
    """Структура ответа для получения текущего стакана по инструменту."""
    symbol: str = Field(description="Символ инструмента")
    orderbook: OrderBook = Field(description="Стакан")

class BarsRequest(BaseModel):
    """Структура запроса для получения исторических данных."""
    symbol: str = Field(description="Символ инструмента")
    timeframe: TimeFrame = Field(description="Необходимый таймфрейм")
    interval: Interval = Field(description="Начало и окончание запрашиваемого периода")

class QuoteRequest(BaseModel):
    """Запрос получения последней котировки по инструменту."""
    symbol: str = Field(description="Символ инструмента")

class OrderBookRequest(BaseModel):
    """Запрос получения текущего стакана по инструменту."""
    symbol: str = Field(description="Символ инструмента")

class LatestTradesRequest(BaseModel):
    """Запрос списка последних сделок по инструменту."""
    symbol: str = Field(description="Символ инструмента")