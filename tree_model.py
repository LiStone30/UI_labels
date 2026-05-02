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
from logger import logger


class WidgetTreeModel(QAbstractItemModel):
    """支持拖拽重组的树形模型"""

    def __init__(self, root_node: UIWidgetNode, parent=None):
        super().__init__(parent)
        self.root_node = root_node
        logger.info(f"WidgetTreeModel initialized with root: {root_node.name}")

    # ---------- QAbstractItemModel 接口 ----------

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parent_node = self.getNode(parent)
        if row < len(parent_node.children):
            child = parent_node.children[row]
            logger.debug(f"index() -> row={row}, col={column}, parent={parent_node.name}, child={child.name}")
            return self.createIndex(row, column, child)
        return QModelIndex()

    def parent(self, index):
        node = self.getNode(index)
        if node is None or node.parent is None:
            logger.debug(f"parent() -> invalid (node={node})")
            return QModelIndex()
        parent_node = node.parent
        grandparent = parent_node.parent
        row = grandparent.children.index(parent_node) if grandparent else 0
        logger.debug(f"parent() -> node={node.name}, parent_node={parent_node.name}, row={row}")
        return self.createIndex(row, 0, parent_node)

    def rowCount(self, parent=QModelIndex()):
        node = self.getNode(parent)
        count = len(node.children)
        logger.debug(f"rowCount() -> parent={node.name}, count={count}")
        return count

    def columnCount(self, parent=QModelIndex()):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        node = self.getNode(index)
        if role in (Qt.DisplayRole, Qt.EditRole):
            if index.column() == 0:
                return node.name
            else:
                template = template_manager.get_template(node.template_id)
                return template.display_name if template else f"Unknown({node.template_id})"
        elif role == Qt.UserRole:
            return node.id
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole and index.column() == 0:
            node = self.getNode(index)
            old_name = node.name
            node.name = value
            logger.info(f"setData() -> node={old_name} renamed to '{value}'")
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index):
        default_flags = QAbstractItemModel.flags(self, index)
        if index.isValid():
            node = self.getNode(index)
            result = (
                default_flags
                | Qt.ItemIsDragEnabled
                | Qt.ItemIsDropEnabled
                | Qt.ItemIsEditable
            )
            logger.info(f"flags() -> valid index, node={node.name}, drag={'Y' if result & Qt.ItemIsDragEnabled else 'N'}, drop={'Y' if result & Qt.ItemIsDropEnabled else 'N'}")
            return result
        else:
            logger.info("flags() -> invalid index (root), drop=Y")
            return default_flags | Qt.ItemIsDropEnabled

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return ["名称", "类型"][section]
        return None

    # ---------- 拖拽支持 ----------

    def supportedDragActions(self):
        return Qt.MoveAction

    def supportedDropActions(self):
        return Qt.MoveAction

    def mimeTypes(self):
        return ["application/x-uiwidgetnode"]

    def mimeData(self, indexes):
        if not indexes:
            logger.warning("mimeData() -> called with empty indexes")
            return None
        data = QMimeData()
        encoded = QByteArray()
        stream = QDataStream(encoded, QIODevice.WriteOnly)
        dragged_nodes = []
        for idx in indexes:
            if idx.isValid():
                node = self.getNode(idx)
                stream.writeQString(node.id)
                dragged_nodes.append(node.name)
        data.setData("application/x-uiwidgetnode", encoded)
        logger.info(f"mimeData() -> dragged nodes: {dragged_nodes}, ids count={len(dragged_nodes)}")
        return data

    def dropMimeData(self, data, action, row, column, parent):
        logger.warning(f"!!! dropMimeData() WAS CALLED - this is unexpected if not logged before !!!")
        logger.info(f"=== dropMimeData called ===")
        logger.info(f"  action={action}, row={row}, column={column}, parent={parent}")
        logger.info(f"  parent.isValid()={parent.isValid()}")
        if parent.isValid():
            parent_node = self.getNode(parent)
            logger.info(f"  parent_node={parent_node.name}, parent_node.id={parent_node.id}")
            parent_flags = self.flags(parent)
            logger.info(f"  parent_flags={parent_flags}, ItemIsDropEnabled={bool(parent_flags & Qt.ItemIsDropEnabled)}")

        if action == Qt.IgnoreAction:
            logger.debug("dropMimeData -> IgnoreAction, returning True")
            return True

        if not data.hasFormat("application/x-uiwidgetnode"):
            logger.warning("dropMimeData -> wrong mime type, returning False")
            return False

        encoded = data.data("application/x-uiwidgetnode")
        stream = QDataStream(encoded, QIODevice.ReadOnly)
        dropped_ids = []
        while not stream.atEnd():
            dropped_ids.append(stream.readQString())

        logger.info(f"dropMimeData -> dropped ids (before dedup): {dropped_ids}")
        dropped_ids = list(dict.fromkeys(dropped_ids))
        logger.info(f"dropMimeData -> dropped ids (after dedup): {dropped_ids}")

        target_parent_node = self.getNode(parent)
        if target_parent_node is None:
            target_parent_node = self.root_node

        logger.info(f"dropMimeData -> target_parent: {target_parent_node.name} (id={target_parent_node.id})")

        success_count = 0
        for node_id in dropped_ids:
            source_node = self.findNodeById(node_id)
            logger.info(f"  Processing node_id={node_id}, found={source_node is not None}")
            if source_node:
                logger.info(f"  source_node: {source_node.name}, parent={source_node.parent.name if source_node.parent else 'None'}")

            if not source_node:
                logger.warning(f"  Skipping: source node not found for id={node_id}")
                continue

            if source_node == target_parent_node:
                logger.warning(f"  Skipping: cannot drop node onto itself ({source_node.name})")
                continue

            if self.isAncestor(source_node, target_parent_node):
                logger.warning(f"  Skipping: target is descendant of source ({source_node.name} is ancestor of {target_parent_node.name})")
                continue

            old_parent = source_node.parent
            if old_parent is None:
                logger.warning(f"  Skipping: source node has no parent ({source_node.name})")
                continue

            old_row = old_parent.children.index(source_node) if source_node in old_parent.children else -1
            if old_row == -1:
                logger.warning(f"  Skipping: source node not found in old parent's children ({source_node.name})")
                continue

            new_row = row if row != -1 else len(target_parent_node.children)

            if old_parent == target_parent_node:
                logger.info(f"  Moving within same parent: {old_parent.name}, from row={old_row} to row={new_row}")
                self.beginMoveRows(parent, old_row, old_row, parent, new_row)
                source_node.parent = target_parent_node
                old_parent.children.remove(source_node)
                old_parent.children.insert(new_row, source_node)
                self.endMoveRows()
            else:
                logger.info(f"  Moving from {old_parent.name} to {target_parent_node.name}")
                self.beginRemoveRows(
                    self.createIndex(0, 0, old_parent),
                    old_row,
                    old_row,
                )
                old_parent.children.remove(source_node)
                self.endRemoveRows()

                self.beginInsertRows(parent, new_row, new_row)
                source_node.parent = target_parent_node
                target_parent_node.children.insert(new_row, source_node)
                self.endInsertRows()

            success_count += 1
            logger.info(f"  Successfully moved {source_node.name} to {target_parent_node.name}")

        logger.info(f"=== dropMimeData complete: {success_count}/{len(dropped_ids)} nodes moved ===")
        self.layoutChanged.emit()
        logger.info(f"dropMimeData returning True (success)")
        return True

    # ---------- 工具方法 ----------

    def getNode(self, index: QModelIndex) -> Optional[UIWidgetNode]:
        if not index.isValid():
            logger.debug(f"getNode() -> returning root_node (invalid index)")
            return self.root_node
        node = index.internalPointer() if index.internalPointer() else self.root_node
        logger.debug(f"getNode() -> index valid, node={node.name if node else 'None'}")
        return node

    def findNodeById(self, node_id: str, start_node=None) -> Optional[UIWidgetNode]:
        if start_node is None:
            start_node = self.root_node
        if start_node.id == node_id:
            logger.debug(f"findNodeById({node_id}) -> found at start_node={start_node.name}")
            return start_node
        for child in start_node.children:
            found = self.findNodeById(node_id, child)
            if found:
                return found
        logger.debug(f"findNodeById({node_id}) -> not found under {start_node.name}")
        return None

    def isAncestor(self, node, potential_descendant) -> bool:
        if node is None or potential_descendant is None:
            return False
        current = potential_descendant.parent
        depth = 0
        max_depth = 100
        while current is not None and depth < max_depth:
            if current == node:
                logger.debug(f"isAncestor({node.name}, {potential_descendant.name}) -> True (found at depth {depth})")
                return True
            current = current.parent
            depth += 1
        logger.debug(f"isAncestor({node.name}, {potential_descendant.name}) -> False")
        return False