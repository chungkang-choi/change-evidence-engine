"""
STEP 2-G: Polygon ROI -> Binary Mask

T1 pixel coordinate 기준 Polygon vertex 목록을 받아, T1 이미지와 동일한 크기의
binary ROI mask(uint8, ROI 내부=255, 외부=0)로 변환하는 순수 함수만 제공합니다.

GUI(PySide6)나 project_io.py에는 의존하지 않습니다.
World coordinate / CRS / GSD 변환은 다루지 않습니다 — 입력 좌표는 항상
T1 이미지의 pixel coordinate(origin=top-left, x=column, y=row)라고 가정합니다.
"""

import numpy as np
import cv2

MIN_POINTS_FOR_POLYGON = 3


def points_to_mask(polygon_points, image_shape):
    """Polygon vertex 목록으로부터 binary ROI mask를 생성합니다.

    Args:
        polygon_points: [(x1, y1), (x2, y2), ...] 형태의 T1 pixel coordinate 목록.
            좌표는 float이어도 되며, 내부적으로 np.int32로 반올림하여 사용합니다.
        image_shape: (height, width, ...) — T1 이미지 크기. 앞의 두 값만 사용하며,
            생성되는 mask도 반드시 이와 동일한 (height, width)를 가집니다.

    Returns:
        numpy.ndarray | None: (height, width) 크기의 uint8 mask.
            ROI 내부 = 255, 외부 = 0. vertex가 3개 미만이면 None.
    """
    if polygon_points is None or len(polygon_points) < MIN_POINTS_FOR_POLYGON:
        count = 0 if polygon_points is None else len(polygon_points)
        print(f"  [ERROR] ROI mask 생성에는 최소 {MIN_POINTS_FOR_POLYGON}개의 vertex가 필요합니다. "
              f"(현재 {count}개)")
        return None

    height, width = image_shape[0], image_shape[1]

    mask = np.zeros((height, width), dtype=np.uint8)

    pts = np.array(
        [[int(round(x)), int(round(y))] for x, y in polygon_points],
        dtype=np.int32,
    )

    cv2.fillPoly(mask, [pts], 255)

    return mask
