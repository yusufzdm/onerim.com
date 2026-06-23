import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.collection import Collection

from config import Settings

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None


def get_collection(settings: Settings) -> Collection:
    global _client
    if not settings.mongodb_uri or not settings.mongodb_db or not settings.mongodb_collection:
        logger.error("MongoDB ayarları eksik. MONGODB_URI/DB/COLLECTION kontrol edin.")
        raise ValueError("MongoDB ayarları eksik. MONGODB_URI/DB/COLLECTION kontrol edin.")

    if _client is None:
        logger.info("MongoDB bağlantısı kuruluyor: %s", settings.mongodb_db)
        _client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)

    db = _client[settings.mongodb_db]
    return db[settings.mongodb_collection]
