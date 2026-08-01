import sys
import cv2

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
    QTreeWidgetItem
)

from image_view import ImageView
from control_points import ControlPointManager

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Change Evidence - Alignment Tool")
        self.resize(1600, 900)

        self.before_img = None
        self.after_img = None

        self.cp_manager = ControlPointManager()

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




        control_layout = QVBoxLayout()

        title = QLabel("Control Points")
        title.setStyleSheet("font-weight:bold;")

        self.lbl_next = QLabel()
        self.lbl_step = QLabel()

        self.point_tree = QTreeWidget()

        self.point_tree.setHeaderLabels(
            ["ID","T1","T2"]
        )

        self.reset_btn = QPushButton("Reset Points")
        self.reset_btn.clicked.connect(self.reset_points)
        self.reset_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 6px;")

        control_layout.addWidget(title)
        control_layout.addWidget(self.lbl_next)
        control_layout.addWidget(self.lbl_step)
        control_layout.addWidget(self.point_tree)
        control_layout.addWidget(self.reset_btn)
        self.update_cp_panel()


        # ----------------------------
        # 좌우 이미지 Layout
        # ----------------------------
        image_layout = QHBoxLayout()

        image_layout.addLayout(before_layout,3)
        image_layout.addLayout(after_layout,3)
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

        self.before_view.set_cv_image(self.before_img)
        self.after_view.set_cv_image(self.after_img)

        self.status.setText("Images Loaded")

    def image_clicked(self, image_name, x, y):

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

    def reset_points(self):
        self.cp_manager.clear()
        self.update_cp_panel()
        self.refresh_points()
        self.status.setText("All Control Points Reset")


def main():

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()