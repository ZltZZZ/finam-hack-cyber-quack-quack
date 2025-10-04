from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from .common import DecimalValue, Money, Side, Interval

class Position(BaseModel):
    """Структура позиции."""
    symbol: str = Field(description="Символ инструмента")
    quantity: DecimalValue = Field(description="Количество в шт., значение со знаком определяющее (long-short)")
    average_price: Optional[DecimalValue] = Field(None, description="Средняя цена. Не заполняется для FORTS позиций")
    current_price: DecimalValue = Field(description="Текущая цена")
    maintenance_margin: Optional[DecimalValue] = Field(None, description="Поддерживающее гарантийное обеспечение. Заполняется только для FORTS позиций")
    daily_pnl: Optional[DecimalValue] = Field(None, description="Прибыль или убыток за текущий день (PnL). Не заполняется для FORTS позиций")
    unrealized_pnl: DecimalValue = Field(description="Суммарная нереализованная прибыль или убыток (PnL) текущей позиции")

class MC(BaseModel):
    """Общий тип для счетов Московской Биржи."""
    available_cash: DecimalValue = Field(description="Сумма собственных денежных средств на счете, доступная для торговли. Включает маржинальные средства.")
    initial_margin: DecimalValue = Field(description="Начальная маржа")
    maintenance_margin: DecimalValue = Field(description="Минимальная маржа")

class MCT(BaseModel):
    """Тип портфеля для счетов на американских рынках."""
    pass  # Пустая структура согласно proto

class FORTS(BaseModel):
    """Тип портфеля для торговли на срочном рынке Московской Биржи."""
    available_cash: DecimalValue = Field(description="Сумма собственных денежных средств на счете, доступная для торговли. Включает маржинальные средства.")
    money_reserved: DecimalValue = Field(description="Минимальная маржа (необходимая сумма обеспечения под открытые позиции)")

class GetAccountResponse(BaseModel):
    """Структура ответа для получения информации по аккаунту."""
    account_id: str = Field(description="Идентификатор аккаунта")
    type: str = Field(description="Тип аккаунта")
    status: str = Field(description="Статус аккаунта")
    equity: DecimalValue = Field(description="Доступные средства плюс стоимость открытых позиций")
    unrealized_profit: DecimalValue = Field(description="Нереализованная прибыль")
    positions: List[Position] = Field(description="Позиции. Открытые, плюс теоретические (по неисполненным активным заявкам)")
    cash: List[Money] = Field(description="Сумма собственных денежных средств на счете, доступная для торговли. Не включает маржинальные средства.")
    portfolio_mc: Optional[MC] = Field(None, description="Общий тип для счетов Московской Биржи")
    portfolio_mct: Optional[MCT] = Field(None, description="Тип портфеля для счетов на американских рынках")
    portfolio_forts: Optional[FORTS] = Field(None, description="Тип портфеля для торговли на срочном рынке Московской Биржи")

class AccountTrade(BaseModel):
    """Структура сделки аккаунта."""
    trade_id: str = Field(description="Идентификатор сделки")
    symbol: str = Field(description="Символ инструмента")
    price: DecimalValue = Field(description="Цена сделки")
    size: DecimalValue = Field(description="Объем сделки")
    side: Side = Field(description="Направление сделки (BUY/SELL)")
    timestamp: str = Field(description="Время сделки")
    order_id: str = Field(description="Идентификатор заявки")
    account_id: str = Field(description="Идентификатор аккаунта")

class GetTradesResponse(BaseModel):
    """Структура ответа для получения истории сделок аккаунта."""
    trades: List[AccountTrade] = Field(description="Сделки по аккаунту")

class TransactionTrade(BaseModel):
    """Информация о сделке в транзакции."""
    size: Optional[DecimalValue] = Field(None, description="Количество в шт.")
    price: Optional[DecimalValue] = Field(None, description="Цена сделки за штуку")
    accrued_interest: Optional[DecimalValue] = Field(None, description="НКД. Заполнено если в сделке есть НКД")

class TransactionCategory(str, Enum):
    """Категории транзакции."""
    OTHERS = "OTHERS"
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    INCOME = "INCOME"
    COMMISSION = "COMMISSION"
    TAX = "TAX"
    INHERITANCE = "INHERITANCE"
    TRANSFER = "TRANSFER"
    CONTRACT_TERMINATION = "CONTRACT_TERMINATION"
    OUTCOMES = "OUTCOMES"
    FINE = "FINE"
    LOAN = "LOAN"

class Transaction(BaseModel):
    """Структура транзакции."""
    id: str = Field(description="Идентификатор транзакции")
    category: Optional[str] = Field(None, description="Тип транзакции из TransactionCategory (deprecated)")
    timestamp: str = Field(description="Метка времени")
    symbol: str = Field(description="Символ инструмента")
    change: Money = Field(description="Изменение в деньгах")
    trade: Optional[TransactionTrade] = Field(None, description="Информация о сделке")
    transaction_category: TransactionCategory = Field(description="Категория транзакции из TransactionCategory")
    transaction_name: str = Field(description="Наименование транзакции")

class GetTransactionsResponse(BaseModel):
    """Структура ответа для получения списка транзакций аккаунта."""
    transactions: List[Transaction] = Field(description="Транзакции по аккаунту")

class GetAccountRequest(BaseModel):
    """Запрос получения информации по конкретному аккаунту."""
    account_id: str = Field(description="Идентификатор аккаунта")

class TradesRequest(BaseModel):
    """Запрос получения истории по сделкам."""
    account_id: str = Field(description="Идентификатор аккаунта")
    limit: Optional[int] = Field(None, description="Лимит количества сделок")
    interval: Interval = Field(None, description="Начало и окончание запрашиваемого периода")

class TransactionsRequest(BaseModel):
    """Запрос получения списка транзакций."""
    account_id: str = Field(description="Идентификатор аккаунта")
    limit: Optional[int] = Field(None, description="Лимит количества транзакций")
    interval: Interval = Field(None, description="Начало и окончание запрашиваемого периода")