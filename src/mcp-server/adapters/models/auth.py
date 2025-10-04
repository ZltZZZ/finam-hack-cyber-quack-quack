from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from .common import BaseModel

class AuthRequest(BaseModel):
    """Запрос авторизации."""
    secret: str = Field(description="API токен (secret key)")

class TokenDetailsRequest(BaseModel):
    """Запрос информации о токене."""
    token: str = Field(description="JWT-токен")

class SubscribeJwtRenewalRequest(BaseModel):
    """Запрос подписки на обновление JWT токена."""
    secret: str = Field(description="API токен (secret key)")

class MDPermission(BaseModel):
    """Информация о доступе к рыночным данным."""
    
    class QuoteLevel(str, Enum):
        """Уровень котировок."""
        QUOTE_LEVEL_UNSPECIFIED = "QUOTE_LEVEL_UNSPECIFIED"
        QUOTE_LEVEL_LAST_PRICE = "QUOTE_LEVEL_LAST_PRICE"
        QUOTE_LEVEL_BEST_BID_OFFER = "QUOTE_LEVEL_BEST_BID_OFFER"
        QUOTE_LEVEL_DEPTH_OF_MARKET = "QUOTE_LEVEL_DEPTH_OF_MARKET"
        QUOTE_LEVEL_DEPTH_OF_BOOK = "QUOTE_LEVEL_DEPTH_OF_BOOK"
        QUOTE_LEVEL_ACCESS_FORBIDDEN = "QUOTE_LEVEL_ACCESS_FORBIDDEN"
    
    quote_level: QuoteLevel = Field(description="Уровень котировок")
    delay_minutes: int = Field(description="Задержка в минутах")
    mic: Optional[str] = Field(None, description="Идентификатор биржи mic")
    country: Optional[str] = Field(None, description="Страна")
    continent: Optional[str] = Field(None, description="Континент")
    worldwide: Optional[bool] = Field(None, description="Весь мир")

class TokenDetailsResponse(BaseModel):
    """Информация о токене. Входная точка, если не хватает данных для начала выполнения действий."""
    created_at: str = Field(description="Дата и время создания")
    expires_at: str = Field(description="Дата и время экспирации")
    md_permissions: List[MDPermission] = Field(description="Информация о доступе к рыночным данным")
    account_ids: List[str] = Field(description="Идентификаторы аккаунтов")
    readonly: bool = Field(description="Сессия и торговые счета в токене будут помечены readonly")

class AuthResponse(BaseModel):
    """Информация об авторизации."""
    token: str = Field(description="Полученный JWT-токен")

class SubscribeJwtRenewalResponse(BaseModel):
    """Обновленный токен (стрим)."""
    token: str = Field(description="Полученный JWT-токен")