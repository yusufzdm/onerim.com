import logging
import re
from typing import Any, Dict, Iterable, List, Optional

from config import Settings
from db import get_collection

logger = logging.getLogger(__name__)


def _get_first(doc: Dict[str, Any], keys: Iterable[str]) -> Optional[Any]:
    for key in keys:
        if key in doc and doc[key] is not None:
            return doc[key]
    return None


def _to_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).lower().replace(",", ".")
    match = re.search(r"\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def _parse_gb(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).lower()
    number = _to_number(text)
    if number is None:
        return None
    if "tb" in text:
        return number * 1024
    return number


def _parse_weight_kg(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).lower()
    number = _to_number(text)
    if number is None:
        return None
    if "g" in text and "kg" not in text:
        return number / 1000
    return number


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _cpu_score(cpu_name: Optional[str]) -> float:
    if not cpu_name:
        return 0.4
    s = cpu_name.lower()
    if any(x in s for x in ["celeron", "pentium", "athlon", "atom"]):
        return 0.2
    if re.search(r"\bn\d{3,4}\b", s):
        return 0.2
    if any(x in s for x in ["silver", "gold"]):
        return 0.25
    if any(x in s for x in ["i9", "ryzen 9", "ultra 9"]):
        return 1.0
    if any(x in s for x in ["i7", "ryzen 7", "ultra 7"]):
        return 0.8
    if any(x in s for x in ["i5", "ryzen 5", "ultra 5"]):
        return 0.6
    if any(x in s for x in ["i3", "ryzen 3", "ultra 3"]):
        return 0.4
    return 0.5


def _gpu_score(gpu_name: Optional[str]) -> float:
    if not gpu_name:
        return 0.2
    s = gpu_name.lower()
    if any(x in s for x in ["rtx 4090", "rtx 4080", "rtx 4070 ti", "rx 7900", "rx 7800"]):
        return 1.0
    if any(x in s for x in ["rtx 4070", "rtx 4060", "rx 7700", "rx 7600", "arc a770", "arc a750"]):
        return 0.8
    if any(x in s for x in ["rtx 4050", "rtx 3060", "rtx 3050", "rx 6600", "gtx 1660", "quadro", "arc"]):
        return 0.6
    if "radeon" in s and "rx" not in s and "pro" not in s:
        return 0.3
    if any(
        x in s
        for x in [
            "gtx 1650",
            "gtx 1050",
            "mx",
            "iris",
            "uhd",
            "hd graphics",
            "integrated",
            "paylasimli",
            "shared",
            "radeon graphics",
            "vega",
        ]
    ):
        return 0.3
    return 0.4


def _has_discrete_gpu(gpu_name: Optional[str]) -> bool:
    if not gpu_name:
        return False
    s = gpu_name.lower()
    # Once entegre GPU'lari filtrele (paylasimli, integrated, igpu vb.)
    if any(x in s for x in ["paylaşımlı", "paylasimli", "integrated", "igpu", "shared"]):
        return False
    if any(x in s for x in ["iris", "uhd", "hd graphics", "radeon graphics", "vega"]):
        return False
    # Discrete GPU'lar
    if any(x in s for x in ["rtx", "gtx", "rx ", "quadro", "radeon pro", "mx"]):
        return True
    # Arc A serisi discrete (A770, A750, A580) ama Arc Graphics entegre
    if "arc" in s and any(x in s for x in ["a770", "a750", "a580", "a380", "a310"]):
        return True
    return False


def _has_rtx(gpu_name: Optional[str]) -> bool:
    if not gpu_name:
        return False
    return "rtx" in gpu_name.lower()


def _extract_brand(name: str) -> Optional[str]:
    if not name:
        return None
    cleaned = re.sub(r"[^A-Za-z0-9\-\s]", " ", name).strip()
    if not cleaned:
        return None
    return cleaned.split()[0]


def _find_prop(props: Dict[str, Any], keyword: str) -> Optional[Any]:
    if not props:
        return None
    for key, value in props.items():
        if keyword.lower() in key.lower():
            return value
    return None


def _normalize_doc(doc: Dict[str, Any], settings: Settings) -> Dict[str, Any]:
    name_keys = [k for k in [settings.name_field, "name", "model", "title", "urun_adi"] if k]
    brand_keys = [k for k in [settings.brand_field, "brand", "manufacturer", "vendor"] if k]
    price_keys = [k for k in [settings.price_field, "price", "price_try", "price_tl", "price_usd", "fiyat"] if k]

    name = _get_first(doc, name_keys) or "Unknown Model"
    brand = _get_first(doc, brand_keys)
    price = _to_number(_get_first(doc, price_keys))
    url = doc.get("url")

    cpu = _get_first(doc, ["cpu", "processor", "cpu_name"])
    gpu = _get_first(doc, ["gpu", "graphics", "gpu_name", "graphics_card"])
    ram = _parse_gb(_get_first(doc, ["ram", "ram_gb", "memory", "memory_gb"]))
    storage = _parse_gb(_get_first(doc, ["storage", "storage_gb", "ssd", "hdd", "disk", "capacity"]))
    screen = _to_number(_get_first(doc, ["screen_size", "display", "display_size", "screen"]))
    weight = _parse_weight_kg(_get_first(doc, ["weight", "weight_kg"]))
    battery = _to_number(_get_first(doc, ["battery_wh", "battery", "battery_capacity"]))

    props = doc.get("ozellikler") if isinstance(doc.get("ozellikler"), dict) else {}
    if props:
        cpu_mark = props.get("İşlemci Markası")
        cpu_tech = props.get("İşlemci Teknolojisi")
        cpu_num = props.get("İşlemci Numarası")
        cpu_parts = [p for p in [cpu_mark, cpu_tech, cpu_num] if p and p != "-"]
        if cpu_parts:
            cpu = " ".join(cpu_parts)

        gpu_chip = props.get("Ekran Kartı Chipseti") or props.get("Ekran Kartı Chipset Marka")
        gpu_mem = props.get("Ekran Kartı Hafızası")
        if gpu_chip and gpu_mem and gpu_mem != "-":
            gpu = f"{gpu_chip} {gpu_mem}"
        elif gpu_chip:
            gpu = gpu_chip

        ram = ram or _parse_gb(props.get("Ram (Sistem Belleği)"))
        storage = storage or _parse_gb(props.get("Disk Kapasitesi"))
        screen = screen or _to_number(props.get("Ekran Boyutu (inch)"))
        weight = weight or _parse_weight_kg(_find_prop(props, "Ağırlığı"))
        battery = battery or _to_number(_find_prop(props, "Pil"))

    if not brand and isinstance(name, str):
        brand = _extract_brand(name)

    # Resim URL'lerini al (MongoDB'de images array'i varsa)
    images = doc.get("images")
    image = None
    if isinstance(images, list) and images:
        image = images[0]
    elif isinstance(doc.get("image"), str) and doc.get("image"):
        image = doc["image"]

    return {
        "name": str(name),
        "brand": str(brand) if brand is not None else None,
        "price": price,
        "cpu": cpu,
        "gpu": gpu,
        "ram_gb": ram,
        "storage_gb": storage,
        "screen_size": screen,
        "weight_kg": weight,
        "battery_wh": battery,
        "usage_hint": props.get("Kullanım Amacı") if props else None,
        "url": url,
        "image": image,
        "raw": doc,
    }


def _build_dynamic_weights(prefs: Dict[str, Any]) -> Dict[str, float]:
    """LLM'in dondurdugu priority_order'dan dinamik agirlik olusturur."""
    priority = prefs.get("priority_order")

    if not priority or not isinstance(priority, list):
        # Fallback: usage'a gore varsayilan siralar
        usage = prefs.get("usage") or "general"
        fallbacks = {
            "gaming": ["gpu", "cpu", "ram", "storage", "price"],
            "render": ["gpu", "cpu", "ram", "storage", "price"],
            "design": ["gpu", "cpu", "ram", "screen", "price"],
            "programming": ["cpu", "ram", "storage", "battery", "weight", "price"],
            "student": ["price", "battery", "weight", "ram", "storage"],
            "office": ["cpu", "ram", "price", "battery", "weight"],
            "general": ["cpu", "ram", "storage", "price", "battery"],
        }
        priority = fallbacks.get(usage, fallbacks["general"])

    # Siradaki her ozellige azalan agirlik ver
    weights = {}
    n = len(priority)
    total = 0.0
    for i, key in enumerate(priority):
        w = max(0.05, (n - i) / n)
        weights[key] = w
        total += w

    # weight_importance ve battery_importance boost
    if prefs.get("weight_importance") == "high":
        weights["weight"] = weights.get("weight", 0) + 0.3
        total += 0.3
    elif prefs.get("weight_importance") == "medium":
        weights["weight"] = weights.get("weight", 0) + 0.1
        total += 0.1

    if prefs.get("battery_importance") == "high":
        weights["battery"] = weights.get("battery", 0) + 0.3
        total += 0.3
    elif prefs.get("battery_importance") == "medium":
        weights["battery"] = weights.get("battery", 0) + 0.1
        total += 0.1

    # Normalize et (toplam = 1.0)
    if total > 0:
        weights = {k: v / total for k, v in weights.items()}

    return weights


# GPU tier seviyeleri — ust seviyeler alt seviyeleri de icerir
_GPU_TIER_CHIPS = {
    "high": ["rtx 4070", "rtx 4080", "rtx 4090", "rtx 5070", "rtx 5080", "rtx 5090", "rx 7800", "rx 7900", "rx 9070"],
    "mid-high": ["rtx 4050", "rtx 4060", "rtx 3060", "rtx 3070", "rtx 5050", "rtx 5060", "rx 7600", "rx 7700"],
    "mid": ["gtx 1650", "gtx 1660", "rtx 3050", "mx 550", "mx 570", "rx 6600"],
    "entry": [],  # herhangi discrete GPU
}


def _meets_gpu_tier(gpu_name: Optional[str], min_tier: str) -> bool:
    """Laptop'un GPU'su minimum tier'i karsilar mi?"""
    if min_tier in ("any", "integrated", None, ""):
        return True

    if not _has_discrete_gpu(gpu_name):
        return False

    if min_tier == "entry":
        return True  # discrete GPU yeterli

    s = (gpu_name or "").lower()

    # Tier'e gore gecerli GPU'lar: o seviye + ust seviyeler
    tiers_order = ["mid", "mid-high", "high"]
    start_idx = tiers_order.index(min_tier) if min_tier in tiers_order else 0
    valid_chips = []
    for tier in tiers_order[start_idx:]:
        valid_chips.extend(_GPU_TIER_CHIPS[tier])

    return any(chip in s for chip in valid_chips)


def _score_laptop(laptop: Dict[str, Any], prefs: Dict[str, Any]) -> float:
    budget = prefs.get("budget_max")
    price = laptop.get("price")
    price_score = 0.5
    if budget and price:
        if prefs.get("price_focus"):
            # Ucuz olan daha iyi (ogrenci modu)
            price_score = _clamp((budget - price) / budget)
        else:
            # Butcenin %60-100 arasi en iyi puan, altinda ve ustunde duser
            ratio = price / budget
            if ratio <= 1.0 and ratio >= 0.6:
                price_score = 0.7 + 0.3 * ((ratio - 0.6) / 0.4)  # 0.6->0.7, 1.0->1.0
            elif ratio < 0.6:
                price_score = ratio  # Cok ucuz = dusuk puan (muhtemelen dusuk spec)
            else:
                price_score = max(0, 1.0 - (ratio - 1.0) * 2)  # Butce ustu cezali

    features = {
        "cpu": _cpu_score(laptop.get("cpu")),
        "gpu": _gpu_score(laptop.get("gpu")),
        "ram": _clamp((laptop.get("ram_gb") or 0) / 32),
        "storage": _clamp((laptop.get("storage_gb") or 0) / 1024),
        "battery": _clamp((laptop.get("battery_wh") or 0) / 80),
        "weight": _clamp((3.0 - (laptop.get("weight_kg") or 3.0)) / 3.0),
        "screen": _clamp(((laptop.get("screen_size") or 15.6) - 12) / 6.0),
        "price": price_score,
    }

    # Dinamik agirliklar — LLM'in priority_order'indan uretilir
    w = _build_dynamic_weights(prefs)

    score = sum(features.get(key, 0) * weight for key, weight in w.items())

    usage = prefs.get("usage") or ""
    usage_hint = (laptop.get("usage_hint") or "").lower()
    if usage_hint and usage in usage_hint:
        score += 0.05

    return score


def _matches_filters(laptop: Dict[str, Any], prefs: Dict[str, Any]) -> bool:
    budget = prefs.get("budget_max")
    if budget is not None:
        price = laptop.get("price")
        if price is not None and price > budget:
            return False

    # Tum alanlari tek string'e cevir — brand/excluded filtresi icin
    all_text = " ".join(
        str(v) for v in laptop.values()
        if isinstance(v, (str, int, float)) and v
    ).lower()

    brand = prefs.get("brand")
    if brand and brand.lower() not in all_text:
        return False

    excluded = prefs.get("excluded_brands")
    if excluded and isinstance(excluded, list):
        for ex in excluded:
            if ex.lower() in all_text:
                return False

    min_ram = prefs.get("min_ram_gb")
    if min_ram is not None:
        if (laptop.get("ram_gb") or 0) < min_ram:
            return False

    min_storage = prefs.get("min_storage_gb")
    if min_storage is not None:
        if (laptop.get("storage_gb") or 0) < min_storage:
            return False

    screen_min = prefs.get("screen_size_min")
    if screen_min is not None:
        if (laptop.get("screen_size") or 0) < screen_min:
            return False

    screen_max = prefs.get("screen_size_max")
    if screen_max is not None:
        if (laptop.get("screen_size") or 99) > screen_max:
            return False

    weight_max = prefs.get("weight_max_kg")
    if weight_max is not None:
        if (laptop.get("weight_kg") or 99) > weight_max:
            return False

    # GPU tier filtresi — min_gpu_tier varsa kullan, yoksa gpu_required'a fallback
    min_gpu_tier = prefs.get("min_gpu_tier")
    if min_gpu_tier and min_gpu_tier not in ("any", "integrated"):
        if not _meets_gpu_tier(laptop.get("gpu"), min_gpu_tier):
            return False
    elif prefs.get("gpu_required"):
        if not _has_discrete_gpu(laptop.get("gpu")):
            return False

    return True


def _usage_label(usage: Optional[str]) -> str:
    labels = {
        "gaming": "Oyun",
        "design": "Tasarım",
        "render": "Render",
        "programming": "Yazılım",
        "student": "Öğrenci",
        "office": "Ofis",
        "general": "Genel",
    }
    return labels.get(usage or "general", "Genel")



def _build_intro(prefs: Dict[str, Any], laptops: List[Dict[str, Any]]) -> str:
    usage = prefs.get("usage")
    budget = prefs.get("budget_max")
    if usage and budget is not None:
        intro = f"{_usage_label(usage)} için bütçeniz {int(budget)} TL ve öncelikli ihtiyaç olarak anladım."
    elif usage:
        intro = f"{_usage_label(usage)} için öncelikli ihtiyaç olarak anladım."
    elif budget is not None:
        intro = f"Bütçeniz {int(budget)} TL olarak anladım."
    else:
        intro = "İhtiyacınızı anladım."
    follow = "Bu bütçe ve kullanıma göre en uygun laptopları filtreleyip öneriyorum."

    notes = []
    if prefs.get("price_focus"):
        notes.append("En uygun fiyatlı modelleri önceliklendirdim.")
    if usage in ["render", "design"]:
        rtx_count = sum(1 for item in laptops if _has_rtx(item.get("gpu")))
        if rtx_count == 0:
            notes.append(
                "Veritabanında bu bütçede RTX gibi güçlü ekran kartlı modeller bulunamadı. "
                "Ancak işlemci, bellek ve SSD kapasitesiyle temel render ve diğer işler için uygun modeller var."
            )
    if usage == "gaming":
        dgpu_count = sum(1 for item in laptops if _has_discrete_gpu(item.get("gpu")))
        if dgpu_count == 0:
            notes.append(
                "Bu bütçede harici ekran kartlı oyun odaklı modeller bulunamadı. "
                "Yine de genel oyunlar için uygun alternatifler listelendi."
            )

    if notes:
        return f"{intro} {follow}\n" + "\n".join(notes)
    return f"{intro} {follow}"


def _build_reasons(laptop: Dict[str, Any], prefs: Dict[str, Any]) -> List[str]:
    reasons = []
    price = laptop.get("price")
    budget = prefs.get("budget_max")

    if prefs.get("price_focus"):
        if price is not None:
            reasons.append("En uygun fiyatlı modellere yakın bir seçenek, fiyat/performans odaklı.")
        else:
            reasons.append("Fiyat odaklı filtreye uygun bir model.")

    if budget is not None and price is not None:
        if price <= budget * 0.9:
            reasons.append("Bütçenin belirgin altında, fiyat/performans dengesi iyi.")
        elif price <= budget:
            reasons.append("Bütçeyi aşmadan daha iyi donanıma çıkma şansı veriyor.")

    usage = prefs.get("usage") or "general"
    ram_gb = laptop.get("ram_gb") or 0
    storage_gb = laptop.get("storage_gb") or 0
    weight_kg = laptop.get("weight_kg") or 99
    battery_wh = laptop.get("battery_wh") or 0
    gpu_name = laptop.get("gpu")
    cpu_name = laptop.get("cpu")

    if usage == "gaming":
        if _has_discrete_gpu(gpu_name):
            reasons.append("Harici GPU, oyunlarda daha stabil ve yüksek kare hızları sağlar.")
        if ram_gb >= 16:
            reasons.append("16GB RAM, yeni oyunlarda takılmayı azaltır.")
    elif usage in ["design", "render"]:
        if _has_rtx(gpu_name):
            reasons.append("RTX GPU, render/tasarım uygulamalarında hızlandırma sağlar.")
        elif _has_discrete_gpu(gpu_name):
            reasons.append("Harici GPU, render/tasarım işlerinde paylaşımlı GPU'ya göre daha stabil performans verir.")
        if ram_gb >= 16:
            reasons.append("16GB RAM, büyük projelerde bellek darboğazını azaltır.")
    elif usage in ["programming", "student", "office"]:
        if ram_gb >= 16:
            reasons.append("16GB RAM, çoklu uygulamada akıcı çalışma sağlar.")
        if storage_gb >= 512:
            reasons.append("512GB depolama, proje ve dosyalar için daha rahat alan sunar.")
        if weight_kg <= 1.6:
            reasons.append("Hafif tasarım, taşımayı kolaylaştırır.")
        if battery_wh >= 50:
            reasons.append("Daha uzun pil ömrü, gün içinde priz bağımlılığını azaltır.")
    else:
        if ram_gb >= 16:
            reasons.append("16GB RAM, genel kullanımda daha uzun ömür ve akıcılık sağlar.")

    if cpu_name:
        cpu_sc = _cpu_score(cpu_name)
        if cpu_sc >= 0.8:
            reasons.append("Güçlü işlemci sınıfı, ağır işlerde daha hızlı tamamlanma sağlar.")
        elif cpu_sc >= 0.6:
            reasons.append("Orta-üst seviye işlemci, performans ve fiyat dengesini iyi kurar.")
        elif cpu_sc > 0:
            reasons.append("Günlük işlemler için yeterli işlemci, temel ihtiyacı karşılar.")

    if storage_gb >= 512:
        reasons.append("512GB ve üzeri depolama, sistemin çabuk dolmasını engeller.")

    if len(reasons) < 2:
        if usage in ["gaming", "render", "design"]:
            reasons.append("Bu bütçe aralığında dengeli performans sunan alternatiflerden biri.")
        else:
            reasons.append("Günlük kullanım için fiyat/performans dengesi iyi.")

    if not reasons:
        reasons.append("Genel kullanım için dengeli bir seçim.")

    return reasons[:3]


def _build_specs(laptop: Dict[str, Any]) -> str:
    props = laptop.get("raw", {}).get("ozellikler", {}) if isinstance(laptop.get("raw"), dict) else {}
    specs = []

    screen = props.get("Ekran Boyutu (inch)") or laptop.get("screen_size")
    if screen:
        screen_text = str(screen)
        if "inch" in screen_text.lower():
            specs.append(f"{screen_text} ekran")
        else:
            specs.append(f"{screen_text} inch ekran")

    resolution = props.get("Çözünürlük (Piksel)") or props.get("Ekran")
    if resolution and resolution != "-":
        specs.append(f"{resolution}")

    ram = props.get("Ram (Sistem Belleği)") or (
        f"{int(laptop.get('ram_gb'))} GB" if laptop.get("ram_gb") else None
    )
    if ram:
        specs.append(f"{ram} RAM")

    gpu = laptop.get("gpu")
    if gpu:
        specs.append(f"{gpu} GPU")

    storage = props.get("Disk Kapasitesi") or (
        f"{int(laptop.get('storage_gb'))} GB" if laptop.get("storage_gb") else None
    )
    if storage:
        disk_type = props.get("Disk Türü")
        if disk_type and disk_type != "-":
            specs.append(f"{storage} {disk_type}")
        else:
            specs.append(f"{storage} Depolama")

    os_name = props.get("İşletim Sistemi")
    if os_name and os_name != "-":
        specs.append(os_name)

    return ", ".join(specs)


def format_markdown_with_reasons(
    laptops: List[Dict[str, Any]],
    prefs: Dict[str, Any],
    reasons_by_index: Optional[Dict[Any, str]] = None,
) -> str:
    if not laptops:
        return "Uygun laptop bulunamadı. Bütçeyi artırmak veya kriterleri gevşetmek ister misin?"

    lines = [_build_intro(prefs, laptops), ""]
    for idx, item in enumerate(laptops, start=1):
        # Resim URL'i varsa marker olarak ekle (frontend parse edecek)
        if item.get("image"):
            lines.append(f"[IMG:{item['image']}]")
        lines.append(f"### {idx}) {item.get('name')}")
        if item.get("price") is not None:
            lines.append(f"Fiyat: {int(item.get('price'))} TL")
        if item.get("url"):
            lines.append(f"🔗 Ürünü İncele: {item.get('url')}")

        reason_text = None
        if reasons_by_index:
            reason_text = (
                reasons_by_index.get(str(idx))
                or reasons_by_index.get(idx)
                or reasons_by_index.get(item.get("name"))
            )
        if not reason_text:
            reasons = _build_reasons(item, prefs)
            if reasons:
                reason_text = " ".join(reasons)
        if reason_text:
            lines.append(f"Neden uygun? {reason_text}")

        specs = _build_specs(item)
        if specs:
            lines.append(f"Özellikler: {specs}")
        lines.append("")
    followup = _build_followup(prefs)
    if followup:
        lines.append(followup)
    return "\n".join(lines).strip()


def _build_followup(prefs: Dict[str, Any]) -> str:
    usage = prefs.get("usage")
    if usage == "render":
        return "Render için hangi programları kullanıyorsunuz? Taşıma kolaylığı sizin için önemli mi?"
    if usage == "gaming":
        return "Hangi oyunları oynuyorsunuz ve taşınabilirlik sizin için önemli mi?"
    return ""

def recommend_laptops_data(preferences: Dict[str, Any], settings: Settings) -> List[Dict[str, Any]]:
    logger.info("Laptop önerisi hesaplanıyor, tercihler: %s", preferences)

    collection = get_collection(settings)
    cursor = collection.find({})
    if settings.max_fetch:
        cursor = cursor.limit(settings.max_fetch)

    docs = list(cursor)
    logger.info("Veritabanından %d döküman çekildi", len(docs))
    normalized = [_normalize_doc(doc, settings) for doc in docs]

    filtered = [item for item in normalized if _matches_filters(item, preferences)]

    # GPU tier ile az sonuc donerse, bir alt tier'e gevset
    # Ama design/gaming/render icin asla "any"/"integrated"e dusurme
    min_tier = preferences.get("min_gpu_tier")
    usage = preferences.get("usage")
    tier_order = ["high", "mid-high", "mid", "entry", "any"]
    # GPU gerektiren usage'larda minimum "entry" (discrete GPU)
    min_floor = "entry" if usage in ("gaming", "render", "design") else "any"
    floor_idx = tier_order.index(min_floor)

    if len(filtered) < 3 and min_tier in tier_order:
        tier_idx = tier_order.index(min_tier)
        while len(filtered) < 3 and tier_idx < floor_idx:
            tier_idx += 1
            preferences["min_gpu_tier"] = tier_order[tier_idx]
            filtered = [item for item in normalized if _matches_filters(item, preferences)]
            logger.info("GPU tier gevşetildi: %s → %d sonuç", tier_order[tier_idx], len(filtered))
    logger.info("Filtreleme sonrası %d laptop kaldı", len(filtered))
    scored = [dict(item, score=_score_laptop(item, preferences)) for item in filtered]

    if preferences.get("price_focus"):
        scored.sort(key=lambda x: (x["price"] is None, x["price"], -x["score"]))
    else:
        scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:3]
