# -*- coding: utf-8 -*-
"""管理图片显示和所有矩形项的图形场景"""

from typing import Dict, Optional, Callable

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPixmap, QPen, QColor, QBrush
from PySide6.QtWidgets import QGraphicsScene

from models.widget_node import UIWidgetNode
from .resizable_rect import ResizableRectItem


class ImageScene(QGraphicsScene):
    """管理图片显示和所有矩形项"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_pixmap: Optional[QPixmap] = None
        self.pixmap_item = None
        self.rect_items: Dict[str, ResizableRectItem] = {}
        self.node_updated_callback: Optional[Callable[[UIWidgetNode], None]] = None

        # 矩形绘制状态
        self.drawing = False
        self.start_point = QPointF()
        self.temp_rect_item = None

    def setImage(self, pixmap: QPixmap):
        """设置要显示的背景图片"""
        self.clear()
        self.current_pixmap = pixmap
        self.pixmap_item = self.addPixmap(pixmap)
        self.setSceneRect(0, 0, pixmap.width(), pixmap.height())
        self.rect_items.clear()

    def addNode(self, node: UIWidgetNode) -> ResizableRectItem:
        """添加节点对应的矩形项"""
        rect_item = ResizableRectItem(node, self)
        self.addItem(rect_item)
        rect_item.updateGeometry()
        self.rect_items[node.id] = rect_item
        return rect_item

    def removeNode(self, node_id: str):
        """移除指定节点对应的矩形项"""
        if node_id in self.rect_items:
            self.removeItem(self.rect_items[node_id])
            del self.rect_items[node_id]

    def updateAllRects(self):
        """更新所有矩形项的几何位置"""
        for rect_item in self.rect_items.values():
            rect_item.updateGeometry()

    # ---------- 鼠标事件：矩形绘制 ----------

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.current_pixmap:
            # 未选中任何现有项时，开始绘制新矩形
            if not self.selectedItems():
                self.drawing = True
                self.start_point = event.scenePos()
                self.temp_rect_item = self.addRect(
                    QRectF(self.start_point, self.start_point),
                    QPen(QColor(255, 0, 0, 200), 2, Qt.SolidLine),
                    QBrush(QColor(255, 0, 0, 50)),
                )
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drawing and self.temp_rect_item:
            rect = QRectF(self.start_point, event.scenePos()).normalized()
            self.temp_rect_item.setRect(rect)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.drawing and self.temp_rect_item and self.current_pixmap:
            rect = self.temp_rect_item.rect()
            self.removeItem(self.temp_rect_item)
            self.temp_rect_item = None

            # 转换为百分比坐标
            img_w = self.current_pixmap.width()
            img_h = self.current_pixmap.height()
            if img_w > 0 and img_h > 0 and rect.width() > 5 and rect.height() > 5:
                x = rect.x() / img_w
                y = rect.y() / img_h
                w = rect.width() / img_w
                h = rect.height() / img_h
                # 请求创建新控件（由父级处理）
                if self.parent() and hasattr(self.parent(), "requestCreateWidget"):
                    self.parent().requestCreateWidget((x, y, w, h))
        self.drawing = False
        super().mouseReleaseEvent(event)