import logging
import os
import sys
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage

# Mevcut dizini path'e ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_settings
from db import get_collection
from main import app as graph_app

# PC Builder modülleri
from pc_builder.logic_engine import PCBuilderLogic
from pc_builder.graph import pc_graph
from pc_builder.models import (
    PartsResponse,
    PartItem,
    OptimizeRequest,
    OptimizeResponse,
    CompatibilityRequest,
    CompatibilityResponse,
    PCChatRequest,
    PCChatResponse,
)

logger = logging.getLogger(__name__)

api = FastAPI(title="Laptop Recommender API")

# CORS origin'lerini environment variable'dan oku, yoksa varsayılan dev sunucularını kullan
_default_origins = "http://localhost:5173,http://localhost:3000"
_cors_origins_raw = os.getenv("CORS_ORIGINS", _default_origins)
cors_origins: List[str] = [origin.strip() for origin in _cors_origins_raw.split(",") if origin.strip()]

# Vite, 5173 portu doluysa otomatik olarak 5174/5175... portuna kayar (örn. makinede
# başka bir dev sunucusu çalışıyorsa). Bu yüzden dev'de tüm localhost/127.0.0.1
# portlarına izin veren bir regex ekliyoruz — yalnızca yerel origin'ler eşleşir, harici
# origin'ler değil. Prod origin'leri için CORS_ORIGINS env değişkeni açıkça kullanılır.
_localhost_origin_regex = r"https?://(localhost|127\.0\.0\.1)(:\d+)?"
logger.info("CORS izin verilen origin'ler: %s (+ localhost regex)", cors_origins)

api.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=_localhost_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api.on_event("startup")
async def _warm_connections():
    """Atlas cold-start gecikmesini ortadan kaldırmak için ilk isteği beklemeden bağlanır
    ve optimize_build pipeline'ının ihtiyaç duyduğu performans index'lerini doğrular."""
    try:
        from pc_builder.mongo_client import get_db, ensure_performance_indexes
        db = get_db()
        db.command("ping")
        ensure_performance_indexes()
        logger.info("PC Builder Atlas ön-ısıtma + index kontrolü tamamlandı (buildcores_db)")
    except Exception as e:
        logger.warning("PC Builder Atlas ön-ısıtma başarısız (istek anında tekrar denenecek): %s", e)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    thread_id: str = Field(default="default", max_length=50)


class ChatResponse(BaseModel):
    reply: str


@api.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        logger.info("Chat isteği alındı, thread_id: %s", request.thread_id)
        config = {"configurable": {"thread_id": request.thread_id}}
        input_data = {"messages": [HumanMessage(content=request.message)]}

        final_state = await graph_app.ainvoke(input_data, config=config)

        messages = final_state.get("messages", [])
        if not messages:
            logger.warning("Asistandan yanıt alınamadı, thread_id: %s", request.thread_id)
            raise HTTPException(status_code=500, detail="Asistandan yanıt alınamadı")

        last_msg = messages[-1]
        if isinstance(last_msg, AIMessage):
            return ChatResponse(reply=last_msg.content)
        else:
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    return ChatResponse(reply=msg.content)

        return ChatResponse(reply="Üzgünüm, bir yanıt oluşturamadım.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Chat endpoint'inde hata: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Bir hata oluştu. Lütfen tekrar deneyin.")


_DEBUG_ENDPOINTS_ENABLED = os.getenv("ENABLE_DEBUG_ENDPOINTS", "").strip().lower() == "true"

if _DEBUG_ENDPOINTS_ENABLED:
    @api.get("/chat/history/{thread_id}")
    async def get_chat_history(thread_id: str):
        """Konusma gecmisini dondur — SADECE lokal debug icin. Prod'da kapali.

        Thread ID'ler Math.random ile üretiliyor (düşük entropi), kimlik doğrulama da
        olmadığı için bu endpoint tahmine açık IDOR riski taşır. Bu yüzden varsayılan
        olarak kapalıdır — yalnızca ENABLE_DEBUG_ENDPOINTS=true env flag'i ile açılır.
        """
        try:
            config = {"configurable": {"thread_id": thread_id}}
            state = await graph_app.aget_state(config)
            messages = state.values.get("messages", [])
            preferences = state.values.get("preferences", {})

            history = []
            for msg in messages:
                history.append({
                    "role": "user" if hasattr(msg, "type") and msg.type == "human" else "assistant",
                    "content": (msg.content or "")[:500],
                })

            return {
                "thread_id": thread_id,
                "message_count": len(messages),
                "preferences": preferences,
                "messages": history,
            }
        except Exception as e:
            logger.warning("Chat history debug endpoint hatası (thread_id=%s): %s", thread_id, e)
            raise HTTPException(status_code=500, detail="Geçmiş alınamadı.")


@api.get("/health")
def health():
    try:
        settings = get_settings()
        get_collection(settings).database.client.admin.command("ping")
        logger.info("Sağlık kontrolü başarılı, veritabanı bağlı")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.warning("Sağlık kontrolü: veritabanı bağlantısı yok - %s", e)
        return {"status": "degraded", "database": "disconnected"}


# ======================================================================
# PC Builder Endpoint'leri
# ======================================================================

_VALID_CATEGORIES = {"cpu", "gpu", "motherboard", "memory", "case", "psu", "storage", "cooler"}
pc_logic = PCBuilderLogic()


@api.get("/pc-builder/parts/{category}", response_model=PartsResponse)
def get_parts(category: str):
    """Kategori bazlı parça listesi döndürür."""
    cat = category.lower().strip()
    if cat not in _VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Geçersiz kategori: '{category}'. Geçerli kategoriler: {', '.join(sorted(_VALID_CATEGORIES))}",
        )

    parts = pc_logic.get_parts_by_category(cat)
    logger.info("PC Builder parça listesi istendi: %s (%d adet)", cat, len(parts))
    return PartsResponse(
        category=cat,
        count=len(parts),
        parts=[PartItem(**p) for p in parts],
    )


@api.post("/pc-builder/optimize", response_model=OptimizeResponse)
def optimize_build(request: OptimizeRequest):
    """Bütçe ve kullanım senaryosuna göre otomatik sistem toplar."""
    try:
        # Türkçe -> İngilizce kullanım senaryosu eşleştirmesi
        usage_map = {
            "oyun": "gaming",
            "game": "gaming",
            "mimarlık": "architecture",
            "mimarlik": "architecture",
            "render": "rendering",
            "video": "rendering",
            "ofis": "office",
            "genel": "general",
        }
        normalized_usage = usage_map.get(request.usage.lower(), request.usage.lower())

        # Custom allocation doğrulama
        parsed_allocations = None
        if request.custom_allocations and normalized_usage == "custom":
            total = sum(request.custom_allocations.values())
            if abs(total - 1.0) > 0.05:
                raise HTTPException(
                    status_code=400,
                    detail=f"Bütçe dağılımı toplamı {total:.2f} — 1.0 olmalı.",
                )
            parsed_allocations = request.custom_allocations

        result = pc_logic.optimize_build(request.budget, normalized_usage, parsed_allocations)
        selected = result.get("selected_components", {}) or {}
        build_names = {
            cat: (comp.get("name") or "?")
            for cat, comp in selected.items()
            if isinstance(comp, dict)
        }
        total_price = int(result.get("total_spend", 0) or 0)
        remaining_budget = int(result.get("remaining_budget", 0) or 0)

        compat = pc_logic.check_compatibility(selected) if selected else {"valid": True, "errors": [], "warnings": []}
        extra_warnings = result.get("warnings") or []
        if result.get("warning"):
            extra_warnings = [*extra_warnings, result["warning"]]

        compatibility_payload = {
            "valid": compat.get("valid", False),
            "errors": compat.get("errors", []),
            "warnings": [*compat.get("warnings", []), *extra_warnings],
        }

        logger.info(
            "PC Builder optimize sonucu: bütçe=%d, senaryo=%s, toplam=%d",
            request.budget,
            normalized_usage,
            total_price,
        )

        return OptimizeResponse(
            build=build_names,
            build_details=selected,
            total_price=total_price,
            remaining_budget=remaining_budget,
            compatibility=compatibility_payload,
            use_case=result.get("use_case", normalized_usage),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("PC Builder optimize hatası: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Sistem optimizasyonunda bir hata oluştu.")


@api.post("/pc-builder/compatibility", response_model=CompatibilityResponse)
def check_compatibility(request: CompatibilityRequest):
    """Seçilen parçaların uyumluluğunu kontrol eder."""
    try:
        # Geçerli kategori kontrolü
        for key in request.parts:
            if key not in _VALID_CATEGORIES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Geçersiz parça kategorisi: '{key}'. Geçerli: {', '.join(sorted(_VALID_CATEGORIES))}",
                )

        result = pc_logic.check_compatibility_by_names(request.parts)
        logger.info("PC Builder uyumluluk kontrolü: uyumlu=%s", result["valid"])

        return CompatibilityResponse(
            compatible=result["valid"],
            errors=result["errors"],
            warnings=result["warnings"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("PC Builder uyumluluk kontrolü hatası: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Uyumluluk kontrolünde bir hata oluştu.")


@api.post("/pc-builder/chat", response_model=PCChatResponse)
async def pc_chat(request: PCChatRequest):
    """PC Builder sohbet endpoint'i — LangGraph tabanlı asistan."""
    import time
    t_start = time.perf_counter()
    try:
        logger.info("PC Builder chat isteği, thread_id: %s", request.thread_id)
        config = {"configurable": {"thread_id": request.thread_id}}
        input_data = {"messages": [HumanMessage(content=request.message)]}

        final_state = await pc_graph.ainvoke(input_data, config=config)
        logger.info("PC Builder chat graph süresi=%.2fs thread_id=%s", time.perf_counter() - t_start, request.thread_id)

        messages = final_state.get("messages", [])
        if not messages:
            logger.warning("PC Builder asistanından yanıt alınamadı, thread_id: %s", request.thread_id)
            raise HTTPException(status_code=500, detail="PC Builder asistanından yanıt alınamadı.")

        # Graph state'inde optimize_build/select_component sonucu birikmiş bileşenler.
        # Frontend bu dict'i kullanarak parça panelini ve 3D sahneyi text parse'a
        # düşmeden günceller.
        selected = final_state.get("selected_components") or None
        total_price = None
        if isinstance(selected, dict) and selected:
            try:
                total_price = sum(int((c or {}).get("price") or 0) for c in selected.values())
            except (TypeError, ValueError):
                total_price = None

        # Son AI mesajını bul
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                return PCChatResponse(reply=msg.content, selected_components=selected, total_price=total_price)

        return PCChatResponse(reply="Üzgünüm, bir yanıt oluşturamadım.", selected_components=selected, total_price=total_price)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("PC Builder chat hatası: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Bir hata oluştu. Lütfen tekrar deneyin.")


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    uvicorn.run(api, host="0.0.0.0", port=8000)
