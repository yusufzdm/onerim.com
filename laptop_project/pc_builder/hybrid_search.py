"""
database/hybrid_search.py
MongoDB Vector Search ($vectorSearch) ile inventory $match (bütçe/stok) birleştiren
hibrit arama fonksiyonları.
"""

import logging
import os
import re
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))
from pc_builder.mongo_client import get_db

load_dotenv()

logger = logging.getLogger(__name__)

# Tool katmanından gelen filtre anahtarlarını `components` koleksiyonundaki gerçek
# alan adlarına eşler. Inventory'de socket/wattage/ram_type YOK; bu alanlar yalnızca
# components'te bulunur. Eşleme component_type'a göre değişir:
#   - memory (RAM modülü): RAM tipi TOP-LEVEL `ram_type` alanında.
#   - motherboard (anakart): RAM tipi NESTED `memory.ram_type` alanında.
# (Canlı dokümanlarla doğrulandı.)
_COMPONENT_FILTER_FIELD_MAP = {
    "motherboard": {"memory_type": "memory.ram_type"},
    "memory": {"memory_type": "ram_type"},
}


def _map_filter_field(component_type: str, key: str) -> str:
    """Tool-katmanı filtre anahtarını component_type'a uygun components alanına eşler."""
    return _COMPONENT_FILTER_FIELD_MAP.get(component_type, {}).get(key, key)

EMBEDDING_MODEL = "text-embedding-3-small"
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _get_query_embedding(query: str) -> list[float]:
    """Arama sorgusunu vektöre çevirir."""
    response = openai_client.embeddings.create(
        input=query,
        model=EMBEDDING_MODEL,
    )
    return response.data[0].embedding


def hybrid_search(
    query: str,
    component_type: str,
    max_price: Optional[int] = None,
    max_results: int = 5,
    ignore_stock: bool = False,
    filters: Optional[dict] = None,
) -> list[dict]:
    """
    Kategori bazında MongoDB Hybrid Search yapar.
    filters: {'socket': 'AM4', 'wattage': 650} gibi teknik kısıtlar.
    """
    query_embedding = _get_query_embedding(query)
    db = get_db()
    components_col = db["components"]

    # Vector search pre-filter: sadece index'te tanimli alanlar (component_type, is_in_stock)
    vs_filter = {"component_type": component_type}
    if not ignore_stock:
        vs_filter["is_in_stock"] = True

    # Post-filter: diger teknik filtreler ($match asamasinda)
    post_filter = {}
    if filters:
        for k, v in filters.items():
            if v:
                post_filter[k] = v
    # Memory: SO-DIMM (laptop RAM) hariç tut, masaüstü build varsayilan
    if component_type == "memory":
        post_filter["form_factor"] = {"$not": {"$regex": "SO.?DIMM", "$options": "i"}}

    if ignore_stock:
        # Araştırma Modu (Shopping yok). Laptop bileşenlerini referans modunda da gizle.
        ignore_stock_match = {**vs_filter, **post_filter, "is_laptop": {"$ne": True}}
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": 500,
                    "limit": max_results * 5,
                    "filter": vs_filter
                }
            },
            {"$match": ignore_stock_match},
            {"$project": {"embedding": 0, "description_text": 0, "_id": 0, "score": {"$meta": "vectorSearchScore"}}},
            {"$limit": max_results}
        ]
        return list(components_col.aggregate(pipeline))

    # Shopping Pipeline (Join'li, multi-retailer aware)
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": 1000,
                "limit": max_results * 10,
                "filter": vs_filter
            }
        },
        {"$match": {**vs_filter, **post_filter}} if post_filter else {"$match": vs_filter},
        {"$project": {"embedding": 0, "description_text": 0, "_id": 0, "score": {"$meta": "vectorSearchScore"}}},
        {
            "$lookup": {
                "from": "inventory",
                "localField": "component_id",
                "foreignField": "component_id",
                "as": "inventory_info",
            }
        },
        {"$unwind": "$inventory_info"},
        {
            "$addFields": {
                "price": "$inventory_info.price",
                "in_stock": "$inventory_info.in_stock",
                "url": "$inventory_info.url",
                "retailer": "$inventory_info.retailer",
                "is_accessory": "$inventory_info.is_accessory",
                "is_laptop_inv": "$inventory_info.is_laptop",
            }
        },
        {
            "$match": {
                "in_stock": True,
                "is_accessory": {"$ne": True},
                "is_laptop_inv": {"$ne": True},
                "is_laptop": {"$ne": True},  # components seviyesindeki flag
                **({"price": {"$lte": max_price}} if max_price is not None else {}),
            }
        },
        {"$project": {"inventory_info": 0}},
        # En ucuzu top-level'a koymak icin once price'a gore sirala
        {"$sort": {"price": 1}},
        # Component_id basina grupla: tum offer'lari topla, en ucuzu doc'a yaz
        {
            "$group": {
                "_id": "$component_id",
                "doc": {"$first": "$$ROOT"},
                "offers": {"$push": {
                    "retailer": "$retailer",
                    "price": "$price",
                    "url": "$url",
                }},
            }
        },
        # doc + offers'i tek seviyede birlestir (top-level'da en ucuz fiyat/url/retailer)
        {"$replaceRoot": {"newRoot": {"$mergeObjects": ["$doc", {"offers": "$offers"}]}}},
        # Vektor skoruna gore sirala (orijinal alaka sirasi)
        {"$sort": {"score": -1}},
        {"$limit": max_results},
    ]

    try:
        results = list(components_col.aggregate(pipeline))
        return results
    except Exception as e:
        logger.warning("Vector Search hatası: %s", e)
        return []


def _build_components_match(query: str, component_type: str, filters: Optional[dict]) -> dict:
    """`components` koleksiyonu için $match dokümanı kurar.

    Teknik filtreler (socket, ram_type, wattage ...) DOĞRUDAN components alanlarına
    uygulanır — inventory'de bu alanlar yoktur. `memory_type` gibi tool-katmanı
    anahtarları gerçek components alan adına eşlenir. Query verildiğinde isim
    (`name` veya `metadata.name`) üzerinde case-insensitive regex eklenir.
    """
    match: dict = {"component_type": component_type, "is_laptop": {"$ne": True}}

    if filters:
        for k, v in filters.items():
            if v is None or v == "":
                continue
            field = _map_filter_field(component_type, k)
            match[field] = v

    if query and query.strip():
        # Query terimi hem name hem metadata.name'de aransın (components'te ikisi de var)
        pattern = re.escape(query.strip())
        match["$or"] = [
            {"name": {"$regex": pattern, "$options": "i"}},
            {"metadata.name": {"$regex": pattern, "$options": "i"}},
        ]

    # Memory: SO-DIMM (laptop RAM) hariç tut — masaüstü build varsayılan.
    if component_type == "memory":
        match["form_factor"] = {"$not": {"$regex": "SO.?DIMM", "$options": "i"}}

    return match


def text_search(
    query: str,
    component_type: str,
    max_price: Optional[int] = None,
    max_results: int = 5,
    ignore_stock: bool = False,
    filters: Optional[dict] = None,
) -> list[dict]:
    """Fallback (vector index yokken): `components` üzerinde regex + teknik filtre,
    ardından `inventory` join'i ile stok/fiyat/multi-retailer.

    `hybrid_search`'in kanıtlanmış post-lookup yapısını taklit eder; tek fark ilk
    aşamanın $vectorSearch yerine components üzerinde $match olmasıdır. Çıktı şekli
    `hybrid_search` ile aynıdır (name, socket, price, offers[], url, retailer,
    component_id) — _format_results ve çoklu-perakendeci karşılaştırması bozulmaz.
    """
    db = get_db()
    components_col = db["components"]
    comp_match = _build_components_match(query, component_type, filters)

    if ignore_stock:
        # Araştırma Modu (Shopping yok): components'te regex, stok join'siz.
        ref_match = dict(comp_match)
        return list(
            components_col.find(ref_match, {"embedding": 0, "description_text": 0, "_id": 0})
            .limit(max_results)
        )

    pipeline = _build_text_pipeline(comp_match, max_price, max_results)
    results = list(components_col.aggregate(pipeline))
    if not results and query and query.strip():
        # Query regex hiç eşleşmediyse (ör. doğal dil sorgusu isimle birebir uymuyor),
        # teknik filtreleri koru ama regex'i düşür — socket/ram_type vb. yine geçerli.
        fallback_match = _build_components_match("", component_type, filters)
        results = list(components_col.aggregate(_build_text_pipeline(fallback_match, max_price, max_results)))
    return results


def _build_text_pipeline(comp_match: dict, max_price: Optional[int], max_results: int) -> list:
    """components → inventory join'li pipeline. Stok/fiyat inventory'den; teknik
    alanlar (socket vb.) components'ten gelir. Grouping/offers/replaceRoot mantığı
    `hybrid_search`'teki Shopping Pipeline ile birebir aynıdır."""
    return [
        {"$match": comp_match},
        {"$project": {"embedding": 0, "description_text": 0, "_id": 0}},
        {
            "$lookup": {
                "from": "inventory",
                "localField": "component_id",
                "foreignField": "component_id",
                "as": "inventory_info",
            }
        },
        {"$unwind": "$inventory_info"},
        {
            "$addFields": {
                "price": "$inventory_info.price",
                "in_stock": "$inventory_info.in_stock",
                "url": "$inventory_info.url",
                "retailer": "$inventory_info.retailer",
                "retailer_title": "$inventory_info.retailer_title",
                "is_accessory": "$inventory_info.is_accessory",
                "is_laptop_inv": "$inventory_info.is_laptop",
            }
        },
        {
            "$match": {
                "in_stock": True,
                "is_accessory": {"$ne": True},
                "is_laptop_inv": {"$ne": True},
                "is_laptop": {"$ne": True},  # components seviyesindeki flag
                **({"price": {"$lte": max_price}} if max_price is not None else {}),
            }
        },
        {"$project": {"inventory_info": 0}},
        # En ucuzu top-level'a koymak için önce price'a göre sırala
        {"$sort": {"price": 1}},
        # Component_id başına grupla: tüm offer'ları topla, en ucuzu doc'a yaz
        {
            "$group": {
                "_id": "$component_id",
                "doc": {"$first": "$$ROOT"},
                "offers": {"$push": {
                    "retailer": "$retailer",
                    "price": "$price",
                    "url": "$url",
                }},
            }
        },
        # doc + offers'i tek seviyede birleştir (top-level'da en ucuz fiyat/url/retailer)
        {"$replaceRoot": {"newRoot": {"$mergeObjects": ["$doc", {"offers": "$offers"}]}}},
        # En ucuz fiyat sırasına göre (vektör skoru yok; fiyat artan mantıklı varsayılan)
        {"$sort": {"price": 1}},
        {"$limit": max_results},
    ]


def safe_search(
    query: str,
    component_type: str,
    max_price: Optional[int] = None,
    max_results: int = 5,
    ignore_stock: bool = False,
    filters: Optional[dict] = None,
) -> list[dict]:
    """Tüm aramalarda teknik filtre desteği."""
    try:
        results = hybrid_search(query, component_type, max_price, max_results, ignore_stock, filters)
        if results:
            return results
        return text_search(query, component_type, max_price, max_results, ignore_stock, filters)
    except Exception as e:
        return text_search(query, component_type, max_price, max_results, ignore_stock, filters)


if __name__ == "__main__":
    # Hızlı test
    logging.basicConfig(level=logging.INFO)
    logger.info("Hybrid Search Testi...")
    results = safe_search("GeForce RTX 4070", "gpu")
    for r in results:
        logger.info("  • %s — %s TL", r.get("name"), r.get("price", "STOKTA YOK"))
