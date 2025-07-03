import math


def estimate_weight(
    area_px: float,
    image_area_px: float | None = None,
    plate_diameter_cm: float = 25.0,
    density_factor: float = 1.0,
) -> float:
    """Оцінює вагу інгредієнта на основі площі сегмента.

    Якщо відома загальна площа зображення ``image_area_px``, площа сегмента
    приводиться до фізичної площі тарілки ``plate_diameter_cm``. Це дозволяє
    отримати більш реалістичну оцінку ваги, ніж попереднє наївне порівняння
    кількості пікселів з діаметром тарілки.
    """
    plate_area_cm2 = math.pi * (plate_diameter_cm / 2) ** 2
    if image_area_px and image_area_px > 0:
        area_cm2 = plate_area_cm2 * (area_px / image_area_px)
    else:
        # Повертаємося до простого наближення, якщо масштаб невідомий
        area_cm2 = area_px
    return density_factor * area_cm2
