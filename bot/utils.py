import json

def format_response(result: dict) -> str:
    data = result.get("data", {})
    error = result.get("error") or data.get("error")

    if error:
        return "⚠️ Не вдалося обробити зображення."

    ingredients = data.get("ingredients", [])
    total = data.get("total", {})

    # 👇 Додаткова перевірка, якщо дані вкладені в raw_response
    if not ingredients and "raw_response" in data:
        try:
            raw = data["raw_response"].strip().removeprefix("```json").removesuffix("```").strip()
            data = json.loads(raw)
            ingredients = data.get("ingredients", [])
            total = data.get("total", {})
        except Exception:
            return "⚠️ Не вдалося розпізнати відповідь GPT."

    if not ingredients:
        return "⚠️ Не вдалося визначити інгредієнти."

    lines = ["🍽 *Інгредієнти:*"]
    for ing in ingredients:
        name = ing.get("name", "Невідомо")
        weight = ing.get("weight_g", "?")
        lines.append(f"• {name} — {weight} г")

    lines.append(
        f"\n📊 *Разом:* {total.get('calories_kcal', 0)} ккал "
        f"(Б: {total.get('protein_g', 0)} г / "
        f"Ж: {total.get('fat_g', 0)} г / "
        f"В: {total.get('carbs_g', 0)} г)"
    )

    return "\n".join(lines)
