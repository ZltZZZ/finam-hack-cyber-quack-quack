from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from .common import DecimalValue, Money, Interval

class Asset(BaseModel):
    """Структура информации об инструменте."""
    symbol: str = Field(description="Символ инструмента ticker@mic")
    id: str = Field(description="Идентификатор инструмента")
    ticker: str = Field(description="Тикер инструмента")
    mic: str = Field(description="mic идентификатор биржи")
    isin: str = Field(description="Isin идентификатор инструмента")
    type: str = Field(description="Тип инструмента")
    name: str = Field(description="Наименование инструмента")

class GetAssetsResponse(BaseModel):
    """Структура ответа для получения списка доступных инструментов."""
    assets: List[Asset] = Field(description="Информация об инструменте")

class Exchange(BaseModel):
    """Структура информации о бирже."""
    mic: str = Field(description="Идентификатор биржи mic")
    name: str = Field(description="Наименование биржи")

class GetExchangesResponse(BaseModel):
    """Структура ответа для получения списка доступных бирж."""
    exchanges: List[Exchange] = Field(description="Информация о бирже")

class Date(BaseModel):
    """Структура даты."""
    year: int = Field(description="Год")
    month: int = Field(description="Месяц")
    day: int = Field(description="День")

class GetAssetResponse(BaseModel):
    """Структура ответа для получения информации по конкретному инструменту."""
    board: str = Field(description="Код режима торгов")
    id: str = Field(description="Идентификатор инструмента")
    ticker: str = Field(description="Тикер инструмента")
    mic: str = Field(description="mic идентификатор биржи")
    isin: str = Field(description="Isin идентификатор инструмента")
    type: str = Field(description="Тип инструмента")
    name: str = Field(description="Наименование инструмента")
    decimals: int = Field(description="Кол-во десятичных знаков в цене")
    min_step: str = Field(description="Минимальный шаг цены. Для расчета финального ценового шага: min_step/(10^decimals)")
    lot_size: DecimalValue = Field(description="Кол-во штук в лоте")
    expiration_date: Optional[Date] = Field(None, description="Дата экспирации фьючерса")
    quote_currency: Optional[str] = Field(None, description="Валюта котировки, может не совпадать с валютой режима торгов инструмента")

class LongableStatus(str, Enum):
    """Статус доступности операций в Лонг."""
    NOT_AVAILABLE = "NOT_AVAILABLE"
    AVAILABLE = "AVAILABLE"
    ACCOUNT_NOT_APPROVED = "ACCOUNT_NOT_APPROVED"

class Longable(BaseModel):
    """Структура доступности операций в Лонг."""
    value: LongableStatus = Field(description="Статус инструмента")
    halted_days: int = Field(description="Сколько дней действует запрет на операции в Лонг (если есть)")

class ShortableStatus(str, Enum):
    """Статус доступности операций в Шорт."""
    NOT_AVAILABLE = "NOT_AVAILABLE"
    AVAILABLE = "AVAILABLE"
    HTB = "HTB"
    ACCOUNT_NOT_APPROVED = "ACCOUNT_NOT_APPROVED"
    AVAILABLE_STRATEGY = "AVAILABLE_STRATEGY"

class Shortable(BaseModel):
    """Структура доступности операций в Шорт."""
    value: ShortableStatus = Field(description="Статус инструмента")
    halted_days: int = Field(description="Сколько дней действует запрет на операции в Шорт (если есть)")

class GetAssetParamsResponse(BaseModel):
    """Структура ответа для получения торговых параметров по инструменту."""
    symbol: str = Field(description="Символ инструмента в формате ticker@mic")
    account_id: str = Field(description="ID аккаунта для которого подбираются торговые параметры")
    tradeable: bool = Field(description="Доступны ли торговые операции")
    longable: Optional[Longable] = Field(None, description="Доступны ли операции в Лонг")
    shortable: Optional[Shortable] = Field(None, description="Доступны ли операции в Шорт")
    long_risk_rate: Optional[DecimalValue] = Field(None, description="Ставка риска для операции в Лонг")
    long_collateral: Optional[Money] = Field(None, description="Сумма обеспечения для поддержания позиции Лонг (deprecated)")
    short_risk_rate: Optional[DecimalValue] = Field(None, description="Ставка риска для операции в Шорт")
    short_collateral: Optional[Money] = Field(None, description="Сумма обеспечения для поддержания позиции Шорт (deprecated)")
    long_initial_margin: Optional[Money] = Field(None, description="Начальные требования, сколько на счету должно быть свободных денежных средств, чтобы открыть лонг позицию")
    short_initial_margin: Optional[Money] = Field(None, description="Начальные требования, сколько на счету должно быть свободных денежных средств, чтобы открыть шорт позицию")

class OptionType(str, Enum):
    """Тип опциона."""
    TYPE_UNSPECIFIED = "TYPE_UNSPECIFIED"
    TYPE_CALL = "TYPE_CALL"
    TYPE_PUT = "TYPE_PUT"

class Option(BaseModel):
    """Структура информации об опционе."""
    symbol: str = Field(description="Символ инструмента в формате ticker@mic")
    type: OptionType = Field(description="Тип инструмента")
    contract_size: DecimalValue = Field(description="Лот, количество базового актива в инструменте")
    trade_first_day: Optional[Date] = Field(None, description="Дата старта торговли")
    trade_last_day: Date = Field(description="Дата окончания торговли")
    strike: DecimalValue = Field(description="Цена исполнения опциона")
    multiplier: Optional[DecimalValue] = Field(None, description="Множитель опциона")
    expiration_first_day: Date = Field(description="Дата начала экспирации")
    expiration_last_day: Date = Field(description="Дата окончания экспирации")

class OptionsChainResponse(BaseModel):
    """Структура ответа для получения цепочки опционов для базового актива."""
    symbol: str = Field(description="Символ базового актива опциона  в формате ticker@mic")
    options: List[Option] = Field(description="Информация об опционе")

class Session(BaseModel):
    """Структура сессии торгов."""
    type: str = Field(description="Тип сессии")
    interval: Interval = Field(description="Интервал сессии")

class ScheduleResponse(BaseModel):
    """Структура ответа для получения расписания торгов для инструмента."""
    symbol: str = Field(description="Символ инструмента в формате ticker@mic")
    sessions: List[Session] = Field(description="Сессии инструмента")

class ClockResponse(BaseModel):
    """Структура ответа для получения времени на сервере."""
    timestamp: str = Field(description="Метка времени в формате %Y-%m-%dT%H:%M:%SZ")

class ExchangesRequest(BaseModel):
    """Запрос получения списка доступных бирж."""
    pass

class AssetsRequest(BaseModel):
    """Запрос получения списка доступных инструментов."""
    pass

class GetAssetRequest(BaseModel):
    """Запрос получения информации по конкретному инструменту."""
    symbol: str = Field(description="Символ инструмента в формате ticker@mic")
    account_id: str = Field(description="ID аккаунта для которого будет подбираться информация по инструменту")

class GetAssetParamsRequest(BaseModel):
    """Запрос торговых параметров инструмента."""
    symbol: str = Field(description="Символ инструмента в формате ticker@mic")
    account_id: str = Field(description="ID аккаунта для которого будут подбираться торговые параметры")

class OptionsChainRequest(BaseModel):
    """Запрос получения цепочки опционов."""
    underlying_symbol: str = Field(description="Символ базового актива опциона")

class ScheduleRequest(BaseModel):
    """Запрос получения расписания инструмента."""
    symbol: str = Field(description="Символ инструмента в формате ticker@mic")

class ClockRequest(BaseModel):
    """Запрос получения времени на сервере."""
    pass