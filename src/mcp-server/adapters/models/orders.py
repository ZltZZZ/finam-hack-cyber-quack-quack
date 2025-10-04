from pydantic import BaseModel, Field
from typing import List, Optional
from .common import DecimalValue, Side, OrderType, TimeInForce, StopCondition, OrderStatus, ValidBefore, Interval

class Leg(BaseModel):
    """Структура для мульти-лег заявки."""
    symbol: str = Field(description="Символ инструмента")
    quantity: DecimalValue = Field(description="Количество")
    side: Side = Field(description="Сторона")

class Order(BaseModel):
    """Структура заявки."""
    account_id: str = Field(description="Идентификатор аккаунта")
    symbol: str = Field(description="Символ инструмента")
    quantity: DecimalValue = Field(description="Количество в шт.")
    side: Side = Field(description="Сторона (long или short)")
    type: OrderType = Field(description="Тип заявки")
    time_in_force: TimeInForce = Field(description="Срок действия заявки")
    limit_price: Optional[DecimalValue] = Field(None, description="Необходимо для лимитной и стоп лимитной заявки")
    stop_price: Optional[DecimalValue] = Field(None, description="Необходимо для стоп рыночной и стоп лимитной заявки")
    stop_condition: StopCondition = Field(description="Необходимо для стоп рыночной и стоп лимитной заявки")
    legs: List[Leg] = Field(description="Необходимо для мульти лег заявки")
    client_order_id: str = Field(description="Уникальный идентификатор заявки. Автоматически генерируется, если не отправлен. (максимум 20 символов)")
    valid_before: ValidBefore = Field(description="Срок действия условной заявки. Заполняется для заявок с типом ORDER_TYPE_STOP, ORDER_TYPE_STOP_LIMIT")
    comment: Optional[str] = Field(None, description="Метка заявки. (максимум 128 символов)")

class OrderState(BaseModel):
    """Структура состояния заявки."""
    order_id: str = Field(description="Идентификатор заявки")
    exec_id: str = Field(description="Идентификатор исполнения")
    status: OrderStatus = Field(description="Статус заявки")
    order: Order = Field(description="Заявка")
    transact_at: str = Field(description="Дата и время выставления заявки")
    accept_at: Optional[str] = Field(None, description="Дата и время принятия заявки")
    withdraw_at: Optional[str] = Field(None, description="Дата и время отмены заявки")

class CancelOrderResponse(BaseModel):
    """Структура ответа для отмены биржевой заявки."""
    order_id: str = Field(description="Идентификатор заявки")
    exec_id: str = Field(description="Идентификатор исполнения")
    status: OrderStatus = Field(description="Статус заявки")
    order: Order = Field(description="Заявка")
    transact_at: str = Field(description="Дата и время выставления заявки")

class GetOrderResponse(BaseModel):
    """Структура ответа для получения информации о конкретном ордере."""
    order_id: str = Field(description="Идентификатор заявки")
    exec_id: str = Field(description="Идентификатор исполнения")
    status: OrderStatus = Field(description="Статус заявки")
    order: Order = Field(description="Заявка")
    transact_at: str = Field(description="Дата и время выставления заявки")
    accept_at: Optional[str] = Field(None, description="Дата и время принятия заявки")
    withdraw_at: Optional[str] = Field(None, description="Дата и время отмены заявки")

class GetOrdersResponse(BaseModel):
    """Структура ответа для получения списка заявок для аккаунта."""
    orders: List[OrderState] = Field(description="Заявки")

class PlaceOrderRequest(BaseModel):
    """Структура запроса для выставления биржевой заявки."""
    symbol: str = Field(description="Символ инструмента")
    quantity: DecimalValue = Field(description="Количество в шт.")
    side: Side = Field(description="Сторона (long или short)")
    type: OrderType = Field(description="Тип заявки")
    time_in_force: TimeInForce = Field(description="Срок действия заявки")
    limit_price: Optional[DecimalValue] = Field(None, description="Необходимо для лимитной и стоп лимитной заявки")
    stop_price: Optional[DecimalValue] = Field(None, description="Необходимо для стоп рыночной и стоп лимитной заявки")
    stop_condition: Optional[StopCondition] = Field(None, description="Необходимо для стоп рыночной и стоп лимитной заявки")
    legs: Optional[List[Leg]] = Field(None, description="Необходимо для мульти лег заявки")
    client_order_id: Optional[str] = Field(None, description="Уникальный идентификатор заявки. Автоматически генерируется, если не отправлен. (максимум 20 символов)")
    valid_before: Optional[ValidBefore] = Field(None, description="Срок действия условной заявки. Заполняется для заявок с типом ORDER_TYPE_STOP, ORDER_TYPE_STOP_LIMIT")
    comment: Optional[str] = Field(None, description="Метка заявки. (максимум 128 символов)")

class PlaceOrderResponse(BaseModel):
    """Структура ответа для выставления биржевой заявки."""
    order_id: str = Field(description="Идентификатор заявки")
    exec_id: str = Field(description="Идентификатор исполнения")
    status: OrderStatus = Field(description="Статус заявки")
    order: Order = Field(description="Заявка")
    transact_at: str = Field(description="Дата и время выставления заявки")

class OrdersRequest(BaseModel):
    """Запрос получения списка торговых заявок."""
    account_id: str = Field(description="Идентификатор аккаунта")

class GetOrderRequest(BaseModel):
    """Запрос на получение конкретного ордера."""
    account_id: str = Field(description="Идентификатор аккаунта")
    order_id: str = Field(description="Идентификатор заявки")

class CancelOrderRequest(BaseModel):
    """Запрос отмены торговой заявки."""
    account_id: str = Field(description="Идентификатор аккаунта")
    order_id: str = Field(description="Идентификатор заявки")