# Laptop Oneri (LangGraph)

This project mirrors the n8n flow:
- User message -> AI extracts intent/budget/preferences
- MongoDB fetch
- Filter + score
- Return top 3 laptops in Markdown

## Setup

1) Create a virtual environment and install requirements:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Create `.env` (copy from `.env.example`) and set:
- `OPENAI_API_KEY`
- `MONGODB_URI`
- `MONGODB_DB`
- `MONGODB_COLLECTION`

Optional overrides:
- `PRICE_FIELD`, `NAME_FIELD`, `BRAND_FIELD`, `MAX_FETCH`

3) Run:

```bash
python3 main.py
```

## Schema assumptions

The recommender tries to normalize common fields. It looks for these keys (or your overrides):
- `name`, `model`, `title`
- `brand`, `manufacturer`
- `price`, `price_try`, `price_tl`, `price_usd`
- `cpu`, `processor`
- `gpu`, `graphics`
- `ram`, `ram_gb`, `memory`
- `storage`, `storage_gb`, `ssd`, `hdd`
- `screen_size`, `display_size`
- `weight`, `weight_kg`
- `battery_wh`

If your schema differs, update `recommender.py` or set the optional field env vars.

## Notes

- The scoring model is heuristic and easy to adjust in `recommender.py`.
- If no results match, the assistant asks to loosen the constraints.
