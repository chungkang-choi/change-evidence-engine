"""
STEP 2-F: Project Save / Load

현재 Alignment 작업 상태(T1/T2 이미지 경로, Control Points, Affine Matrix,
aligned image 경로)를 project.json으로 저장하고 다시 불러옵니다.

이 파일은 순수 데이터 변환/입출력만 담당하며 Qt(GUI)에는 의존하지 않습니다.
GUI 연결(버튼, 파일 다이얼로그, 이미지 로딩, Overlay 갱신 등)은
align_images.py에서 수행합니다.

GSD 정보는 이 파일에 저장하지 않습니다. GSD는 항상
projects/metadata/image_metadata.json 을 Single Source of Truth로 사용합니다.
"""

import os
import json

import numpy as np

from control_points import ControlPoint

PROJECT_FILE_VERSION = 1


# --------------------------------------------------
# 경로 변환
# --------------------------------------------------

def get_project_root(start_file):
    """start_file(예: align_images.py의 __file__)을 기준으로 프로젝트 루트를 계산한다.

    project_root/src/align/<start_file> 구조를 가정한다
    (align_images.py의 기존 _save_aligned_image()/_load_image_metadata()와 동일한 규칙).
    """
    script_dir = os.path.dirname(os.path.abspath(start_file))
    return os.path.dirname(os.path.dirname(script_dir))


def to_relative_path(path, project_root):
    """project_root 기준 상대경로(슬래시 구분)로 변환한다.

    다른 드라이브 등으로 상대경로를 만들 수 없는 경우에는
    절대경로를 그대로 반환한다 (crash를 피하기 위함).
    """
    if not path:
        return None

    try:
        rel = os.path.relpath(path, project_root)
    except ValueError:
        return path

    return rel.replace(os.sep, "/")


def to_absolute_path(path, project_root):
    """project.json에 저장된 경로(상대 또는 절대)를 절대경로로 변환한다."""
    if not path:
        return None

    if os.path.isabs(path):
        return os.path.normpath(path)

    return os.path.normpath(os.path.join(project_root, path))


# --------------------------------------------------
# Control Point 직렬화 / 복원
# --------------------------------------------------

def control_points_to_list(control_points):
    """ControlPoint 객체 목록을 JSON 직렬화 가능한 list[dict]로 변환한다.

    t1/t2가 모두 비어 있는 Point(Wizard가 다음 입력을 위해 만들어 둔
    빈 slot)는 저장하지 않는다. 저장/복원 대상은 실제로 하나 이상의
    좌표가 입력된 Point만이다.
    """
    result = []

    for p in control_points:

        if p.t1 is None and p.t2 is None:
            continue

        result.append({
            "name": p.name,
            "t1": list(p.t1) if p.t1 is not None else None,
            "t2": list(p.t2) if p.t2 is not None else None,
        })

    return result


def restore_control_points(cp_manager, points_data):
    """저장된 Control Point 목록으로 cp_manager 상태를 복원한다.

    ControlPointManager/ControlPoint 자체는 수정하지 않고,
    기존에 공개된 속성(points/current_point/current_index/state)과
    공개 메서드(create_next_point)만 사용해 상태를 재구성한다.
    이렇게 복원한 뒤에도 Control Point Wizard(P1/P2/... 순차 입력,
    수정/삭제/리셋, ready_for_alignment()/completed_points())는
    기존과 동일하게 계속 동작한다.
    """
    restored_points = []

    for entry in points_data or []:
        t1 = tuple(entry["t1"]) if entry.get("t1") is not None else None
        t2 = tuple(entry["t2"]) if entry.get("t2") is not None else None
        restored_points.append(ControlPoint(name=entry.get("name"), t1=t1, t2=t2))

    if not restored_points:
        cp_manager.clear()
        return

    cp_manager.points = restored_points

    last = restored_points[-1]

    try:
        last_index = int(last.name[1:]) if last.name and last.name.startswith("P") else len(restored_points)
    except ValueError:
        last_index = len(restored_points)

    if last.complete:
        # 마지막으로 저장된 Point가 완료 상태이면, 다음 새 Point부터 이어서 입력한다.
        cp_manager.current_index = last_index + 1
        cp_manager.current_point = None
        cp_manager.state = "T1"
        cp_manager.create_next_point()
    else:
        # 마지막 Point가 미완료 상태(t1만 있고 t2가 없는 등)이면,
        # 그 Point를 이어서 입력하도록 current_point로 지정한다.
        cp_manager.current_index = last_index
        cp_manager.current_point = last
        cp_manager.state = "T2" if last.t1 is not None else "T1"


# --------------------------------------------------
# Affine Matrix 직렬화 / 복원
# --------------------------------------------------

def affine_matrix_to_list(affine_matrix):
    """numpy 2x3 ndarray -> list[list[float]]. None이면 None을 반환한다.

    값 자체는 그대로 float로 변환할 뿐, 재계산이나 반올림은 하지 않는다.
    """
    if affine_matrix is None:
        return None

    return [[float(v) for v in row] for row in affine_matrix]


def affine_matrix_from_list(matrix_list):
    """list[list[float]] -> numpy 2x3 ndarray. None이면 None을 반환한다.

    compute_affine()/warp_image()가 사용하는 형식과 동일한 numpy array로
    복원할 뿐, Affine 값을 다시 계산하지 않는다.
    """
    if matrix_list is None:
        return None

    return np.array(matrix_list, dtype=np.float64)


# --------------------------------------------------
# Polygon ROI 직렬화 / 복원 (STEP 2-G)
# --------------------------------------------------

def roi_polygon_to_list(roi_points):
    """ROI Polygon vertex 목록을 JSON 직렬화 가능한 list[list[float]]로 변환한다.

    좌표 값 자체는 변경하지 않는다 (재계산/반올림 없음). Vertex가 없으면 None.
    """
    if not roi_points:
        return None

    return [[float(x), float(y)] for x, y in roi_points]


def roi_polygon_from_list(polygon_list):
    """project.json에 저장된 roi_polygon을 [(x, y), ...] 목록으로 복원한다.

    값이 없거나 None이면 None을 반환한다 (기존 project.json과의 하위 호환).
    """
    if not polygon_list:
        return None

    return [(float(x), float(y)) for x, y in polygon_list]


# --------------------------------------------------
# Project dict 구성 / 저장 / 로드
# --------------------------------------------------

def build_project_dict(t1_path, t2_path, control_points, affine_matrix, aligned_path,
                        project_root, roi_polygon=None, roi_mask_path=None):
    """현재 Alignment/ROI 작업 상태로부터 저장용 dict를 구성한다.

    roi_polygon/roi_mask_path는 STEP 2-F 시점의 project.json과 하위 호환되도록
    선택적(optional) 인자로 두었다 — 지정하지 않으면 각각 null로 저장된다.
    GSD/CRS/transform 등 원본 metadata는 여기에 저장하지 않는다
    (image_metadata.json이 Single Source of Truth).
    """
    return {
        "version": PROJECT_FILE_VERSION,
        "t1_image": to_relative_path(t1_path, project_root),
        "t2_image": to_relative_path(t2_path, project_root),
        "control_points": control_points_to_list(control_points),
        "affine_matrix": affine_matrix_to_list(affine_matrix),
        "aligned_image": to_relative_path(aligned_path, project_root),
        "roi_polygon": roi_polygon_to_list(roi_polygon),
        "roi_mask": to_relative_path(roi_mask_path, project_root),
    }


def save_project(path, project_dict):
    """project_dict를 JSON 파일로 저장한다."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(project_dict, f, ensure_ascii=False, indent=2)


def load_project(path):
    """project.json을 읽어 dict로 반환한다.

    파일이 없거나 JSON 형식이 잘못된 경우 예외가 그대로 전파되며,
    호출 측(align_images.py)에서 사용자에게 표시할 오류 메시지로 변환한다.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
