def estimate_weight(area_px: float, plate_diameter_cm: float = 25.0) -> float:
    """Estimate ingredient weight from segmented area in pixels.

    This is a placeholder implementation using a naive proportional formula.
    """
    plate_area = 3.1415 * (plate_diameter_cm / 2) ** 2
    density_factor = 1.0  # placeholder density factor g/cm^2
    return density_factor * (area_px / plate_area)
