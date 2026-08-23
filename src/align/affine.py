"""
STEP 2-B: Control Point → Affine Matrix 계산

완료된 Control Point 쌍(T1 좌표 ↔ T2 좌표)으로부터
T2 → T1 방향의 Affine Transformation Matrix를 계산합니다.

T1이 기준(Baseline) 좌표계이므로, 변환 방향은 항상
    T2 좌표 → T1 좌표
이어야 합니다 (그 반대가 아닙니다).

이 모듈은 Affine Matrix 계산까지만 담당하며,
Warp/Overlay/저장 등은 이후 단계(STEP 2-C)에서 다룹니다.
"""

import numpy as np
import cv2

MIN_POINTS_FOR_AFFINE = 3


def compute_affine(control_points):
    """완료된 Control Point 목록으로부터 T2 → T1 Affine Matrix를 계산합니다.

    Args:
        control_points: point.t1, point.t2 속성을 가진 객체의 리스트
            (예: ControlPointManager.get_points() 또는 completed_points()의 반환값).
            t1, t2가 모두 채워진 point만 사용합니다.

    Returns:
        numpy.ndarray | None: 2x3 Affine Matrix (T2 → T1). 계산할 수 없으면 None.
    """
    completed = [p for p in control_points if p.t1 is not None and p.t2 is not None]

    if len(completed) < MIN_POINTS_FOR_AFFINE:
        print(f"  [ERROR] Affine 계산에는 최소 {MIN_POINTS_FOR_AFFINE}개의 Control Point가 필요합니다. "
              f"(현재 완료된 Point: {len(completed)}개)")
        return None

    # source = T2, destination = T1  →  T2 → T1 방향의 변환을 계산
    src = np.array([p.t2 for p in completed], dtype=np.float32)
    dst = np.array([p.t1 for p in completed], dtype=np.float32)

    try:
        matrix, inliers = cv2.estimateAffine2D(src, dst)
    except Exception as e:
        print(f"  [ERROR] Affine 계산 중 오류 발생: {e}")
        return None

    if matrix is None:
        print("  [ERROR] Affine 계산 실패: cv2.estimateAffine2D가 결과를 반환하지 못했습니다.")
        return None

    return matrix
