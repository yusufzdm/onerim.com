"""Pydantic request/response modelleri — PC Builder API endpoint'leri için."""

from typing import Optional

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# GET /pc-builder/parts/{category}
# ------------------------------------------------------------------

class PartItem(BaseModel):
    id: str
    name: str
    price: int
    # Ek alanlar kategoriye göre değişir, bu yüzden extra izin veriyoruz

    model_config = {"extra": "allow"}


class PartsResponse(BaseModel):
    category: str
    count: int
    parts: list[PartItem]


# ------------------------------------------------------------------
# POST /pc-builder/optimize
# ------------------------------------------------------------------

class OptimizeRequest(BaseModel):
    budget: int = Field(..., ge=5000, le=500000, description="Toplam bütçe (TL)")
    usage: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Kullanım senaryosu: gaming, architecture, rendering, office, general",
    )
    custom_allocations: Optional[dict[str, float]] = Field(
        default=None,
        description="Özel bütçe dağılımı (sadece usage='custom' için). Toplam 1.0 olmalı.",
    )


class OptimizeBuildItem(BaseModel):
    kategori: str
    ürün: str = Field(..., alias="urun")
    fiyat: int

    model_config = {"populate_by_name": True}


class OptimizeResponse(BaseModel):
    build: dict[str, str]
    build_details: dict = {}
    total_price: int
    remaining_budget: int
    compatibility: dict
    use_case: str


# ------------------------------------------------------------------
# POST /pc-builder/compatibility
# ------------------------------------------------------------------

class CompatibilityRequest(BaseModel):
    parts: dict[str, str] = Field(
        ...,
        min_length=1,
        description="Parça sözlüğü: {'cpu': '...', 'motherboard': '...', ...}",
    )


class CompatibilityResponse(BaseModel):
    compatible: bool
    errors: list[str]
    warnings: list[str]


# ------------------------------------------------------------------
# POST /pc-builder/chat
# ------------------------------------------------------------------

class PCChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    thread_id: str = Field(default="pc-default", max_length=50)


class PCChatResponse(BaseModel):
    reply: str
    # Frontend, parça listesini ve 3D sahneyi güncellerken markdown'ı parse etmek
    # yerine doğrudan graph state'inden gelen yapılandırılmış component dict'i kullanır.
    selected_components: Optional[dict] = None
    total_price: Optional[int] = None
