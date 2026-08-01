import cv2

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QColor,
    QBrush,
    QPen,
    QImage,
    QPixmap,
    QFont,
)

from PySide6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QGraphicsEllipseItem,
    QGraphicsSimpleTextItem,
)


class ImageView(QGraphicsView):

    # image_name(T1/T2), x, y
    pointClicked = Signal(str, float, float)

    def __init__(self, image_name=""):

        super().__init__()

        self.image_name = image_name

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.pixmap_item = None
        self.cv_image = None

        # -----------------------------
        # Point 관리
        # -----------------------------
        self.point_items = []

        self.setTransformationAnchor(
            QGraphicsView.AnchorUnderMouse
        )

        self.setResizeAnchor(
            QGraphicsView.AnchorUnderMouse
        )

        self.setDragMode(QGraphicsView.NoDrag)

    # --------------------------------------------------
    # Image
    # --------------------------------------------------

    def set_cv_image(self, image):

        self.cv_image = image

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        h, w, ch = rgb.shape

        bytes_per_line = ch * w

        qimg = QImage(
            rgb.data,
            w,
            h,
            bytes_per_line,
            QImage.Format_RGB888,
        )

        pixmap = QPixmap.fromImage(qimg)

        self.scene.clear()

        self.point_items.clear()

        self.pixmap_item = QGraphicsPixmapItem(pixmap)

        self.scene.addItem(self.pixmap_item)

        self.scene.setSceneRect(
            self.pixmap_item.boundingRect()
        )

        self.fitInView(
            self.scene.sceneRect(),
            Qt.KeepAspectRatio,
        )

    # --------------------------------------------------
    # Point Drawing
    # --------------------------------------------------

    def add_point(self, name, x, y):

        # 고해상도 드론/위성 이미지에서 잘 보이도록 반지름 및 텍스트 크기 확대
        radius = 40

        ellipse = QGraphicsEllipseItem(
            x - radius,
            y - radius,
            radius * 2,
            radius * 2,
        )

        ellipse.setBrush(QBrush(QColor("red")))

        # 원 테두리 선 굵기도 함께 강화
        ellipse.setPen(
            QPen(QColor("white"), 3)
        )

        self.scene.addItem(ellipse)

        text = QGraphicsSimpleTextItem(name)

        # 고해상도 뷰에서도 가장 선명하고 확실하게 보이도록 흰색 ExtraBold 폰트 설정
        text.setBrush(
            QBrush(QColor("white"))
        )
        font = QFont("Arial", 28, QFont.Weight.ExtraBold)
        font.setBold(True)
        text.setFont(font)

        # 텍스트의 크기를 구하여 원의 정중앙에 배치
        text_rect = text.boundingRect()
        text.setPos(
            x - text_rect.width() / 2,
            y - text_rect.height() / 2,
        )

        self.scene.addItem(text)

        self.point_items.append(ellipse)
        self.point_items.append(text)

    # --------------------------------------------------

    def clear_points(self):

        for item in self.point_items:

            self.scene.removeItem(item)

        self.point_items.clear()

    # --------------------------------------------------

    def resizeEvent(self, event):

        super().resizeEvent(event)

        if self.pixmap_item:

            self.fitInView(
                self.scene.sceneRect(),
                Qt.KeepAspectRatio,
            )

    # --------------------------------------------------

    def mousePressEvent(self, event):

        super().mousePressEvent(event)

        if self.pixmap_item is None:
            return

        if event.button() != Qt.LeftButton:
            return

        scene_pos = self.mapToScene(event.pos())

        x = scene_pos.x()
        y = scene_pos.y()

        if x < 0 or y < 0:
            return

        if x >= self.cv_image.shape[1]:
            return

        if y >= self.cv_image.shape[0]:
            return

        self.pointClicked.emit(
            self.image_name,
            x,
            y,
        )