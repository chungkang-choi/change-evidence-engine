#!/usr/bin/env python3
"""
STEP 1-A: GeoTIFF → PNG 변환기

projects/tif/*.tif 파일을 projects/png/*.png로 변환하며,
기존 PNG 파일을 덮어씁니다.

metadata는 생성하지 않으며(STEP 1-B에서 구현),
적어도 하나의 샘플에서 정상적으로 작동해야 합니다.
"""

import os
import sys
import rasterio
from PIL import Image
from rasterio.errors import RasterioError
def convert_tif_to_png(tif_path: str, png_dir: str) -> bool:
    """단일 GeoTIFF를 PNG로 변환합니다.

    Returns:
        bool: 성공 여부
    """
    try:
        with rasterio.open(tif_path) as src:
            # 밴드 읽기: (bands, height, width)
            arr = src.read()  # numpy array
            # -- 밴드 선택 및 순서를 RGB로 변환 (최대 3개의 밴드 사용)
            if arr.ndim != 3 or arr.shape[0] < 1:
                print(f"  [ERROR] {tif_path}의 GeoTIFF가 올바르지 않습니다.")
                return False

            # 세 개의 밴드 사용: 4개(RGBA)인 경우 첫 세 개의 밴드 사용, 아니면 가장 중요한 밴드 사용
            bands = arr.shape[0]
            if bands >= 3:
                arr = arr[:3]
            elif bands == 1:
                arr = arr.repeat(3, axis=0)
            else:
                # 2개의 밴드인 경우 빈 밴드 추가
                arr = arr
                # 빈 밴드 추가는 필요하지 않음; 단순화를 위해: 마지막 밴드 반복
                arr = arr[-1:].repeat(3, axis=0)

            # (H, W, C)로 재배열
            arr = arr.transpose(1, 2, 0)

            # Pillow가 수용할 수 있는 dtype로 변환 (uint8이 가장 일반적)
            if arr.dtype != 'uint8':
                # 0-255 범위로 스케일링 (0-1 범위의 float 포함)
                if arr.dtype.kind == 'f':
                    # 단정 float (0.0-1.0)이라고 가정합니다. 간소화를 위해 일반적인 GeoTIFF float의 경우 255로 스케일링
                    arr = (arr * 255).clip(0, 255)
                # 모든 dtype에 대해 min-max 정규화
                arr_min = arr.min()
                arr_max = arr.max()
                if arr_max > arr_min:
                    arr = ((arr - arr_min) / (arr_max - arr_min) * 255)
                else:
                    arr = arr * 0  # 모두 0으로 설정
                arr = arr.astype('uint8')

            img = Image.fromarray(arr, mode='RGB')
    except Exception as e:
        print(f"  [ERROR] {tif_path} 읽기 실패: {e}")
        return False

    # PNG 저장
    base_name = os.path.splitext(os.path.basename(tif_path))[0] + '.png'
    png_path = os.path.join(png_dir, base_name)
    try:
        os.makedirs(png_dir, exist_ok=True)
        img.save(png_path, format='PNG')
        print(f"Saved: {png_path}")
        return True
    except Exception as e:
        print(f"  [ERROR] {png_path} 저장 실패: {e}")
        return False
def main():
    # FIXED: src/convert_tif_to_png.py 바로 위 폴더를 project root로 사용
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # c:/Users/.../change-evidence-engine
    tif_dir = os.path.join(project_root, 'projects', 'tif')
    png_dir = os.path.join(project_root, 'projects', 'png')

    if not os.path.isdir(tif_dir):
        print(f"Input 폴더가 존재하지 않습니다: {tif_dir}")
        sys.exit(1)

    # 하위 폴더를 탐색하지 않고, *.tif 파일만 대상으로 합니다
    tif_files = []
    for entry in os.listdir(tif_dir):
        if entry.lower().endswith('.tif'):
            tif_files.append(os.path.join(tif_dir, entry))

    if not tif_files:
        print(f"Input 폴더에 .tif 파일이 없습니다: {tif_dir}")
        sys.exit(0)  # 빈 폴더는 정상적일 수 있습니다

    success = 0
    for tif_path in tif_files:
        print(f"Converting: {os.path.basename(tif_path)}")
        if convert_tif_to_png(tif_path, png_dir):
            success += 1
        else:
            print(f"  [FAIL] {os.path.basename(tif_path)}")

    print(f"\n완료: {success}개 성공, {len(tif_files)-success}개 실패")
if __name__ == "__main__":
    main()
