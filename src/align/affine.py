"""
STEP 2-B: Control Point → Affine Matrix 계산
STEP 2-C: Affine Matrix → T2 Warp

완료된 Control Point 쌍(T1 좌표 ↔ T2 좌표)으로부터
T2 → T1 방향의 Affine Transformation Matrix를 계산하고,
이 Matrix를 이용해 T2 이미지를 T1 좌표계로 Warp합니다.

T1이 기준(Baseline) 좌표계이므로, 변환 방향은 항상
    T2 좌표 → T1 좌표
이어야 합니다 (그 반대가 아닙니다).

Overlay/저장 경로 관리/GSD 등은 이후 단계에서 다룹니다.
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


def warp_image(image, affine_matrix, output_size):
    """T2 → T1 Affine Matrix를 이용해 이미지를 T1 좌표계로 Warp합니다.

    Args:
        image: Warp할 원본 이미지 (T2). compute_affine()과 동일하게
            cv2.imread()로 읽은 numpy array를 그대로 사용합니다 (channel 순서 변경 없음).
        affine_matrix: compute_affine()이 반환한 2x3 T2 → T1 Affine Matrix.
            (이 함수에서 다시 계산하거나 inverse를 적용하지 않습니다.)
        output_size: (width, height) — T1 PNG의 pixel dimensions 기준 출력 크기.

    Returns:
        numpy.ndarray | None: T1 좌표계로 정렬된 이미지. 입력이 유효하지 않으면 None.
    """
    if affine_matrix is None:
        print("  [ERROR] Warp 실패: affine_matrix가 None입니다.")
        return None

    if image is None:
        print("  [ERROR] Warp 실패: 입력 이미지가 None입니다.")
        return None

    return cv2.warpAffine(image, affine_matrix, output_size)
