import logging
from typing import Union
from mcp.server.fastmcp import FastMCP, Context
from .adapters import FinamApiClient
from .adapters.models import *


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


logging.info("Инициализация MCP сервера...")
mcp = FastMCP(
    name="Trader Tools Server",
    description="Предоставляет доступ к инструментам площадки для торговых операций",
    stateless_http=True,
    host="0.0.0.0"
)
mcp.settings.stateless_http = True
logging.info("MCP сервер 'Trader Tools Server' создан.")

api = FinamApiClient(secret_token="alsdlsadl")
    
@mcp.tool()
async def token_details() -> Union[TokenDetailsResponse, ErrorRequest]:
    """Получение информации о токене сессии + информации о доступных аккаунтах. Токен зашит внутрь, его предоставлять не нужно. Это входная точка, если не дано никаких данных."""
    return await api.token_details()

# ===== АККАУНТЫ =====
@mcp.tool()
async def get_account(request: GetAccountRequest) -> Union[GetAccountResponse, ErrorRequest]:
    """Получение информации по конкретному аккаунту."""
    return await api.get_account(request)

@mcp.tool()
async def get_trades(request: TradesRequest) -> Union[GetTradesResponse, ErrorRequest]:
    """Получение истории по сделкам аккаунта."""
    return await api.get_trades(request)

@mcp.tool()
async def get_transactions(request: TransactionsRequest) -> Union[GetTransactionsResponse, ErrorRequest]:
    """Получение списка транзакций аккаунта."""
    return await api.get_transactions(request)

# ===== ИНСТРУМЕНТЫ =====
@mcp.tool()
async def get_exchanges() -> Union[GetExchangesResponse, ErrorRequest]:
    """Получение списка доступных бирж."""
    return await api.get_exchanges()

@mcp.tool()
async def get_assets() -> Union[GetAssetsResponse, ErrorRequest]:
    """Получение списка доступных инструментов для аккаунта."""
    return await api.get_assets()

@mcp.tool()
async def get_asset(request: GetAssetRequest) -> Union[GetAssetResponse, ErrorRequest]:
    """Получение информации по конкретному инструменту для аккаунта."""
    return await api.get_asset(request)

@mcp.tool()
async def get_asset_params(request: GetAssetParamsRequest) -> Union[GetAssetParamsResponse, ErrorRequest]:
    """Получение торговых параметров по инструменту для аккаунта."""
    return await api.get_asset_params(request)

@mcp.tool()
async def get_options_chain(request: OptionsChainRequest) -> Union[OptionsChainResponse, ErrorRequest]:
    """Получение цепочки опционов для базового актива."""
    return await api.get_options_chain(request)

@mcp.tool()
async def get_schedule(request: ScheduleRequest) -> Union[ScheduleResponse, ErrorRequest]:
    """Получение расписания торгов для инструмента."""
    return await api.get_schedule(request)

@mcp.tool()
async def get_clock() -> Union[ClockResponse, ErrorRequest]:
    """Получение времени на сервере."""
    return await api.get_clock()

# ===== РЫНОЧНЫЕ ДАННЫЕ =====
@mcp.tool()
async def get_bars(request: BarsRequest) -> Union[BarsResponse, ErrorRequest]:
    """Получение исторических данных по инструменту (агрегированные свечи)."""
    return await api.get_bars(request)

@mcp.tool()
async def get_last_quote(request: QuoteRequest) -> Union[LastQuoteResponse, ErrorRequest]:
    """Получение последней котировки по инструменту."""
    return await api.get_last_quote(request)

@mcp.tool()
async def get_orderbook(request: OrderBookRequest) -> Union[OrderBookResponse, ErrorRequest]:
    """Получение текущего стакана по инструменту."""
    return await api.get_orderbook(request)

@mcp.tool()
async def get_latest_trades(request: LatestTradesRequest) -> Union[LatestTradesResponse, ErrorRequest]:
    """Получение списка последних сделок по инструменту."""
    return await api.get_latest_trades(request)

# ===== ЗАЯВКИ =====
@mcp.tool()
async def place_order(account_id: str, request: PlaceOrderRequest) -> Union[PlaceOrderResponse, ErrorRequest]:
    """Выставление биржевой заявки."""
    return await api.place_order(account_id, request)

@mcp.tool()
async def cancel_order(request: CancelOrderRequest) -> Union[CancelOrderResponse, ErrorRequest]:
    """Отмена биржевой заявки."""
    return await api.cancel_order(request)

@mcp.tool()
async def get_orders(request: OrdersRequest) -> Union[GetOrdersResponse, ErrorRequest]:
    """Получение списка заявок для аккаунта."""
    return await api.get_orders(request)

@mcp.tool()
async def get_order(request: GetOrderRequest) -> Union[GetOrderResponse, ErrorRequest]:
    """Получение информации о конкретном ордере."""
    return await api.get_order(request)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

