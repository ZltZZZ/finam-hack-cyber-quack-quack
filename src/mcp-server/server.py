import logging
from typing import Union
from mcp.server.fastmcp import FastMCP, Context
from adapters import FinamApiClient
from adapters.models import *


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


logging.info("Инициализация MCP сервера...")
mcp = FastMCP(
    name="Trader Tools Server",
    stateless_http=True,
    host="0.0.0.0"
)
mcp.settings.stateless_http = True
logging.info("MCP сервер 'Trader Tools Server' создан.")

api = FinamApiClient(secret_token="eyJraWQiOiJlZjk0NzA1Ni0xZDRjLTRiYTUtYTA2Yi1iYTUzZTM5MGE0MTEiLCJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhcmVhIjoidHQiLCJwYXJlbnQiOiI5YmNlM2EyYy0xMDk2LTQ5NjMtODQzZC1lMzIwNjI2M2IxN2EiLCJhcGlUb2tlblByb3BlcnRpZXMiOiJINHNJQUFBQUFBQUFfMjFVTzBfY1FCQUdmQmVRclVpd0NDSlJraVpDQ29JOFJXbnZyZThjYm0yemE0TXZqWFZ3TGxDT08zS1BSS1RNLTFtNGlCUXBhWkltWlFyLVM2cFU2Zk1mTWp1N0lBaHB2bTkyZGg0N251OXU1dmozNTU5ZmJwS3BHV3ZwUjJWbWFubGlaZHF1WGhXZXFHbURlZ0tOblIwYXIxeXlLeTdQSW1SQk04V2VtMGprYmU0clpsbk1GUWNzcXlQN0xOV2NZaHdQSk9aRlVVS1JZLUVpSjlRenpBMXZLWTZEa0JvT0REY05ZNTFZMWpGZUpMcXVTRFZuTHBlYUpUT3NfVjdFTll0VWM2cnZxZWNiVGpRenFwbnJlNVlJWkYtX042dTdPcTZ4NlJ2R2ViTm1MZFJzOHBxbVh6UFNmdTdXa0VOWHZ5X1U4MlpoM1p6TnU4T1c4YmYwT1haMWY5bGdoblVfdWFQblNqYWxXbFR1aFpTaVFiMEFNM0lLbTBHSGFNVm9zRlI0YUhEdTNVY2pqQVZ1TlpjMFdLbmFWaTUxcEl4TmdJdzc2MmdrZ3NrYmt4UGZKcWZzaWFXUGxSbUxXQzdMQUNSVHNLVUFqaUFMZ0MwRjZnSS1NcWw0X1Y2SFZCVU9pUVdmV3dFRTBFWUF3SmtDeUtUYmpFelg3Z1ZoVFpWbGFVWlFVMlRhOTNuT3hUcXAtRUhvRWxzaHoydHAwaUpWUDRMMUU4dUhWbE0tWk5XWklGYkRoNUt3RldJRkxBVklJYUpKV3dDcVYxTTlDM1lCUUNHRFE3TUs1eTQ4aFl0dFlzRjJBTGdDR1NqZ0NtQTZXSXNDdENSQkdSTXJraTVCQlNOeVJJaUFsUkVVTUdLQTJFU0VadkdtWEVlOGlYZ0x3dUZKcUdkaUNRb2ZSaVFlcVlvVWZvSEVrbTRFd0tRQ3VKSjFxQUJ3SGN4R0F5Q0FKSm5BSUNBSFlpVTFtRHBwYnBOS0FqT0JHVUdKcEFVbFVoZXVkOVRzR2FSVWxGcUkxb3c2SkQ0aXpKVlROWWFTRHRIQ0lWbzI0S3ZYWEtLbFE3UkFpRmJGOHNTcExuNVo4SGR5N1ducFBDdWQ1Nlh6b25SZWxzNnIwbmxkT205SzUyM3B2Q3VkOTZYem9YU09QXzJaTkluZkxmdXJaUzg4SFBkSHhXcTNQUnpsbzBHN1UtVERfU2VGdlhqQnZkY2Y5MGIyM0JuX28zNTNmRkRZczJkZDdlNzROUGx3c0w5WG5DMTY1YUpmVnlWbkwwelp1WE0tckh0WnUzYjNPeXJvNU5nZVBzRGp2RDcyRDR0ZXZ0OGJGWU5pT0RweG1wUjgxQi0xdXljejc0NlA4djZnVXd6TUstYlAxVE94WnBaaDBlMy1MX2p4N1J1ckItMlROeTlDWHhpcmZaVHZ0WHVkYnJGcV9Bc1hfRGpQM01YSTJYLUR5S1M5Zk9uTzJ0ckczWTJfWUoweTBEd0dBQUEiLCJzY29udGV4dCI6IkNoQUlCeElNZEhKaFpHVmZZWEJwWDNKMUNpZ0lBeElrTmpJeE9UVTROemd0Wm1ZeU15MDBZVEl4TFdJNFpqY3ROakUwTURjM1pUZ3lOakptQ2dRSUJSSUFDZ2tJQUJJRmFIUnRiRFVLS0FnQ0VpUXpOalUzWlRRNE1TMWhNRFppTFRFeFpqQXRZalZtWlMxaFptWTVPR00yTVRreE1XSUtCUWdJRWdFekNnUUlDUklBQ2drSUNoSUZNUzQyTGpRS0tBZ0VFaVJsWmprME56QTFOaTB4WkRSakxUUmlZVFV0WVRBMllpMWlZVFV6WlRNNU1HRTBNVEV5VFFvVlZGSkJSRVZCVUVsZlMxSkJWRTlUWDFSUFMwVk9FQUVZQVNBQktnZEZSRTlZWDBSQ09nSUlBMG9UQ2dNSWh3Y1NCUWlIb1o0QkdnVUloNWJEQVZnQllBRm9BWElHVkhoQmRYUm8iLCJ6aXBwZWQiOnRydWUsImNyZWF0ZWQiOiIxNzU5NTI0OTQ0IiwicmVuZXdFeHAiOiIxNzYwMDQzNjU5Iiwic2VzcyI6Ikg0c0lBQUFBQUFBQS93WEJzUXFETUJRRlVBcDJFVno4aE9MNklPOG1rWGZIQkp1cE5PTGtWaUxpUi9wMVBlZjE2U2RDNFU4N0JMUW93VjBVdGxQRm8ybHp3RHpiZFV5S1JOaENpZEZCUXNwRjZOOFFocEswbU05eDRmMFkrdWZ2dTI1MTdHcXUreDlrQ3lLQlhnQUFBQSIsImlzcyI6InR4c2VydmVyIiwia2V5SWQiOiJlZjk0NzA1Ni0xZDRjLTRiYTUtYTA2Yi1iYTUzZTM5MGE0MTEiLCJ0eXBlIjoiQXBpVG9rZW4iLCJzZWNyZXRzIjoidXJWTmIxOUU0RklaN2E0TVhMYmRPQT09Iiwic2NvcGUiOiIiLCJ0c3RlcCI6ImZhbHNlIiwic3BpblJlcSI6ZmFsc2UsImV4cCI6MTc2MDA0MzU5OSwic3BpbkV4cCI6IjE3NjAwNDM2NTkiLCJqdGkiOiI2MjE5NTg3OC1mZjIzLTRhMjEtYjhmNy02MTQwNzdlODI2MmYifQ.DeW6-fm0xdR0JORUsG4W7BnAoNDIXKeFsgkfnf-ABtUjuoVl6V1ssKnx2To4lI-_PLzOLjgzxlplak1ONUq94Q")
    
@mcp.tool()
async def token_details() -> Union[TokenDetailsResponse, ErrorResponse]:
    """Получение информации о токене сессии + информации о доступных аккаунтах. Токен зашит внутрь, его предоставлять не нужно. Это входная точка, если не дано никаких данных."""
    return await api.token_details()

# ===== АККАУНТЫ =====
@mcp.tool()
async def get_account(request: GetAccountRequest) -> Union[GetAccountResponse, ErrorResponse]:
    """Получение информации по конкретному аккаунту."""
    return await api.get_account(request)

@mcp.tool()
async def get_trades(request: TradesRequest) -> Union[GetTradesResponse, ErrorResponse]:
    """Получение истории по сделкам аккаунта."""
    return await api.get_trades(request)

@mcp.tool()
async def get_transactions(request: TransactionsRequest) -> Union[GetTransactionsResponse, ErrorResponse]:
    """Получение списка транзакций аккаунта."""
    return await api.get_transactions(request)

# ===== ИНСТРУМЕНТЫ =====
@mcp.tool()
async def get_exchanges() -> Union[GetExchangesResponse, ErrorResponse]:
    """Получение списка доступных бирж."""
    return await api.get_exchanges()

@mcp.tool()
async def get_assets() -> Union[GetAssetsResponse, ErrorResponse]:
    """Получение списка доступных акций, опционов, валют и других инструментов инвестирования для аккаунта."""
    # return await api.get_assets()
    return await ErrorResponse(status_code=200, error="слишком много выходных токенов, воспользуйтесь инструментом поиска по строке.")

@mcp.tool()
async def search_asset_by_string(search_string: str) -> Union[GetAssetsResponse, ErrorResponse]:
    """Получение списка доступных акций, опционов, валют и других инструментов инвестирования для аккаунта. Ищется вхождение строки в названии и тикере актива. Все названия активов либо на английском, либо на русском."""
    # return await api.get_assets()
    assets = await api.get_assets()
    if isinstance(assets, ErrorResponse):
        return assets
    
    finds = []

    assets_list = assets.model_dump()
    search_lower = search_string.lower()

    logging.info(f"Search string: {search_string}")

    for asset in assets_list['assets']:
        
        asset_name_lower = asset['name'].lower()
        asset_ticker_lower = asset['ticker'].lower()
        
        if search_lower in asset_name_lower or search_lower in asset_ticker_lower:
            logging.info("Found")
            finds.append(asset)

    return GetAssetsResponse(assets=finds)
    

@mcp.tool()
async def get_asset(request: GetAssetRequest) -> Union[GetAssetResponse, ErrorResponse]:
    """Получение информации по конкретному инструменту инвестирования для аккаунта."""
    return await api.get_asset(request)

@mcp.tool()
async def get_asset_params(request: GetAssetParamsRequest) -> Union[GetAssetParamsResponse, ErrorResponse]:
    """Получение торговых параметров по инструменту инвестирования для аккаунта."""
    return await api.get_asset_params(request)

@mcp.tool()
async def get_options_chain(request: OptionsChainRequest) -> Union[OptionsChainResponse, ErrorResponse]:
    """Получение цепочки опционов для базового актива."""
    return await api.get_options_chain(request)

@mcp.tool()
async def get_schedule(request: ScheduleRequest) -> Union[ScheduleResponse, ErrorResponse]:
    """Получение расписания торгов для инструмента инвестирования."""
    return await api.get_schedule(request)

@mcp.tool()
async def get_clock() -> Union[ClockResponse, ErrorResponse]:
    """Получение времени на сервере."""
    return await api.get_clock()

# ===== РЫНОЧНЫЕ ДАННЫЕ =====
@mcp.tool()
async def get_bars(request: BarsRequest) -> Union[BarsResponse, ErrorResponse]:
    """Получение исторических данных по инструменту инвестирования (агрегированные свечи)."""
    return await api.get_bars(request)

@mcp.tool()
async def get_last_quote(request: QuoteRequest) -> Union[LastQuoteResponse, ErrorResponse]:
    """Получение последней котировки по инструменту инвестирования."""
    return await api.get_last_quote(request)

@mcp.tool()
async def get_orderbook(request: OrderBookRequest) -> Union[OrderBookResponse, ErrorResponse]:
    """Получение текущего стакана по инструменту инвестирования."""
    return await api.get_orderbook(request)

@mcp.tool()
async def get_latest_trades(request: LatestTradesRequest) -> Union[LatestTradesResponse, ErrorResponse]:
    """Получение списка последних сделок по инструменту инвестирования."""
    return await api.get_latest_trades(request)

# ===== ЗАЯВКИ =====
@mcp.tool()
async def place_order(account_id: str, request: PlaceOrderRequest) -> Union[PlaceOrderResponse, ErrorResponse]:
    """Выставление биржевой заявки. При неудаче попробуй поставить TIME_IN_FORCE_DAY"""
    return await api.place_order(account_id, request)

@mcp.tool()
async def cancel_order(request: CancelOrderRequest) -> Union[CancelOrderResponse, ErrorResponse]:
    """Отмена биржевой заявки."""
    return await api.cancel_order(request)

@mcp.tool()
async def get_orders(request: OrdersRequest) -> Union[GetOrdersResponse, ErrorResponse]:
    """Получение списка заявок для аккаунта."""
    return await api.get_orders(request)

@mcp.tool()
async def get_order(request: GetOrderRequest) -> Union[GetOrderResponse, ErrorResponse]:
    """Получение информации о конкретном ордере."""
    return await api.get_order(request)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

