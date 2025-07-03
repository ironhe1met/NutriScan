import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nutriscan.utils.weight_estimation import estimate_weight


def test_estimate_weight_ratio():
    area_px = 100
    image_area_px = 1000
    diameter = 20.0
    plate_area = math.pi * (diameter / 2) ** 2
    expected = plate_area * (area_px / image_area_px)
    assert math.isclose(
        estimate_weight(area_px, image_area_px=image_area_px, plate_diameter_cm=diameter),
        expected,
        rel_tol=1e-6,
    )


def test_estimate_weight_no_scale():
    assert estimate_weight(0) == 0
