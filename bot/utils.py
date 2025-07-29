def format_response(data: dict) -> str:
    lines = []
    for item in data.get("ingredients", []):
        lines.append(
            f"🍽 *{item['name'].capitalize()}* — {item['weight']} г\n"
            f"Калорії: {item['calories']} ккал\n"
            f"Б: {item['protein']} г / Ж: {item['fat']} г / В: {item['carbs']} г\n"
        )

    total = data.get("total", {})
    lines.append(
        f"\n📊 *Разом*: {total.get('calories', 0)} ккал "
        f"(Б: {total.get('protein', 0)} г / Ж: {total.get('fat', 0)} г / В: {total.get('carbs', 0)} г)"
    )
    return "\n".join(lines)
