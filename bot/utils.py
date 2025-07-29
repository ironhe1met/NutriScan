import json

def format_response(result: dict) -> str:
    data = result.get("data", {})
    error = result.get("error") or data.get("error")

    if error:
        return "⚠️ Не вдалося обробити зображення."

    # 🔄 Якщо є raw_response, спробуй розпарсити вручну
    if "ingredients" not in data and "raw_response" in data:
        raw = data["raw_response"]
        try:
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.strip("`").strip()
                if raw.startswith("json"):
                    raw = raw[4:].strip()
            data = json.loads(raw)
        except Exception:
            return "⚠️ Не вдалося розпізнати відповідь GPT."

    ingredients = data.get("ingredients", [])
    total = data.get("total", {})

    if not ingredients:
        return "⚠️ Не вдалося визначити інгредієнти."

    lines = ["🍽 *Інгредієнти:*"]
    for item in ingredients:
        lines.append(f"• {item['name']} — {item['weight_g']} г")

    lines.append(
        f"\n📊 *Разом:* {total.get('calories_kcal', 0)} ккал "
        f"(Б: {total.get('protein_g', 0)} г / "
        f"Ж: {total.get('fat_g', 0)} г / "
        f"В: {total.get('carbs_g', 0)} г)"
    )

    return "\n".join(lines)
