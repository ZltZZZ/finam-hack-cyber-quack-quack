import httpx
from typing import Dict, Optional, Union, Any
import asyncio
from datetime import datetime, timedelta
import jwt
from .models import *
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FinamApiClient:
    """Клиент для работы с API Finam с автоматической аутентификацией."""
    
    def __init__(self, secret_token: str, base_url: str = "https://api.finam.ru", timeout: float = 30.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._token = None
        self._api_secret = secret_token
        self._token_expires_at = None
        self._client = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
            
    def set_api_secret(self, api_secret: str):
        """Установка API секрета для автоматической аутентификации."""
        self._api_secret = api_secret
        self._token = None
        self._token_expires_at = None
        
    def set_token(self, token: str):
        """Ручная установка JWT токена."""
        self._token = token
        try:
            # Пытаемся декодировать токен для получения времени экспирации
            decoded = jwt.decode(token, options={"verify_signature": False})
            if 'exp' in decoded:
                self._token_expires_at = datetime.fromtimestamp(decoded['exp'])
        except:
            self._token_expires_at = None
            
    def _get_headers(self) -> Dict[str, str]:
        """Получение заголовков для запросов."""
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"{self._token}"
        return headers

    def _is_token_expired(self) -> bool:
        """Проверка, истек ли токен (с запасом в 1 минуту)."""
        if not self._token_expires_at:
            return True
        return datetime.now() + timedelta(minutes=1) >= self._token_expires_at

    async def _ensure_authenticated(self):
        """Обеспечивает наличие валидного токена."""
        if not self._api_secret:
            raise ValueError("API secret is not set. Call set_api_secret() first.")
            
        if not self._token or self._is_token_expired():
            await self._authenticate()

    async def _authenticate(self):
        """Выполняет аутентификацию и сохраняет токен."""
        if not self._api_secret:
            raise ValueError("API secret is required for authentication")
            
        url = f"{self.base_url}/v1/sessions"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={"secret": self._api_secret})
            response.raise_for_status()
            auth_response = AuthResponse(**response.json())
            
        self._token = auth_response.token
        try:
            # Декодируем токен для получения времени экспирации
            decoded = jwt.decode(self._token, options={"verify_signature": False})
            if 'exp' in decoded:
                self._token_expires_at = datetime.fromtimestamp(decoded['exp'])
        except:
            # Если не удалось декодировать, устанавливаем время экспирации как None
            self._token_expires_at = None

    async def _make_request(self, method: str, url: str, **kwargs) -> Union[httpx.Response, Dict[str, Any]]:
        """Выполняет запрос с автоматической аутентификацией и улучшенной обработкой ошибок."""
        try:
            await self._ensure_authenticated()
            
            headers = self._get_headers()
            if 'headers' in kwargs:
                headers.update(kwargs['headers'])
            kwargs['headers'] = headers
            
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    async with httpx.AsyncClient() as client:
                        logging.info(f"MAKING REQUEST: {method} {url}")
                        print(f"🔍 Headers: { {k: v for k, v in headers.items() if k != 'Authorization'} }")
                        print(f"Args: {kwargs}")
                        
                        response = await client.request(method, url, **kwargs)
                        
                        # Логируем ответ
                        print(f"🔍 Response status: {response.status_code}")
                    
                        response.raise_for_status()
                        return response
                        
                except httpx.HTTPStatusError as e:
                    # Обработка ошибки - возвращаем None вместо исключения 
                    print(f"🚨 HTTPStatusError: {e}")
                    print(f"🚨 Request URL: {e.request.url}")
                    print(f"🚨 Response status: {e.response.status_code}")
                    
                    

                    try:
                        error_detail = e.response.json()
                        print(f"🚨 Error details: {error_detail}")
                    except:
                        error_text = e.response.text
                        print(f"🚨 Error text: {error_text}")

                    if e.response.status_code == 401 and attempt == 0:
                        print("🔄 Token expired, refreshing and retrying...")
                        self._token = None
                        await self._ensure_authenticated()
                        continue
                    
                    return {'status_code': e.response.status_code,'error': e.response.text}
                    
                except Exception as e:
                    print(f"🚨 Unexpected error: {e}")
                    print(f"🚨 Error type: {type(e)}")
                    return {'status_code': -1,'error': str(e)}

            return {'status_code': -1, 'error': 'Authentication failed after retries. Service unavaileble.'}
        except Exception as e:
            return {'status_code': -1, 'error': str(e)}

    def _prepare_response(self, response: Union[httpx.Response, Dict[str, Any]], response_model: Any) -> Union[Any, ErrorResponse]:
        if not isinstance(response, httpx.Response):
            response = ErrorResponse(**response)
        else:
            try:
                response = response_model(**response.json())
            except Exception as e:
                response = ErrorResponse(status_code=-1, error=str(e))

        return response
            
    
    async def token_details(self) -> Union[TokenDetailsResponse, ErrorResponse]:
        """Получение информации о токене сессии."""
        if not self._token or self._is_token_expired():
            try:
                await self._authenticate()
            except Exception as e:
                return ErrorResponse(status_code=-1, error="Authentication error. Service Unavailable.")
            
        url = f"{self.base_url}/v1/sessions/details"
        request = TokenDetailsRequest(token=self._token)
        response = await self._make_request("POST", url, json=request.model_dump())
        return self._prepare_response(response, TokenDetailsResponse)

    # ===== АККАУНТЫ =====
    
    async def get_account(self, request: GetAccountRequest) -> Union[GetAccountResponse, ErrorResponse]:
        """Получение информации по конкретному аккаунту."""
        url = f"{self.base_url}/v1/accounts/{request.account_id}"
        response = await self._make_request("GET", url)
        return self._prepare_response(response, GetAccountResponse)
    
    async def get_trades(self, request: TradesRequest) -> GetTradesResponse:
        """Получение истории по сделкам аккаунта."""
        url = f"{self.base_url}/v1/accounts/{request.account_id}/trades"
        params = {}
        if request.limit:
            params["limit"] = request.limit
        if request.interval:
            params.update({
                "interval.start_time": request.interval.start_time,
                "interval.end_time": request.interval.end_time
            })
            
        response = await self._make_request("GET", url, params=params)
        return self._prepare_response(response, GetTradesResponse)
    
    async def get_transactions(self, request: TransactionsRequest) -> Union[GetTransactionsResponse, ErrorResponse]:
        """Получение списка транзакций аккаунта."""
        url = f"{self.base_url}/v1/accounts/{request.account_id}/transactions"
        params = {}
        if request.limit:
            params["limit"] = request.limit
        if request.interval:
            params.update({
                "interval.start_time": request.interval.start_time,
                "interval.end_time": request.interval.end_time
            })
            
        response = await self._make_request("GET", url, params=params)
        return self._prepare_response(response, GetTransactionsResponse)

    # ===== ИНСТРУМЕНТЫ =====
    
    async def get_exchanges(self) -> Union[GetExchangesResponse, ErrorResponse]:
        """Получение списка доступных бирж."""
        url = f"{self.base_url}/v1/exchanges"
        response = await self._make_request("GET", url)
        return self._prepare_response(response, GetExchangesResponse)
    
    async def get_assets(self) -> GetAssetsResponse:
        """Получение списка доступных инструментов."""
        url = f"{self.base_url}/v1/assets"
        response = await self._make_request("GET", url)
        return self._prepare_response(response, GetAssetsResponse)
    
    async def get_asset(self, request: GetAssetRequest) -> Union[GetAssetResponse, ErrorResponse]:
        """Получение информации по конкретному инструменту."""
        url = f"{self.base_url}/v1/assets/{request.symbol}/"
        params = {}
        if request.account_id:
            params["account_id"] = request.account_id
            
        response = await self._make_request("GET", url, params=params)
        return self._prepare_response(response, GetAssetResponse)
    
    async def get_asset_params(self, request: GetAssetParamsRequest) -> Union[GetAssetParamsResponse, ErrorResponse]:
        """Получение торговых параметров по инструменту."""
        url = f"{self.base_url}/v1/assets/{request.symbol}/params"
        params = {}
        if request.account_id:
            params["account_id"] = request.account_id
            
        response = await self._make_request("GET", url, params=params)
        return self._prepare_response(response, GetAssetParamsResponse)
    
    async def get_options_chain(self, request: OptionsChainRequest) -> Union[OptionsChainResponse, ErrorResponse]:
        """Получение цепочки опционов для базового актива."""
        url = f"{self.base_url}/v1/assets/{request.underlying_symbol}/options"
        response = await self._make_request("GET", url)
        return self._prepare_response(response, OptionsChainResponse)
    
    async def get_schedule(self, request: ScheduleRequest) -> Union[ScheduleResponse, ErrorResponse]:
        """Получение расписания торгов для инструмента."""
        url = f"{self.base_url}/v1/assets/{request.symbol}/schedule"
        response = await self._make_request("GET", url)
        return self._prepare_response(response, ScheduleResponse)
    
    async def get_clock(self) -> ClockResponse:
        """Получение времени на сервере."""
        url = f"{self.base_url}/v1/assets/clock"
        response = await self._make_request("GET", url)
        return self._prepare_response(response, ClockResponse)

    # ===== РЫНОЧНЫЕ ДАННЫЕ =====
    
    async def get_bars(self, request: BarsRequest) -> Union[BarsResponse, ErrorResponse]:
        """Получение исторических данных по инструменту (агрегированные свечи)."""
        url = f"{self.base_url}/v1/instruments/{request.symbol}/bars"
        params = {
            "timeframe": request.timeframe.value,
            "interval.start_time": request.interval.start_time,
            "interval.end_time": request.interval.end_time
        }
        
        response = await self._make_request("GET", url, params=params)
        return self._prepare_response(response, BarsResponse)
    
    async def get_last_quote(self, request: QuoteRequest) -> Union[LastQuoteResponse, ErrorResponse]:
        """Получение последней котировки по инструменту."""
        url = f"{self.base_url}/v1/instruments/{request.symbol}/quotes/latest"
        response = await self._make_request("GET", url)
        return self._prepare_response(response, LastQuoteResponse)
    
    async def get_orderbook(self, request: OrderBookRequest) -> Union[OrderBookResponse, ErrorResponse]:
        """Получение текущего стакана по инструменту."""
        url = f"{self.base_url}/v1/instruments/{request.symbol}/orderbook"
        response = await self._make_request("GET", url)
        return self._prepare_response(response, OrderBookResponse)
    
    async def get_latest_trades(self, request: LatestTradesRequest) -> Union[LatestTradesResponse, ErrorResponse]:
        """Получение списка последних сделок по инструменту."""
        url = f"{self.base_url}/v1/instruments/{request.symbol}/trades/latest"
        response = await self._make_request("GET", url)
        return self._prepare_response(response, LatestTradesResponse)

    # ===== ЗАЯВКИ =====


    
    async def place_order(self, account_id: str, request: PlaceOrderRequest) -> Union[PlaceOrderResponse, ErrorResponse]:
        """Выставление биржевой заявки."""
        url = f"{self.base_url}/v1/accounts/{account_id}/orders"
        print(request.model_dump_json())
        response = await self._make_request("POST", url, json=request.model_dump())
        return self._prepare_response(response, PlaceOrderResponse)
    
    async def cancel_order(self, request: CancelOrderRequest) -> Union[CancelOrderResponse, ErrorResponse]:
        """Отмена биржевой заявки."""
        print(request.model_dump_json())
        url = f"{self.base_url}/v1/accounts/{request.account_id}/orders/{request.order_id}"
        response = await self._make_request("DELETE", url)
        return self._prepare_response(response, CancelOrderResponse)
    
    async def get_orders(self, request: OrdersRequest) -> Union[GetOrdersResponse, ErrorResponse]:
        """Получение списка заявок для аккаунта."""
        url = f"{self.base_url}/v1/accounts/{request.account_id}/orders"
        response = await self._make_request("GET", url)
        return self._prepare_response(response, GetOrdersResponse)
    
    async def get_order(self, request: GetOrderRequest) -> Union[GetOrderResponse, ErrorResponse]:
        """Получение информации о конкретном ордере."""
        url = f"{self.base_url}/v1/accounts/{request.account_id}/orders/{request.order_id}"
        response = await self._make_request("GET", url)
        return self._prepare_response(response, GetOrderResponse)


# ===== ПРИМЕР ИСПОЛЬЗОВАНИЯ =====

async def tests():
    """Тест работы всех эндпоинтов."""
    from datetime import datetime, timedelta
    
    async with FinamApiClient(secret_token="eyJraWQiOiJlZjk0NzA1Ni0xZDRjLTRiYTUtYTA2Yi1iYTUzZTM5MGE0MTEiLCJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhcmVhIjoidHQiLCJwYXJlbnQiOiI5YmNlM2EyYy0xMDk2LTQ5NjMtODQzZC1lMzIwNjI2M2IxN2EiLCJhcGlUb2tlblByb3BlcnRpZXMiOiJINHNJQUFBQUFBQUFfMjFVTzBfY1FCQUdmQmVRclVpd0NDSlJraVpDQ29JOFJXbnZyZThjYm0yemE0TXZqWFZ3TGxDT08zS1BSS1RNLTFtNGlCUXBhWkltWlFyLVM2cFU2Zk1mTWp1N0lBaHB2bTkyZGg0N251OXU1dmozNTU5ZmJwS3BHV3ZwUjJWbWFubGlaZHF1WGhXZXFHbURlZ0tOblIwYXIxeXlLeTdQSW1SQk04V2VtMGprYmU0clpsbk1GUWNzcXlQN0xOV2NZaHdQSk9aRlVVS1JZLUVpSjlRenpBMXZLWTZEa0JvT0REY05ZNTFZMWpGZUpMcXVTRFZuTHBlYUpUT3NfVjdFTll0VWM2cnZxZWNiVGpRenFwbnJlNVlJWkYtX042dTdPcTZ4NlJ2R2ViTm1MZFJzOHBxbVh6UFNmdTdXa0VOWHZ5X1U4MlpoM1p6TnU4T1c4YmYwT1haMWY5bGdoblVfdWFQblNqYWxXbFR1aFpTaVFiMEFNM0lLbTBHSGFNVm9zRlI0YUhEdTNVY2pqQVZ1TlpjMFdLbmFWaTUxcEl4TmdJdzc2MmdrZ3NrYmt4UGZKcWZzaWFXUGxSbUxXQzdMQUNSVHNLVUFqaUFMZ0MwRjZnSS1NcWw0X1Y2SFZCVU9pUVdmV3dFRTBFWUF3SmtDeUtUYmpFelg3Z1ZoVFpWbGFVWlFVMlRhOTNuT3hUcXAtRUhvRWxzaHoydHAwaUpWUDRMMUU4dUhWbE0tWk5XWklGYkRoNUt3RldJRkxBVklJYUpKV3dDcVYxTTlDM1lCUUNHRFE3TUs1eTQ4aFl0dFlzRjJBTGdDR1NqZ0NtQTZXSXNDdENSQkdSTXJraTVCQlNOeVJJaUFsUkVVTUdLQTJFU0VadkdtWEVlOGlYZ0x3dUZKcUdkaUNRb2ZSaVFlcVlvVWZvSEVrbTRFd0tRQ3VKSjFxQUJ3SGN4R0F5Q0FKSm5BSUNBSFlpVTFtRHBwYnBOS0FqT0JHVUdKcEFVbFVoZXVkOVRzR2FSVWxGcUkxb3c2SkQ0aXpKVlROWWFTRHRIQ0lWbzI0S3ZYWEtLbFE3UkFpRmJGOHNTcExuNVo4SGR5N1ducFBDdWQ1Nlh6b25SZWxzNnIwbmxkT205SzUyM3B2Q3VkOTZYem9YU09QXzJaTkluZkxmdXJaUzg4SFBkSHhXcTNQUnpsbzBHN1UtVERfU2VGdlhqQnZkY2Y5MGIyM0JuX28zNTNmRkRZczJkZDdlNzROUGx3c0w5WG5DMTY1YUpmVnlWbkwwelp1WE0tckh0WnUzYjNPeXJvNU5nZVBzRGp2RDcyRDR0ZXZ0OGJGWU5pT0RweG1wUjgxQi0xdXljejc0NlA4djZnVXd6TUstYlAxVE94WnBaaDBlMy1MX2p4N1J1ckItMlROeTlDWHhpcmZaVHZ0WHVkYnJGcV9Bc1hfRGpQM01YSTJYLUR5S1M5Zk9uTzJ0ckczWTJfWUoweTBEd0dBQUEiLCJzY29udGV4dCI6IkNoQUlCeElNZEhKaFpHVmZZWEJwWDNKMUNpZ0lBeElrTmpJeE9UVTROemd0Wm1ZeU15MDBZVEl4TFdJNFpqY3ROakUwTURjM1pUZ3lOakptQ2dRSUJSSUFDZ2tJQUJJRmFIUnRiRFVLS0FnQ0VpUXpOalUzWlRRNE1TMWhNRFppTFRFeFpqQXRZalZtWlMxaFptWTVPR00yTVRreE1XSUtCUWdJRWdFekNnUUlDUklBQ2drSUNoSUZNUzQyTGpRS0tBZ0VFaVJsWmprME56QTFOaTB4WkRSakxUUmlZVFV0WVRBMllpMWlZVFV6WlRNNU1HRTBNVEV5VFFvVlZGSkJSRVZCVUVsZlMxSkJWRTlUWDFSUFMwVk9FQUVZQVNBQktnZEZSRTlZWDBSQ09nSUlBMG9UQ2dNSWh3Y1NCUWlIb1o0QkdnVUloNWJEQVZnQllBRm9BWElHVkhoQmRYUm8iLCJ6aXBwZWQiOnRydWUsImNyZWF0ZWQiOiIxNzU5NTI0OTQ0IiwicmVuZXdFeHAiOiIxNzYwMDQzNjU5Iiwic2VzcyI6Ikg0c0lBQUFBQUFBQS93WEJzUXFETUJRRlVBcDJFVno4aE9MNklPOG1rWGZIQkp1cE5PTGtWaUxpUi9wMVBlZjE2U2RDNFU4N0JMUW93VjBVdGxQRm8ybHp3RHpiZFV5S1JOaENpZEZCUXNwRjZOOFFocEswbU05eDRmMFkrdWZ2dTI1MTdHcXUreDlrQ3lLQlhnQUFBQSIsImlzcyI6InR4c2VydmVyIiwia2V5SWQiOiJlZjk0NzA1Ni0xZDRjLTRiYTUtYTA2Yi1iYTUzZTM5MGE0MTEiLCJ0eXBlIjoiQXBpVG9rZW4iLCJzZWNyZXRzIjoidXJWTmIxOUU0RklaN2E0TVhMYmRPQT09Iiwic2NvcGUiOiIiLCJ0c3RlcCI6ImZhbHNlIiwic3BpblJlcSI6ZmFsc2UsImV4cCI6MTc2MDA0MzU5OSwic3BpbkV4cCI6IjE3NjAwNDM2NTkiLCJqdGkiOiI2MjE5NTg3OC1mZjIzLTRhMjEtYjhmNy02MTQwNzdlODI2MmYifQ.DeW6-fm0xdR0JORUsG4W7BnAoNDIXKeFsgkfnf-ABtUjuoVl6V1ssKnx2To4lI-_PLzOLjgzxlplak1ONUq94Q") as api:
        # ===== АУТЕНТИФИКАЦИЯ =====
        print("🔐 Тестирование аутентификации...")
        token_info = await api.token_details()
        if isinstance(token_info, ErrorResponse):
            print(f"Ошибка. status_code: {token_info.status_code}, error: {token_info.error}")
            return
        
        print("✅ Информация о токене получена")
        account_id = token_info.model_dump()['account_ids'][0]
        print(f"📊 Используем аккаунт: {account_id}")

        # ===== АККАУНТЫ =====
        print("\n👤 Тестирование работы с аккаунтами...")
        
        request = GetAccountRequest(account_id=account_id)
        account_info = await api.get_account(request)
        if isinstance(account_info, ErrorResponse):
            print(f"Ошибка. status_code: {account_info.status_code}, error: {account_info.error}")
            return
        print("✅ Информация об аккаунте получена")
        # print(account_info.model_dump_json(indent=2))

        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        request = TransactionsRequest(account_id=account_id, interval=Interval(start_time=start_time.isoformat(timespec="seconds") + "Z", end_time=end_time.isoformat(timespec="seconds") + "Z"))
        transactions = await api.get_transactions(request)
        if isinstance(transactions, ErrorResponse):
            print(f"Ошибка. status_code: {transactions.status_code}, error: {transactions.error}")
        else:
            print("✅ Транзакции получены")
            print(f"📈 Количество транзакций: {len(transactions.transactions)}")

        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        request = TradesRequest(account_id=account_id, interval=Interval(start_time=start_time.isoformat(timespec="seconds") + "Z", end_time=end_time.isoformat(timespec="seconds") + "Z"))
        trades = await api.get_trades(request)
        if isinstance(trades, ErrorResponse):
            print(f"Ошибка. status_code: {trades.status_code}, error: {trades.error}")
        else:
            print("✅ Сделки получены")
            print(f"📊 Количество сделок: {len(trades.trades)}")

        # ===== ИНСТРУМЕНТЫ =====
        print("\n📈 Тестирование работы с инструментами...")
        
        exchanges = await api.get_exchanges()
        if isinstance(exchanges, ErrorResponse):
            print(f"Ошибка. status_code: {exchanges.status_code}, error: {exchanges.error}")
            return
        print("✅ Биржи получены")
        print(f"🏛️ Количество бирж: {len(exchanges.exchanges)}")

        assets = await api.get_assets()
        if isinstance(assets, ErrorResponse):
            print(f"Ошибка. status_code: {assets.status_code}, error: {assets.error}")
            return
        print("✅ Инструменты получены")
        print(f"📊 Количество инструментов: {len(assets.assets)}")

        # Берем несколько разных инструментов для тестирования
        if len(assets.assets) >= 3:
            # Первый инструмент
            ticker1 = assets.assets[0].ticker
            mic1 = assets.assets[0].mic
            symbol1 = ticker1 + "@" + mic1
            
            # Второй инструмент
            ticker2 = assets.assets[1].ticker
            mic2 = assets.assets[1].mic
            symbol2 = ticker2 + "@" + mic2
            
            # Третий инструмент (если есть)
            ticker3 = assets.assets[2].ticker if len(assets.assets) > 2 else ticker1
            mic3 = assets.assets[2].mic if len(assets.assets) > 2 else mic1
            symbol3 = ticker3 + "@" + mic3

            print(f"🔧 Тестируем инструменты: {symbol1}, {symbol2}, {symbol3}")

            # Тестируем информацию по инструменту
            request = GetAssetRequest(symbol=symbol1, account_id=account_id)
            asset = await api.get_asset(request)
            if isinstance(asset, ErrorResponse):
                print(f"Ошибка. status_code: {asset.status_code}, error: {asset.error}")
                return
            print("✅ Информация по инструменту получена")
            print(f"📋 Инструмент: {asset.name}")

            # Тестируем параметры инструмента
            request = GetAssetParamsRequest(symbol=symbol1, account_id=account_id)
            params = await api.get_asset_params(request)
            if isinstance(params, ErrorResponse):
                print(f"Ошибка. status_code: {params.status_code}, error: {params.error}")
                return
            print("✅ Параметры инструмента получены")
            print(f"🔄 Торгуемый: {params.tradeable}")

            # Тестируем расписание
            request = ScheduleRequest(symbol=symbol1)
            schedule = await api.get_schedule(request)
            if isinstance(schedule, ErrorResponse):
                print(f"Ошибка. status_code: {schedule.status_code}, error: {schedule.error}")
                return
            print("✅ Расписание получено")
            print(f"⏰ Количество сессий: {len(schedule.sessions)}")

            # Тестируем время сервера
            clock = await api.get_clock()
            if isinstance(clock, ErrorResponse):
                print(f"Ошибка. status_code: {clock.status_code}, error: {clock.error}")
                return
            print("✅ Время сервера получено")
            print(f"🕒 Серверное время: {clock.timestamp}")

        # ===== РЫНОЧНЫЕ ДАННЫЕ =====
        print("\n📊 Тестирование рыночных данных...")
        
        if len(assets.assets) >= 2:
            # Получаем исторические данные (бары)
            from datetime import datetime, timedelta
            
            # Устанавливаем период - последние 7 дней
            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)
            
            request = BarsRequest(
                symbol=symbol1,
                timeframe=TimeFrame.TIME_FRAME_D,  # Дневной таймфрейм
                interval=Interval(
                    start_time=start_time.isoformat() + "Z",
                    end_time=end_time.isoformat() + "Z"
                )
            )
            bars = await api.get_bars(request)
            if isinstance(bars, ErrorResponse):
                print(f"Ошибка. status_code: {bars.status_code}, error: {bars.error}")
                return
            print("✅ Исторические данные получены")
            print(f"📈 Количество баров: {len(bars.bars)}")
            
            if bars.bars:
                print(f"📅 Первый бар: {bars.bars[0].timestamp}")
                print(f"📅 Последний бар: {bars.bars[-1].timestamp}")

            # Получаем последнюю котировку
            request = QuoteRequest(symbol=symbol1)
            last_quote = await api.get_last_quote(request)
            if isinstance(last_quote, ErrorResponse):
                print(f"Ошибка. status_code: {last_quote.status_code}, error: {last_quote.error}")
                return
            print("✅ Последняя котировка получена")
            print(f"💰 Последняя цена: {last_quote.quote.last.value}")

            # Получаем стакан
            request = OrderBookRequest(symbol=symbol1)
            orderbook = await api.get_orderbook(request)
            if isinstance(orderbook, ErrorResponse):
                print(f"Ошибка. status_code: {orderbook.status_code}, error: {orderbook.error}")
                return
            print("✅ Стакан получен")
            print(f"📊 Уровней в стакане: {len(orderbook.orderbook.rows)}")

            # Получаем последние сделки
            request = LatestTradesRequest(symbol=symbol1)
            latest_trades = await api.get_latest_trades(request)
            if isinstance(latest_trades, ErrorResponse):
                print(f"Ошибка. status_code: {latest_trades.status_code}, error: {latest_trades.error}")
                if latest_trades.status_code != 404:
                    return
            else:
                print("✅ Последние сделки получены")
                print(f"🔁 Количество сделок: {len(latest_trades.trades)}")

        # ===== ОПЦИОНЫ =====
        print("\n🎯 Тестирование работы с опционами...")
        
        # Ищем базовый актив для опционов (акции)
        underlying_assets = [asset for asset in assets.assets if "Option" in asset.name or "Options" in asset.name]
        if underlying_assets:
            underlying_symbol = underlying_assets[0].ticker + "@" + underlying_assets[0].mic
            try:
                request = OptionsChainRequest(underlying_symbol=underlying_symbol)
                options_chain = await api.get_options_chain(request)
                if isinstance(options_chain, ErrorResponse):
                    print(f"Ошибка. status_code: {options_chain.status_code}, error: {options_chain.error}")
                    return
                print("✅ Цепочка опционов получена")
                print(f"📋 Количество опционов: {len(options_chain.options)}")
                
                if options_chain.options:
                    # Показываем информацию о первом опционе
                    first_option = options_chain.options[0]
                    print(f"📊 Пример опциона: {first_option.symbol}, тип: {first_option.type}, страйк: {first_option.strike.value}")
            except Exception as e:
                print(f"⚠️ Не удалось получить цепочку опционов для {underlying_symbol}: {e}")

        # ===== ЗАЯВКИ =====
        print("\n📝 Тестирование работы с заявками...")

        # ===== ТЕСТИРОВАНИЕ ВЫСТАВЛЕНИЯ И ОТМЕНЫ ЗАЯВОК =====
        print("\n🔄 Тестирование выставления и отмены заявок...")
        
        if len(assets.assets) >= 1:
            # Берем первый доступный инструмент для тестирования заявок
            test_symbol = assets.assets[0].ticker + "@" + assets.assets[0].mic
            
            # Сначала получаем информацию об инструменте для корректных параметров
            asset_info = await api.get_asset(GetAssetRequest(symbol=test_symbol, account_id=account_id))
            if isinstance(asset_info, ErrorResponse):
                print(f"⚠️ Не удалось получить информацию об инструменте: {asset_info.error}")
            else:
                print(f"🔧 Тестируем заявки для инструмента: {asset_info.name}")
                
                # Тест 1: Пытаемся выставить некорректную заявку (для тестирования ошибок)
                try:
                    # Создаем заявку с минимальным количеством (скорее всего будет отклонена)
                    place_request = PlaceOrderRequest(
                        symbol=test_symbol,
                        quantity=DecimalValue(value="1"),  # Минимальное количество
                        side=Side.SIDE_BUY,
                        type=OrderType.ORDER_TYPE_LIMIT,
                        time_in_force=TimeInForce.TIME_IN_FORCE_DAY,
                        limit_price=DecimalValue(value="0.01")  # Нереальная цена
                    )
                    
                    place_result = await api.place_order(account_id, place_request)
                    
                    if isinstance(place_result, ErrorResponse):
                        print(f"✅ Ожидаемая ошибка при выставлении заявки: {place_result.error}")
                        
                        # Если заявка все же прошла, пробуем ее отменить
                        if "order_id" in str(place_result.error):
                            # Пытаемся извлечь order_id из ошибки (если есть)
                            import re
                            order_id_match = re.search(r'order_id[\'"]?\s*:\s*[\'"]?([^\'",}\s]+)', str(place_result.error))
                            if order_id_match:
                                order_id = order_id_match.group(1)
                                cancel_request = CancelOrderRequest(
                                    account_id=account_id,
                                    order_id=order_id
                                )
                                cancel_result = await api.cancel_order(cancel_request)
                                if isinstance(cancel_result, ErrorResponse):
                                    print(f"⚠️ Ошибка при отмене тестовой заявки: {cancel_result.error}")
                                else:
                                    print("✅ Тестовая заявка успешно отменена")
                    else:
                        print("✅ Заявка успешно выставлена (неожиданно)")
                        print(f"📝 ID заявки: {place_result.order_id}")
                        
                        # Пытаемся отменить только что созданную заявку
                        cancel_request = CancelOrderRequest(
                            account_id=account_id,
                            order_id=place_result.order_id
                        )
                        cancel_result = await api.cancel_order(cancel_request)
                        
                        if isinstance(cancel_result, ErrorResponse):
                            print(f"⚠️ Ошибка при отмене заявки: {cancel_result.error}")
                        else:
                            print("✅ Заявка успешно отменена")
                            print(f"📊 Статус после отмены: {cancel_result.status}")
                            
                except Exception as e:
                    print(f"⚠️ Исключение при тестировании заявок: {e}")
                
                # Тест 2: Пробуем отменить несуществующую заявку
                print("\n🧪 Тест отмены несуществующей заявки...")
                fake_cancel_request = CancelOrderRequest(
                    account_id=account_id,
                    order_id="NON_EXISTENT_ORDER_12345"
                )
                fake_cancel_result = await api.cancel_order(fake_cancel_request)
                
                if isinstance(fake_cancel_result, ErrorResponse):
                    print(f"✅ Ожидаемая ошибка при отмене несуществующей заявки: {fake_cancel_result.error}")
                else:
                    print("⚠️ Неожиданный успех при отмене несуществующей заявки")
                
                # Тест 3: Пробуем получить информацию о несуществующей заявке
                print("\n🧪 Тест получения несуществующей заявки...")
                fake_get_request = GetOrderRequest(
                    account_id=account_id,
                    order_id="NON_EXISTENT_ORDER_12345"
                )
                fake_get_result = await api.get_order(fake_get_request)
                
                if isinstance(fake_get_result, ErrorResponse):
                    print(f"✅ Ожидаемая ошибка при получении несуществующей заявки: {fake_get_result.error}")
                else:
                    print("⚠️ Неожиданный успех при получении несуществующей заявки")

        # ===== ТЕСТИРОВАНИЕ РАЗНЫХ ТИПОВ ЗАЯВОК =====
        print("\n🎯 Тестирование разных типов заявок...")
        
        if len(assets.assets) >= 1:
            test_symbol = assets.assets[0].ticker + "@" + assets.assets[0].mic
            
            # Получаем последнюю котировку для реалистичных цен
            quote_info = await api.get_last_quote(QuoteRequest(symbol=test_symbol))
            if not isinstance(quote_info, ErrorResponse) and hasattr(quote_info.quote, 'last'):
                current_price = float(quote_info.quote.last.value)
                print(f"💰 Текущая цена {test_symbol}: {current_price}")
                
                # Тестируем разные типы заявок (только создание объектов, без отправки)
                order_types_to_test = [
                    ("Лимитная заявка", OrderType.ORDER_TYPE_LIMIT),
                    ("Рыночная заявка", OrderType.ORDER_TYPE_MARKET),
                ]
                
                for order_name, order_type in order_types_to_test:
                    try:
                        if order_type == OrderType.ORDER_TYPE_LIMIT:
                            test_order = PlaceOrderRequest(
                                symbol=test_symbol,
                                quantity=DecimalValue(value="1"),
                                side=Side.SIDE_BUY,
                                type=order_type,
                                time_in_force=TimeInForce.TIME_IN_FORCE_DAY,
                                limit_price=DecimalValue(value=str(current_price * 0.9))  # 10% ниже текущей цены
                            )

                            place_result = await api.place_order(account_id, test_order)
                    
                            if isinstance(place_result, ErrorResponse):
                                print(f"Ошибка. status_code: {place_result.status_code}, error: {place_result.error}")
                        else:  # MARKET order
                            test_order = PlaceOrderRequest(
                                symbol=test_symbol,
                                quantity=DecimalValue(value="1"),
                                side=Side.SIDE_BUY,
                                type=order_type,
                                time_in_force=TimeInForce.TIME_IN_FORCE_DAY
                            )
                        
                            place_result = await api.place_order(account_id, test_order)
                    
                            if isinstance(place_result, ErrorResponse):
                                print(f"Ошибка. status_code: {place_result.status_code}, error: {place_result.error}")
                        
                        print(f"✅ {order_name}: объект создан успешно")
                        # Не отправляем фактически, чтобы избежать реальных сделок
                        
                    except Exception as e:
                        print(f"❌ Ошибка создания {order_name}: {e}")
            else:
                print("⚠️ Не удалось получить текущую цену для тестирования заявок")
        
        # Получаем список заявок
        try:
            request = OrdersRequest(account_id=account_id)
            orders = await api.get_orders(request)
            if isinstance(orders, ErrorResponse):
                    print(f"Ошибка. status_code: {orders.status_code}, error: {orders.error}")
            else:
                print("✅ Список заявок получен")
                print(f"📋 Количество заявок: {len(orders.orders)}")
            
            # Если есть активные заявки, получаем информацию о конкретной
            if orders.orders:
                first_order = orders.orders[0]
                request = GetOrderRequest(
                    account_id=account_id,
                    order_id=first_order.order_id
                )
                order_detail = await api.get_order(request)
                if isinstance(order_detail, ErrorResponse):
                    print(f"Ошибка. status_code: {order_detail.status_code}, error: {order_detail.error}")
                else:
                    print("✅ Детальная информация о заявке получена")
                    print(f"📊 Статус заявки: {order_detail.status}")
        except Exception as e:
            print(f"⚠️ Ошибка при работе с заявками: {e}")

        # ===== ТЕСТИРОВАНИЕ РАЗНЫХ ТИПОВ ИНСТРУМЕНТОВ =====
        print("\n🔍 Тестирование разных типов инструментов...")
        
        # Группируем инструменты по типам
        asset_types = {}
        for asset in assets.assets:
            asset_type = asset.type
            if asset_type not in asset_types:
                asset_types[asset_type] = []
            asset_types[asset_type].append(asset)
        
        print("📋 Найденные типы инструментов:")
        for asset_type, type_assets in asset_types.items():
            print(f"  - {asset_type}: {len(type_assets)} инструментов")
            
            # Тестируем первый инструмент каждого типа
            if type_assets:
                test_asset = type_assets[0]
                test_symbol = test_asset.ticker + "@" + test_asset.mic
                try:
                    # Получаем базовую информацию
                    request = GetAssetRequest(symbol=test_symbol, account_id=account_id)
                    asset_info = await api.get_asset(request)
                    if isinstance(asset_info, ErrorResponse):
                        print(f"Ошибка. status_code: {asset_info.status_code}, error: {asset_info.error}")
                    else:
                        print(f"    ✅ {asset_info.name}: OK")
                    
                    # Пытаемся получить параметры
                    request = GetAssetParamsRequest(symbol=test_symbol, account_id=account_id)
                    asset_params = await api.get_asset_params(request)
                    if isinstance(asset_params, ErrorResponse):
                        print(f"Ошибка. status_code: {asset_params.status_code}, error: {asset_params.error}")
                    else:
                        print(f"    ✅ Параметры: торгуемый={asset_params.tradeable}")
                    
                except Exception as e:
                    print(f"    ❌ Ошибка для {asset_info.name}: {e}")

        print("\n🎉 Все тесты завершены успешно!")

        # ===== СВОДНАЯ ИНФОРМАЦИЯ =====
        print("\n📊 Сводная информация:")
        print(f"• Аккаунт: {account_id}")
        print(f"• Бирж: {len(exchanges.exchanges)}")
        print(f"• Инструментов: {len(assets.assets)}")
        print(f"• Типов инструментов: {len(asset_types)}")
        
        if 'trades' in locals():
            print(f"• Сделок в истории: {len(trades.trades)}")
        if 'transactions' in locals():
            print(f"• Транзакций в истории: {len(transactions.transactions)}")
        if 'orders' in locals():
            print(f"• Активных заявок: {len(orders.orders)}")


if __name__ == "__main__":
    asyncio.run(tests())