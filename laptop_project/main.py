import json
import logging
import re
from typing import Annotated, Dict
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from config import get_settings
from prompts import INTENT_PROMPT, REASON_PROMPT
from recommender import recommend_laptops_data, format_markdown_with_reasons

logger = logging.getLogger(__name__)

settings = get_settings()

if not settings.openai_api_key:
    raise ValueError("OPENAI_API_KEY .env dosyasında bulunamadı. Lütfen ayarlayın.")


def _merge_preferences(existing: Dict, new_data: Dict) -> Dict:
    if existing is None:
        existing = {}
    if new_data:
        for key, value in new_data.items():
            if value is not None and value != "":
                existing[key] = value

        # Celiskileri temizle: brand degistiyse, excluded_brands'ten cikar
        brand = existing.get("brand")
        excluded = existing.get("excluded_brands")
        if brand and excluded and isinstance(excluded, list):
            existing["excluded_brands"] = [e for e in excluded if e.lower() != brand.lower()]
            if not existing["excluded_brands"]:
                existing["excluded_brands"] = None

    return existing


class State(TypedDict):
    messages: Annotated[list, add_messages]
    preferences: Annotated[dict, _merge_preferences]
    needs_budget: bool


llm = ChatOpenAI(model=settings.openai_model, temperature=0)


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```\w*", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned


def _safe_json_parse(text: str) -> Dict:
    cleaned = _strip_code_fences(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                pass
    return {}


def _last_user_text(messages) -> str:
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return msg.content or ""
    return ""


def _build_reason_payload(preferences: Dict, laptops):
    items = []
    for idx, item in enumerate(laptops, start=1):
        items.append(
            {
                "index": idx,
                "name": item.get("name"),
                "price": item.get("price"),
                "cpu": item.get("cpu"),
                "gpu": item.get("gpu"),
                "ram_gb": item.get("ram_gb"),
                "storage_gb": item.get("storage_gb"),
                "screen_size": item.get("screen_size"),
                "weight_kg": item.get("weight_kg"),
                "battery_wh": item.get("battery_wh"),
                "usage_hint": item.get("usage_hint"),
            }
        )
    return {
        "preferences": preferences,
        "laptops": items,
    }


def _generate_ai_reasons(preferences: Dict, laptops, user_text: str) -> Dict:
    payload = _build_reason_payload(preferences, laptops)
    payload["user_message"] = f"<user_message>{user_text}</user_message>"
    response = llm.invoke(
        [
            SystemMessage(content=REASON_PROMPT),
            HumanMessage(content=json.dumps(payload, ensure_ascii=False)),
        ]
    )
    reasons = _safe_json_parse(response.content)
    if not isinstance(reasons, dict):
        return {}
    cleaned = {}
    for key, value in reasons.items():
        if isinstance(value, str) and value.strip():
            cleaned[str(key)] = value.strip()
    return cleaned


VALIDATE_PROMPT = """You are a laptop recommendation validator. You will receive:
1. The user's conversation messages (what they asked for)
2. A list of recommended laptops with their specs

For EACH laptop, decide if it truly fits what the user wants. Consider:
- If user said "AMD" or "Intel istemiyorum", check the CPU brand
- If user wants gaming, check if GPU is powerful enough
- If user wants lightweight, check the weight
- If user wants good battery, check battery capacity
- Any other specific requirement the user mentioned

Return ONLY valid JSON:
{
  "results": [
    {"index": 1, "approved": true, "reason": ""},
    {"index": 2, "approved": false, "reason": "Kullanıcı Intel istemedi ama bu laptop Intel işlemcili"},
    {"index": 3, "approved": true, "reason": ""}
  ]
}
Rules:
- Be strict. If the user explicitly excluded something, reject laptops that have it.
- If the user said "AMD olsun", reject Intel CPU laptops.
- If the user said "hafif olsun" and laptop is >2kg, reject it.
- Only reject for clear violations, not minor preferences.
"""


def _validate_recommendations(laptops: list, state: State) -> list:
    """LLM ile onerileri kullanicinin taleplerine karsi dogrula."""
    messages = state.get("messages", [])
    recent = messages[-8:] if len(messages) > 8 else messages

    conversation = ""
    for msg in recent:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        content = (msg.content or "")[:300]
        conversation += f"{role}: {content}\n"

    laptop_summaries = []
    for i, laptop in enumerate(laptops, 1):
        laptop_summaries.append({
            "index": i,
            "name": laptop.get("name", "?"),
            "cpu": laptop.get("cpu", "?"),
            "gpu": laptop.get("gpu", "?"),
            "ram_gb": laptop.get("ram_gb"),
            "weight_kg": laptop.get("weight_kg"),
            "battery_wh": laptop.get("battery_wh"),
            "price": laptop.get("price"),
        })

    payload = json.dumps({
        "conversation": conversation,
        "laptops": laptop_summaries
    }, ensure_ascii=False)

    try:
        response = llm.invoke([
            SystemMessage(content=VALIDATE_PROMPT),
            HumanMessage(content=payload),
        ])
        result = _safe_json_parse(response.content)
        results = result.get("results", [])

        approved = []
        rejected_reasons = []
        for r in results:
            idx = r.get("index", 0) - 1
            if r.get("approved", True) and 0 <= idx < len(laptops):
                approved.append(laptops[idx])
            elif 0 <= idx < len(laptops):
                rejected_reasons.append(f"{laptops[idx].get('name','?')}: {r.get('reason','')}")

        if rejected_reasons:
            logger.info("Doğrulama reddetti: %s", rejected_reasons)

        return approved
    except Exception as e:
        logger.warning("Doğrulama hatası, orijinal listeyi kullanıyorum: %s", e)
        return laptops


def _extract_budget(text: str):
    lower = text.lower()

    # GPU/CPU model numaralarının yanındaki sayıları dışla
    # RTX 4060, GTX 1650, i5 12400, i7-13700, Ryzen 5 5600 vb.
    hardware_pattern = re.compile(
        r"(?:rtx|gtx|rx|radeon|intel\s*uhd|iris\s*xe|"
        r"i[3579][\s\-]?|ryzen\s*\d\s*|core\s*ultra\s*|"
        r"mx|quadro|firepro|arc\s*a)"
        r"\s*\d+",
        re.IGNORECASE,
    )
    # Donanım model numaralarını metinden geçici olarak temizle
    cleaned = hardware_pattern.sub("", lower)

    # Sayı pattern'i: önce binlik ayırıcılı (20.000), sonra düz sayı (20000)
    _NUM = r"(\d{1,3}(?:[.,]\d{3})+|\d+)"

    # Bütçe bağlamı olan kalıpları ara (TL, lira, bütçe, fiyat vb.)
    budget_context_patterns = [
        # "20000 TL", "20.000 tl", "20,000TL"
        _NUM + r"\s*(?:tl|lira)\b",
        # "20k TL", "20 bin TL", "20bin tl"
        r"(\d+)\s*(k|bin)\s*(?:tl|lira)?\b",
        # "bütçem 20000", "bütçe: 20000", "budget 20000"
        r"(?:bütçe|butce|budget|bütçem|butcem|fiyat|max|maksimum|maximum)\s*[:=]?\s*" + _NUM + r"\s*(k|bin)?",
        # "20000 bütçe", "20000 bütçeyle", "20000 bütçem var"
        _NUM + r"\s*(k|bin)?\s*(?:bütçe|butce|budget|bütçem|butcem|fiyat)",
        # "20000'e kadar", "20000 civarı", "20000 arası"
        _NUM + r"\s*(k|bin)?\s*(?:'?[eay]e?\s*kadar|civar[ıi]|aras[ıi])",
        # "en fazla 20000", "max 20000"
        r"(?:en\s*fazla|en\s*çok|max|maksimum|maximum)\s*" + _NUM + r"\s*(k|bin)?",
    ]

    for pattern in budget_context_patterns:
        match = re.search(pattern, cleaned)
        if match:
            # Gruplardan sayı ve çarpan bilgisini bul
            groups = match.groups()
            number_str = None
            multiplier = None
            for g in groups:
                if g is None:
                    continue
                if g in ("k", "bin"):
                    multiplier = g
                elif re.match(r"^\d", g):
                    number_str = g

            if number_str is None:
                continue

            # Binlik ayırıcıları temizle: "20.000" -> "20000", "1.000.000" -> "1000000"
            if re.match(r"^\d{1,3}(?:[.,]\d{3})+$", number_str):
                number_str = number_str.replace(".", "").replace(",", "")
            else:
                number_str = number_str.replace(",", ".")

            try:
                number = float(number_str)
            except ValueError:
                continue

            if multiplier in ("k", "bin"):
                number *= 1000

            if number < 1000:
                continue

            return int(number)

    return None


def _no_budget_hint(text: str) -> bool:
    lower = text.lower()
    hints = ["butce yok", "bütçe yok", "butce onemsiz", "bütçe önemsiz", "fark etmez",
             "farketmez", "farketsiz", "sinir yok", "sınır yok", "limitsiz", "no budget",
             "butce farketmez", "bütçe farketmez", "para onemli degil", "en iyi"]
    return any(hint in lower for hint in hints)


def _price_focus_hint(text: str) -> bool:
    lower = text.lower()
    hints = ["en ucuz", "ucuz", "en uygun", "butce dostu", "bütçe dostu", "ekonomik", "lowest price"]
    return any(hint in lower for hint in hints)


def _normalize_extracted(data: Dict) -> Dict:
    normalized = {
        "intent": data.get("intent"),
        "budget_max": data.get("budget_max"),
        "usage": data.get("usage"),
        "brand": data.get("brand"),
        "excluded_brands": data.get("excluded_brands"),
        "priority_order": data.get("priority_order"),
        "min_gpu_tier": data.get("min_gpu_tier"),
        "min_ram_gb": data.get("min_ram_gb"),
        "min_storage_gb": data.get("min_storage_gb"),
        "screen_size_min": data.get("screen_size_min"),
        "screen_size_max": data.get("screen_size_max"),
        "weight_max_kg": data.get("weight_max_kg"),
        "weight_importance": data.get("weight_importance"),
        "battery_importance": data.get("battery_importance"),
        "gpu_required": data.get("gpu_required"),
        "notes": data.get("notes"),
    }

    if normalized["budget_max"] is not None:
        try:
            normalized["budget_max"] = int(float(normalized["budget_max"]))
        except (TypeError, ValueError):
            normalized["budget_max"] = None
    if normalized["budget_max"] is not None and normalized["budget_max"] < 1000:
        normalized["budget_max"] = None

    # Usage bazli GPU varsayilani — LLM tier belirtmediyse uygula
    usage = normalized.get("usage")
    tier = normalized.get("min_gpu_tier") or "any"
    if usage in ("gaming", "render") and tier in ("any", "integrated"):
        normalized["min_gpu_tier"] = "mid-high"
    elif usage == "design" and tier in ("any", "integrated"):
        normalized["min_gpu_tier"] = "mid"

    return normalized


def extract_preferences(state: State):
    messages = state["messages"]
    last_user = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
    if not last_user:
        return {}

    user_text = last_user.content or ""
    user_lower = user_text.lower()

    logger.info("Kullanıcı mesajı alındı, tercihler çıkarılıyor")

    # Onceki konusma gecmisini de ekle (son 6 mesaj) — context kaybini onle
    recent_messages = messages[-6:] if len(messages) > 6 else messages
    conversation_context = ""
    for msg in recent_messages[:-1]:  # Son mesaj haric (onu ayri gonderiyoruz)
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        content = (msg.content or "")[:200]
        conversation_context += f"{role}: {content}\n"

    safe_user_text = f"<user_message>{user_text}</user_message>"
    if conversation_context:
        safe_user_text = f"Previous conversation:\n{conversation_context}\nCurrent message:\n{safe_user_text}"

    response = llm.invoke([
        SystemMessage(content=INTENT_PROMPT),
        HumanMessage(content=safe_user_text),
    ])

    extracted = _normalize_extracted(_safe_json_parse(response.content))
    logger.info("Çıkarılan intent: %s, tercihler: %s", extracted.get("intent"), extracted)

    if "render" in user_lower:
        extracted["usage"] = "render"

    if extracted.get("usage") == "gaming" and extracted.get("gpu_required") is None:
        extracted["gpu_required"] = True
    if _price_focus_hint(last_user.content):
        extracted["price_focus"] = True

    if extracted.get("budget_max") is None:
        budget_fallback = _extract_budget(last_user.content)
        if budget_fallback:
            extracted["budget_max"] = budget_fallback

    if _no_budget_hint(last_user.content):
        extracted["budget_max"] = None

    existing_budget = (state.get("preferences") or {}).get("budget_max")
    needs_budget = (
        extracted.get("budget_max") is None
        and existing_budget is None
        and not _no_budget_hint(last_user.content)
        and not extracted.get("price_focus")
    )

    return {"preferences": extracted, "needs_budget": needs_budget}


def _handle_question(state: State) -> str:
    """Genel laptop sorusuna LLM ile cevap ver."""
    user_text = _last_user_text(state.get("messages", []))
    logger.info("Genel soru intent'i işleniyor: %s", user_text[:80])
    response = llm.invoke([
        SystemMessage(
            content="Sen bir laptop uzmanısın. Kullanıcının laptop ile ilgili genel sorusuna "
                    "Türkçe, kısa ve net cevap ver. Markdown formatı kullanabilirsin."
        ),
        HumanMessage(content=user_text),
    ])
    return response.content


def _handle_compare(state: State) -> str:
    """Kullanıcının karşılaştırmak istediği laptopları bul ve karşılaştır."""
    user_text = _last_user_text(state.get("messages", []))
    preferences = state.get("preferences", {})
    logger.info("Karşılaştırma intent'i işleniyor: %s", user_text[:80])

    laptops = recommend_laptops_data(preferences, settings)
    if not laptops:
        return "Karşılaştırma için uygun laptop bulunamadı. Lütfen kriterlerini belirt."

    payload = _build_reason_payload(preferences, laptops)
    payload["user_message"] = user_text
    response = llm.invoke([
        SystemMessage(
            content="Sen bir laptop uzmanısın. Kullanıcının karşılaştırmak istediği laptopları "
                    "aşağıdaki verilerden bul ve Türkçe olarak karşılaştırmalı bir tablo veya "
                    "madde listesi halinde sun. Avantaj ve dezavantajlarını belirt."
        ),
        HumanMessage(content=json.dumps(payload, ensure_ascii=False)),
    ])
    return response.content


def _handle_other() -> str:
    """Laptop dışı mesajlarda kibarca yönlendir."""
    logger.info("Konu dışı mesaj algılandı, kullanıcı yönlendiriliyor")
    return (
        "Ben bir laptop öneri asistanıyım. Sana en uygun laptopları bulmana yardımcı olabilirim.\n\n"
        "Örneğin şunları sorabilirsin:\n"
        "- \"Oyun için 25000 TL bütçeyle laptop öner\"\n"
        "- \"Yazılım geliştirme için hafif bir laptop arıyorum\"\n"
        "- \"Öğrenci için uygun fiyatlı laptop\""
    )


def _build_not_found_message(preferences: Dict) -> str:
    """Sonuc bulunamadiginda bilgilendirici mesaj olustur."""
    parts = ["Kriterlerinize uygun laptop bulunamadı."]

    budget = preferences.get("budget_max")
    brand = preferences.get("brand")
    excluded = preferences.get("excluded_brands")

    # DB'deki en ucuz fiyati bul
    try:
        collection = get_collection(settings)
        cheapest = collection.find_one(sort=[("price", 1)])
        if cheapest and budget:
            min_price = cheapest.get("price") or cheapest.get("fiyat") or 0
            if min_price and budget < min_price:
                parts.append(f"Veritabanındaki en uygun fiyatlı laptop {int(min_price):,} TL.")
    except Exception:
        pass

    suggestions = []
    if budget and budget < 15000:
        suggestions.append("Bütçenizi artırın (en az 15.000 TL öneriyoruz)")
    if brand:
        suggestions.append(f"'{brand}' marka filtresini kaldırın")
    if excluded:
        suggestions.append(f"Dışlanan markaları ({', '.join(excluded)}) gevşetin")

    screen_min = preferences.get("screen_size_min")
    if screen_min and screen_min >= 17:
        suggestions.append(f"{screen_min}\"+ ekran filtresi çok dar — 15.6\" veya 16\" deneyin")

    if suggestions:
        parts.append("\nŞunları deneyebilirsiniz:")
        for s in suggestions:
            parts.append(f"- {s}")

    return "\n".join(parts)


def _do_recommend(state: State, preferences: Dict) -> str:
    """Oneri yap — filtreleme + puanlama ile en iyi 3'u sec."""
    laptops = recommend_laptops_data(preferences, settings)
    if not laptops:
        return _build_not_found_message(preferences)

    top3 = laptops[:3]
    user_text = _last_user_text(state.get("messages", []))
    reasons = _generate_ai_reasons(preferences, top3, user_text)
    return format_markdown_with_reasons(top3, preferences, reasons)


def respond(state: State):
    if state.get("needs_budget"):
        return {"messages": [AIMessage(content="Bütçe limitin nedir? (Örnek: 30000)")]}

    try:
        preferences = state.get("preferences", {})
        intent = preferences.get("intent", "recommend")
        logger.info("Yanıt oluşturuluyor, intent: %s", intent)

        if intent == "question":
            reply = _handle_question(state)
        elif intent == "compare":
            reply = _handle_compare(state)
        elif intent == "other":
            existing_usage = preferences.get("usage")
            existing_budget = preferences.get("budget_max")
            if existing_usage or existing_budget:
                logger.info("Intent 'other' ama onceki tercihler var — recommend olarak isleniyor")
                reply = _do_recommend(state, preferences)
                return {"messages": [AIMessage(content=reply)]}
            reply = _handle_other()
        else:
            reply = _do_recommend(state, preferences)
    except Exception as exc:
        logger.error("Yanıt oluşturulurken hata: %s", exc, exc_info=True)
        return {"messages": [AIMessage(content="Bir hata oluştu. Lütfen tekrar deneyin.")]}

    return {"messages": [AIMessage(content=reply)]}


builder = StateGraph(State)

builder.add_node("extract", extract_preferences)
builder.add_node("respond", respond)

builder.add_edge(START, "extract")
builder.add_edge("extract", "respond")
builder.add_edge("respond", END)

memory = MemorySaver()
app = builder.compile(checkpointer=memory)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    logger.info("Laptop Öneri Asistanı başlatılıyor (CLI modu)")

    print("\n==============================")
    print("Laptop Oneri Asistani")
    print("Cikis icin 'q' yazin.")
    print("==============================\n")

    config = {"configurable": {"thread_id": "1"}}

    while True:
        user_input = input("Siz: ")
        if user_input.lower() in ["q", "exit", "cik"]:
            break

        for event in app.stream({"messages": [HumanMessage(content=user_input)]}, config=config, stream_mode="values"):
            if "messages" in event:
                last_msg = event["messages"][-1]
                if isinstance(last_msg, AIMessage) and last_msg.content:
                    print(f"\nAsistan: {last_msg.content}\n")
