# -*- coding: utf-8 -*-
"""带调整大小控制点的矩形图形项"""

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QColor, QBrush
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem

from models.widget_node import UIWidgetNode


class ResizableRectItem(QGraphicsRectItem):
    """带有调整大小控制点的矩形项，坐标存储为百分比，但视觉上映射到图片坐标"""

    def __init__(self, node: UIWidgetNode, scene_ref, parent=None):
        super().__init__(parent)
        self.node = node
        self.scene_ref = scene_ref  # 用于获取图片尺寸

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setPen(QPen(QColor(0, 255, 0, 200), 2, Qt.DashLine))
        self.setBrush(QBrush(QColor(0, 255, 0, 30)))
        self.setZValue(1)
        self._resize_handles = []  # 简化，实际可实现缩放手柄，此处省略

    def updateGeometry(self):
        """根据节点的百分比bbox更新图形位置和大小"""
        if not self.scene_ref or not self.scene_ref.current_pixmap:
            return
        img_w = self.scene_ref.current_pixmap.width()
        img_h = self.scene_ref.current_pixmap.height()
        x, y, w, h = self.node.bbox
        rect = QRectF(x * img_w, y * img_h, w * img_w, h * img_h)
        self.setRect(rect)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # 移动后更新节点百分比坐标
            new_pos = value
            old_rect = self.rect()
            new_rect = QRectF(new_pos.x(), new_pos.y(), old_rect.width(), old_rect.height())
            self._update_node_bbox_from_rect(new_rect)
        elif change == QGraphicsItem.ItemTransformChange:
            # 缩放处理（如果实现了手柄）
            pass
        return super().itemChange(change, value)

    def _update_node_bbox_from_rect(self, rect: QRectF):
        if not self.scene_ref or not self.scene_ref.current_pixmap:
            return
        img_w = self.scene_ref.current_pixmap.width()
        img_h = self.scene_ref.current_pixmap.height()
        if img_w == 0 or img_h == 0:
            return
        x = rect.x() / img_w
        y = rect.y() / img_h
        w = rect.width() / img_w
        h = rect.height() / img_h
        self.node.bbox = (x, y, w, h)
        if self.scene_ref.node_updated_callback:
            self.scene_ref.node_updated_callback(self.node)