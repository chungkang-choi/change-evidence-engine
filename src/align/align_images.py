import os
import sys
import json
import cv2

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QLabel,
    QFileDialog,
    QHBoxLayout,
    QVBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QSlider,
)

from image_view import ImageView
from control_points import ControlPointManager
from affine import compute_affine, warp_image


# --------------------------------------------------
# STEP 2-E: GSD 정보 표시 (관측/표시 전용, Resampling 없음)
# --------------------------------------------------

def _load_image_metadata():
    """projects/metadata/image_metadata.json을 읽어 dict로 반환합니다.

    파일이 없거나 손상된 경우 None을 반환하며, 예외를 발생시키지 않습니다.
    (metadata가 없어도 기존 Alignment workflow는 그대로 동작해야 하므로)
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    metadata_path = os.path.join(project_root, "projects", "metadata", "image_metadata.json")

    if not os.path.isfile(metadata_path):
        return None

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _lookup_gsd(metadata, image_path):
    """PNG 파일 경로에 대응하는 원본 TIF 항목의 gsd 값을 조회합니다.

    metadata는 STEP 1에서 생성된 "<TIF 파일명>": {...} 구조를 그대로 사용하며,
    key/value 구조는 변경하지 않습니다. 대응 항목이 없거나 gsd가 null이면 None.
    """
    if metadata is None or not image_path:
        return None

    stem = os.path.splitext(os.path.basename(image_path))[0]
    entry = metadata.get(stem + ".tif")

    if entry is None:
        return None

    return entry.get("gsd")


def _classify_gsd_difference(diff_pct):
    """GSD Difference(%)에 대한 정보성 분류.

    정합 성공/실패, Resampling 필요 여부, Change Detection 가능 여부와는
    무관한 단순 참고용 표시이다.
    """
    if diff_pct < 5:
        return "Small GSD difference"
    elif diff_pct <= 20:
        return "Moderate GSD difference"
    else:
        return "Large GSD difference"


def _build_gsd_report_text(metadata_available, t1_gsd, t2_gsd):
    """GUI에 표시할 GSD 정보 텍스트를 구성한다.

    metadata 파일 부재, gsd 값 None(T1/T2 단독 또는 둘 다) 모두
    예외 없이 안전하게 처리한다.
    """
    if not metadata_available:
        return "GSD information unavailable:\nimage_metadata.json not found."

    if t1_gsd is None and t2_gsd is None:
        return (
            "T1 GSD         : N/A\n"
            "T2 GSD         : N/A\n"
            "GSD Ratio      : N/A\n"
            "GSD Difference : N/A\n"
            "Status         : GSD unavailable"
        )

    if t1_gsd is None or t2_gsd is None:
        t1_text = f"{t1_gsd:.4f} m/pixel" if t1_gsd is not None else "N/A"
        t2_text = f"{t2_gsd:.4f} m/pixel" if t2_gsd is not None else "N/A"
        return (
            f"T1 GSD         : {t1_text}\n"
            f"T2 GSD         : {t2_text}\n"
            "GSD Ratio      : N/A\n"
            "GSD Difference : N/A\n"
            "Status         : GSD unavailable"
        )

    ratio = t2_gsd / t1_gsd
    diff_pct = abs(t2_gsd - t1_gsd) / t1_gsd * 100

    status = _classify_gsd_difference(diff_pct)

    lines = [
        f"T1 GSD         : {t1_gsd:.4f} m/pixel",
        f"T2 GSD         : {t2_gsd:.4f} m/pixel",
        f"GSD Ratio      : {ratio:.4f}",
        f"GSD Difference : {diff_pct:.2f}%",
        f"Status         : {status}",
    ]

    if status == "Large GSD difference":
        lines.append("Warning: Large GSD difference.")
        lines.append("Visual alignment verification recommended.")

    return "\n".join(lines)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Change Evidence - Alignment Tool")
        self.resize(1600, 900)

        self.before_img = None
        self.after_img = None
        self.before_path = None
        self.after_path = None

        # STEP 2-D: Alignment 결과 (aligned T2)
        self.aligned_img = None

        self.cp_manager = ControlPointManager()
        self.selected_point = None

        self.init_ui()

    def init_ui(self):


        # ----------------------------
        # 버튼
        # ----------------------------
        self.load_btn = QPushButton("Load Images")
        self.load_btn.clicked.connect(self.load_images)

        # ----------------------------
        # 상태바
        # ----------------------------
        self.status = QLabel("Ready")

        # ----------------------------
        # Image View 생성
        # ----------------------------
        self.before_view = ImageView("T1")
        self.after_view = ImageView("T2")

        # ----------------------------
        # Before 영역
        # ----------------------------
        before_layout = QVBoxLayout()

        before_title = QLabel("Before (T1)")
        before_title.setStyleSheet("font-weight:bold;")

        before_layout.addWidget(before_title)
        before_layout.addWidget(self.before_view)

        # ----------------------------
        # After 영역
        # ----------------------------
        after_layout = QVBoxLayout()

        after_title = QLabel("After (T2)")
        after_title.setStyleSheet("font-weight:bold;")

        after_layout.addWidget(after_title)
        after_layout.addWidget(self.after_view)

        # ----------------------------
        # Overlay 영역 (STEP 2-D)
        # ----------------------------
        overlay_layout = QVBoxLayout()

        overlay_title = QLabel("Overlay (T1 + Aligned T2)")
        overlay_title.setStyleSheet("font-weight:bold;")

        self.overlay_view = ImageView("Overlay")

        self.align_btn = QPushButton("Run Alignment")
        self.align_btn.clicked.connect(self.run_alignment)
        self.align_btn.setStyleSheet("background-color: #4caf50; color: white; font-weight: bold; padding: 6px;")

        self.opacity_label = QLabel("T2 Opacity: 50")

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(50)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)

        # ----------------------------
        # GSD 정보 표시 (STEP 2-E, 관측/표시 전용)
        # ----------------------------
        self.gsd_info_label = QLabel("GSD Info: load T1/T2 images to see comparison.")
        self.gsd_info_label.setWordWrap(True)
        self.gsd_info_label.setStyleSheet(
            "font-family: Consolas, monospace; background-color: #f5f5f5; "
            "padding: 6px; border: 1px solid #ccc;"
        )

        overlay_layout.addWidget(overlay_title)
        overlay_layout.addWidget(self.overlay_view)
        overlay_layout.addWidget(self.align_btn)
        overlay_layout.addWidget(self.opacity_label)
        overlay_layout.addWidget(self.opacity_slider)
        overlay_layout.addWidget(self.gsd_info_label)

        control_layout = QVBoxLayout()

        title = QLabel("Control Points")
        title.setStyleSheet("font-weight:bold;")

        self.lbl_next = QLabel()
        self.lbl_step = QLabel()

        self.point_tree = QTreeWidget()

        self.point_tree.setHeaderLabels(
            ["ID","T1","T2"]
        )
        self.point_tree.itemSelectionChanged.connect(self.on_tree_selection_changed)

        self.delete_btn = QPushButton("Delete Point")
        self.delete_btn.clicked.connect(self.delete_selected_point)
        self.delete_btn.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold; padding: 6px; margin-bottom: 4px;")

        self.reset_btn = QPushButton("Reset Points")
        self.reset_btn.clicked.connect(self.reset_points)
        self.reset_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 6px;")

        control_layout.addWidget(title)
        control_layout.addWidget(self.lbl_next)
        control_layout.addWidget(self.lbl_step)
        control_layout.addWidget(self.point_tree)
        control_layout.addWidget(self.delete_btn)
        control_layout.addWidget(self.reset_btn)
        self.update_cp_panel()


        # ----------------------------
        # 좌우 이미지 Layout
        # ----------------------------
        image_layout = QHBoxLayout()

        image_layout.addLayout(before_layout,3)
        image_layout.addLayout(after_layout,3)
        image_layout.addLayout(overlay_layout,3)
        image_layout.addLayout(control_layout,1)

        # ----------------------------
        # 전체 Layout
        # ----------------------------
        main_layout = QVBoxLayout()

        main_layout.addWidget(self.load_btn)
        main_layout.addLayout(image_layout)
        main_layout.addWidget(self.status)

        container = QWidget()
        container.setLayout(main_layout)

        self.setCentralWidget(container)

        self.before_view.pointClicked.connect(
           self.image_clicked
        )

        self.after_view.pointClicked.connect(
            self.image_clicked
        )




    def load_images(self):

        before_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select BEFORE Image",
            "",
            "PNG (*.png)"
        )

        if not before_path:
            return

        after_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select AFTER Image",
            "",
            "PNG (*.png)"
        )

        if not after_path:
            return

        self.before_img = cv2.imread(before_path)
        self.after_img = cv2.imread(after_path)

        if self.before_img is None or self.after_img is None:
            self.status.setText("Image Load Failed")
            return

        self.before_path = before_path
        self.after_path = after_path

        self.before_view.set_cv_image(self.before_img)
        self.after_view.set_cv_image(self.after_img)

        self.status.setText("Images Loaded")

        self.update_gsd_info()

    def update_gsd_info(self):
        """STEP 2-E: T1/T2 metadata의 GSD를 조회하여 정보 Label을 갱신한다.

        metadata 파일 부재, gsd 값 None 등 어떤 경우에도 예외를 발생시키지 않으며,
        Alignment(Control Point/Affine/Warp/Overlay) 기능에는 전혀 영향을 주지 않는다.
        """
        metadata = _load_image_metadata()
        metadata_available = metadata is not None

        t1_gsd = _lookup_gsd(metadata, self.before_path) if metadata_available else None
        t2_gsd = _lookup_gsd(metadata, self.after_path) if metadata_available else None

        text = _build_gsd_report_text(metadata_available, t1_gsd, t2_gsd)

        self.gsd_info_label.setText(text)

    def image_clicked(self, image_name, x, y):

        if self.selected_point is not None:
            self.cp_manager.update_point(
                self.selected_point,
                image_name,
                x,
                y
            )
            self.update_cp_panel()
            self.refresh_points()
            self.status.setText(
                f"Updated {self.selected_point} {image_name} : ({int(x)}, {int(y)})"
            )
            return

        expected = self.cp_manager.current_step()

        if expected != image_name:
            self.status.setText(
                f"Please click {expected} first."
            )
            return

        self.cp_manager.add_click(
            image_name,
            x,
            y
        )

        self.update_cp_panel()

        # 새로 추가
        self.refresh_points()

        self.status.setText(
            f"{image_name} : ({int(x)}, {int(y)})"
        )

    def update_cp_panel(self):

        self.lbl_next.setText(
            f"Next Point : {self.cp_manager.current_name()}"
        )

        self.lbl_step.setText(
            self.cp_manager.status_text()
        )

        self.point_tree.clear()

        for p in self.cp_manager.get_points():

            if p.complete:

                t1 = "✓"

                t2 = "✓"

            else:

                t1 = "✓" if p.t1 else ""

                t2 = "✓" if p.t2 else ""

            item = QTreeWidgetItem(
                [
                    p.name,
                    t1,
                    t2
                ]
            )

            self.point_tree.addTopLevelItem(item)
        
    def refresh_points(self):

        self.before_view.clear_points()
        self.after_view.clear_points()

        for p in self.cp_manager.get_points():

            if p.t1:

                self.before_view.add_point(
                    p.name,
                    p.t1[0],
                    p.t1[1]
                )

            if p.t2:

                self.after_view.add_point(
                    p.name,
                    p.t2[0],
                    p.t2[1]
                )

    def on_tree_selection_changed(self):
        selected_items = self.point_tree.selectedItems()
        if selected_items:
            self.selected_point = selected_items[0].text(0)
        else:
            self.selected_point = None

    def delete_selected_point(self):
        if not self.selected_point:
            self.status.setText("No point selected to delete.")
            return

        point_name = self.selected_point
        self.cp_manager.delete_point(point_name)
        self.selected_point = None
        self.point_tree.clearSelection()
        self.update_cp_panel()
        self.refresh_points()
        self.status.setText(f"Deleted control point {point_name}")

    def reset_points(self):
        self.cp_manager.clear()
        self.update_cp_panel()
        self.refresh_points()
        self.status.setText("All Control Points Reset")

    # --------------------------------------------------
    # STEP 2-D: Alignment 실행 + Overlay
    # --------------------------------------------------

    def run_alignment(self):

        if self.before_img is None or self.after_img is None:
            self.status.setText("Please load both T1 and T2 images first.")
            return

        completed = self.cp_manager.completed_points()

        if len(completed) < 3:
            self.status.setText(
                f"Alignment requires at least 3 completed Control Points. (currently {len(completed)})"
            )
            return

        matrix = compute_affine(completed)

        if matrix is None:
            self.status.setText("Affine calculation failed. Check Control Points.")
            return

        t1_h, t1_w = self.before_img.shape[:2]

        aligned = warp_image(self.after_img, matrix, (t1_w, t1_h))

        if aligned is None:
            self.status.setText("Warp failed.")
            return

        self.aligned_img = aligned

        # T1을 base로, aligned T2를 overlay로 표시 (기존 opacity 값 유지)
        self.overlay_view.set_cv_image(self.before_img)
        self.overlay_view.set_overlay_image(self.aligned_img)
        self.overlay_view.set_overlay_opacity(self.opacity_slider.value() / 100.0)

        self._save_aligned_image()

    def on_opacity_changed(self, value):

        self.opacity_label.setText(f"T2 Opacity: {value}")
        self.overlay_view.set_overlay_opacity(value / 100.0)

    def _save_aligned_image(self):

        if self.aligned_img is None or not self.after_path:
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        aligned_dir = os.path.join(project_root, "projects", "aligned")

        os.makedirs(aligned_dir, exist_ok=True)

        t2_stem = os.path.splitext(os.path.basename(self.after_path))[0]
        out_path = os.path.join(aligned_dir, f"aligned_{t2_stem}.png")

        ok = cv2.imwrite(out_path, self.aligned_img)

        if ok:
            self.status.setText(f"Alignment complete. Saved: {out_path}")
        else:
            self.status.setText("Alignment complete, but saving aligned image failed.")


def main():

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()