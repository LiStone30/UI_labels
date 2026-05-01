# -*- coding: utf-8 -*-
"""支持拖拽重组的树形模型"""

from typing import Optional

from PySide6.QtCore import (
    Qt,
    QModelIndex,
    QAbstractItemModel,
    QMimeData,
    QByteArray,
    QDataStream,
    QIODevice,
)

from models.widget_node import UIWidgetNode
from models.template import template_manager


class WidgetTreeModel(QAbstractItemModel):
    """支持拖拽重组的树形模型"""

    def __init__(self, root_node: UIWidgetNode, parent=None):
        super().__init__(parent)
        self.root_node = root_node

    # ---------- QAbstractItemModel 接口 ----------

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parent_node = self.getNode(parent)
        if row < len(parent_node.children):
            child = parent_node.children[row]
            return self.createIndex(row, column, child)
        return QModelIndex()

    def parent(self, index):
        node = self.getNode(index)
        if node is None or node.parent is None:
            return QModelIndex()
        parent_node = node.parent
        grandparent = parent_node.parent
        row = grandparent.children.index(parent_node) if grandparent else 0
        return self.createIndex(row, 0, parent_node)

    def rowCount(self, parent=QModelIndex()):
        node = self.getNode(parent)
        return len(node.children)

    def columnCount(self, parent=QModelIndex()):
        return 2  # 名称和类型

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        node = self.getNode(index)
        if role in (Qt.DisplayRole, Qt.EditRole):
            if index.column() == 0:
                return node.name
            else:
                template = template_manager.get_template(node.template_id)
                return template.display_name if template else "Unknown"
        elif role == Qt.UserRole:
            return node.id
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole and index.column() == 0:
            node = self.getNode(index)
            node.name = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index):
        default_flags = QAbstractItemModel.flags(self, index)
        if index.isValid():
            return (
                default_flags
                | Qt.ItemIsDragEnabled
                | Qt.ItemIsDropEnabled
                | Qt.ItemIsEditable
            )
        else:
            return default_flags | Qt.ItemIsDropEnabled

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return ["名称", "类型"][section]
        return None

    # ---------- 拖拽支持 ----------

    def supportedDragActions(self):
        return Qt.MoveAction

    def mimeTypes(self):
        return ["application/x-uiwidgetnode"]

    def mimeData(self, indexes):
        if not indexes:
            return None
        data = QMimeData()
        encoded = QByteArray()
        stream = QDataStream(encoded, QIODevice.WriteOnly)
        for idx in indexes:
            if idx.isValid():
                node = self.getNode(idx)
                stream.writeQString(node.id)
        data.setData("application/x-uiwidgetnode", encoded)
        return data

    def dropMimeData(self, data, action, row, column, parent):
        if action == Qt.IgnoreAction:
            return True
        if not data.hasFormat("application/x-uiwidgetnode"):
            return False
        encoded = data.data("application/x-uiwidgetnode")
        stream = QDataStream(encoded, QIODevice.ReadOnly)
        dropped_ids = []
        while not stream.atEnd():
            dropped_ids.append(stream.readQString())

        target_parent_node = self.getNode(parent)
        if target_parent_node is None:
            target_parent_node = self.root_node

        for node_id in dropped_ids:
            source_node = self.findNodeById(node_id)
            if (
                source_node
                and source_node != target_parent_node
                and not self.isAncestor(source_node, target_parent_node)
            ):
                old_parent = source_node.parent
                if old_parent:
                    old_parent.children.remove(source_node)
                    self.beginRemoveRows(
                        self.createIndex(
                            old_parent.parent.children.index(old_parent)
                            if old_parent.parent
                            else 0,
                            0,
                            old_parent,
                        ),
                        old_parent.children.index(source_node)
                        if source_node in old_parent.children
                        else 0,
                        0,
                    )

                new_row = row if row != -1 else len(target_parent_node.children)
                self.beginInsertRows(parent, new_row, new_row)
                source_node.parent = target_parent_node
                target_parent_node.children.insert(new_row, source_node)
                self.endInsertRows()

                if old_parent:
                    self.endRemoveRows()

        self.layoutChanged.emit()
        return True

    # ---------- 工具方法 ----------

    def getNode(self, index: QModelIndex) -> Optional[UIWidgetNode]:
        if not index.isValid():
            return self.root_node
        return index.internalPointer() if index.internalPointer() else self.root_node

    def findNodeById(self, node_id: str, start_node=None) -> Optional[UIWidgetNode]:
        if start_node is None:
            start_node = self.root_node
        if start_node.id == node_id:
            return start_node
        for child in start_node.children:
            found = self.findNodeById(node_id, child)
            if found:
                return found
        return None

    @staticmethod
    def isAncestor(node, potential_descendant) -> bool:
        while potential_descendant.parent:
            if potential_descendant.parent == node:
                return True
            potential_descendant = potential_descendant.parent
        return False