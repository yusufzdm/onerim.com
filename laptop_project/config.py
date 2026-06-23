import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str
    mongodb_db: str
    mongodb_collection: str
    openai_api_key: str
    openai_model: str
    max_fetch: int
    price_field: Optional[str]
    name_field: Optional[str]
    brand_field: Optional[str]


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning("Geçersiz tamsayı değeri: %s=%s, varsayılan kullanılıyor: %d", name, value, default)
        return default


@lru_cache()
def get_settings() -> Settings:
    logger.info("Uygulama ayarları yükleniyor")
    return Settings(
        mongodb_uri=os.getenv("MONGODB_URI", ""),
        mongodb_db=os.getenv("MONGODB_DB", ""),
        mongodb_collection=os.getenv("MONGODB_COLLECTION", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        max_fetch=_get_int("MAX_FETCH", 200),
        price_field=os.getenv("PRICE_FIELD"),
        name_field=os.getenv("NAME_FIELD"),
        brand_field=os.getenv("BRAND_FIELD"),
    )
