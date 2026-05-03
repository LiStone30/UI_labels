# -*- coding: utf-8 -*-
"""主窗口：UI逆向标注工具"""

import json
from typing import Optional

from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QAction, QPainter, QPixmap
from PySide6.QtWidgets import (
    QMainWindow,
    QGraphicsView,
    QDockWidget,
    QTreeView,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDoubleSpinBox,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QInputDialog,
    QMenu,
    QToolBar,
    QStatusBar,
)


from models import UIWidgetNode, template_manager, TemplateManager, Template
from graphics import ImageScene, ResizableRectItem
from tree_model import WidgetTreeModel
from logger import logger


class MainWindow(QMainWindow):
    """UI逆向标注工具主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("UI逆向标注工具")
        self.resize(1200, 800)
        logger.info("MainWindow initialized")

        # 数据
        self.current_image_path: Optional[str] = None
        self.ui_tree_root = UIWidgetNode("Root", "", (0, 0, 1, 1))  # 根节点不可见
        self.tree_model = WidgetTreeModel(self.ui_tree_root)
        self.current_filter_depth: Optional[int] = None  # None表示全部

        self.init_ui()
        self.connect_signals()

    # ---------- UI 初始化 ----------

    def init_ui(self):
        """构建所有UI组件"""
        # ---- 中心：图形视图 ----
        self.scene = ImageScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        self.setCentralWidget(self.view)

        # ---- 文件工具栏 ----
        file_toolbar = self.addToolBar("文件")
        open_action = QAction("打开图片", self)
        open_action.triggered.connect(self.open_image)
        file_toolbar.addAction(open_action)

        save_action = QAction("保存结构", self)
        save_action.triggered.connect(self.save_structure)
        file_toolbar.addAction(save_action)

        load_action = QAction("加载结构", self)
        load_action.triggered.connect(self.load_structure)
        file_toolbar.addAction(load_action)

        # ---- 右侧：UI结构树 ----
        right_dock = QDockWidget("UI结构树", self)
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.tree_model)
        self.tree_view.setHeaderHidden(False)
        self.tree_view.setDragEnabled(True)
        self.tree_view.setAcceptDrops(True)
        self.tree_view.setDropIndicatorShown(True)
        self.tree_view.setDragDropMode(QTreeView.InternalMove)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.on_tree_context_menu)
        right_dock.setWidget(self.tree_view)
        self.addDockWidget(Qt.RightDockWidgetArea, right_dock)

        # ---- 底部：模板列表 + 属性编辑 ----
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)

        # 模板列表
        template_group = QGroupBox("控件模板")
        template_layout = QVBoxLayout()
        self.template_list = QListWidget()
        for t in template_manager.get_all():
            item = QListWidgetItem(t.display_name)
            item.setData(Qt.UserRole, t.id)
            self.template_list.addItem(item)
        template_layout.addWidget(self.template_list)
        template_group.setLayout(template_layout)

        # 属性编辑
        prop_group = QGroupBox("属性")
        prop_layout = QFormLayout()

        self.prop_name_edit = QLineEdit()
        self.prop_name_edit.setPlaceholderText("控件名称")
        prop_layout.addRow("名称:", self.prop_name_edit)

        self.prop_template_combo = QComboBox()
        for t in template_manager.get_all():
            self.prop_template_combo.addItem(t.display_name, t.id)
        prop_layout.addRow("模板:", self.prop_template_combo)

        self.prop_x = QDoubleSpinBox()
        self.prop_x.setRange(0, 1)
        self.prop_x.setSingleStep(0.01)
        self.prop_y = QDoubleSpinBox()
        self.prop_y.setRange(0, 1)
        self.prop_y.setSingleStep(0.01)
        self.prop_w = QDoubleSpinBox()
        self.prop_w.setRange(0, 1)
        self.prop_w.setSingleStep(0.01)
        self.prop_h = QDoubleSpinBox()
        self.prop_h.setRange(0, 1)
        self.prop_h.setSingleStep(0.01)
        prop_layout.addRow("x:", self.prop_x)
        prop_layout.addRow("y:", self.prop_y)
        prop_layout.addRow("w:", self.prop_w)
        prop_layout.addRow("h:", self.prop_h)

        self.update_prop_btn = QPushButton("更新")
        prop_layout.addRow(self.update_prop_btn)

        prop_group.setLayout(prop_layout)

        bottom_layout.addWidget(template_group)
        bottom_layout.addWidget(prop_group)

        # 使用状态栏，但不覆盖底部dock，用setStatusBar替代
        # 这里我们将bottom_widget放到一个dock中
        bottom_dock = QDockWidget("控件编辑", self)
        bottom_dock.setWidget(bottom_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, bottom_dock)

        # ---- 层级控制工具栏 ----
        level_toolbar = self.addToolBar("层级")
        self.level_filter_btn = QPushButton("只显示当前层级")
        level_toolbar.addWidget(self.level_filter_btn)
        self.level_up_btn = QPushButton("上一层级")
        level_toolbar.addWidget(self.level_up_btn)
        self.level_reset_btn = QPushButton("显示全部")
        level_toolbar.addWidget(self.level_reset_btn)

        # 状态栏
        status_bar = QStatusBar()
        status_bar.showMessage("就绪")
        self.setStatusBar(status_bar)


        # 辅助变量
        self.current_drawing_bbox = None

    def connect_signals(self):
        """连接信号与槽"""
        self.tree_view.selectionModel().selectionChanged.connect(self.on_node_selected)
        self.update_prop_btn.clicked.connect(self.update_current_node)
        self.level_filter_btn.clicked.connect(self.show_only_current_level)
        self.level_up_btn.clicked.connect(self.go_up_one_level)
        self.level_reset_btn.clicked.connect(self.reset_level_filter)
        self.scene.node_updated_callback = self.on_node_updated

    # ---------- 图片操作 ----------

    def open_image(self):
        """打开并显示图片"""
        path, _ = QFileDialog.getOpenFileName(
            self, "打开图片", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not path:
            return
        self.current_image_path = path
        pixmap = QPixmap(path)
        if pixmap.isNull():
            QMessageBox.warning(self, "错误", "无法加载图片")
            return
        self.scene.setImage(pixmap)
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        self.rebuild_scene_rects()

    def rebuild_scene_rects(self):
        """根据当前树重新生成所有矩形项"""
        for rect_item in self.scene.rect_items.values():
            self.scene.removeItem(rect_item)
        self.scene.rect_items.clear()

        def add_nodes(node: UIWidgetNode):
            for child in node.children:
                self.scene.addNode(child)
                add_nodes(child)

        add_nodes(self.ui_tree_root)

    # ---------- 控件创建 ----------

    def requestCreateWidget(self, bbox_percent):
        """由场景调用，弹出对话框并创建控件"""
        if not self.scene.current_pixmap:
            return
        selected_template = self.template_list.currentItem()
        if not selected_template:
            QMessageBox.information(self, "提示", "请先选择一个模板")
            return
        template_id = selected_template.data(Qt.UserRole)
        template = template_manager.get_template(template_id)
        name, ok = QInputDialog.getText(
            self, "控件名称", "请输入控件名:", text=template.display_name
        )
        if not ok or not name:
            name = template.display_name

        node = UIWidgetNode(name, template_id, bbox_percent)
        node.props = template.default_props.copy()
        node.parent = self.ui_tree_root
        self.ui_tree_root.children.append(node)

        self.tree_model.layoutChanged.emit()
        self.scene.addNode(node)
        self.select_node_in_tree(node)

    def select_node_in_tree(self, node: UIWidgetNode):
        """在树视图中选中指定节点"""

        def find_idx(parent_idx: QModelIndex, target_node):
            for row in range(self.tree_model.rowCount(parent_idx)):
                idx = self.tree_model.index(row, 0, parent_idx)
                n = self.tree_model.getNode(idx)
                if n == target_node:
                    return idx
                child_idx = find_idx(idx, target_node)
                if child_idx.isValid():
                    return child_idx
            return QModelIndex()

        idx = find_idx(QModelIndex(), node)
        if idx.isValid():
            self.tree_view.setCurrentIndex(idx)
            self.tree_view.expand(idx)

    # ---------- 节点选中/编辑 ----------

    def on_node_selected(self, selected, deselected):
        """树选中项改变"""
        logger.info(f"on_node_selected() -> called, selected={selected}, deselected={deselected}")
        indexes = selected.indexes()
        logger.info(f"on_node_selected() -> indexes count: {len(indexes)}")
        if indexes:
            idx = indexes[0]
            logger.info(f"on_node_selected() -> idx={idx}, idx.isValid()={idx.isValid()}")
            node = self.tree_model.getNode(idx)
            logger.info(f"on_node_selected() -> node={node}, node.name={node.name if node else 'None'}")
            logger.info(f"on_node_selected() -> self.ui_tree_root={self.ui_tree_root}")
            if node and node != self.ui_tree_root:
                logger.info(f"on_node_selected() -> calling show_node_properties")
                self.show_node_properties(node)
                for rid, ritem in self.scene.rect_items.items():
                    ritem.setSelected(ritem.node.id == node.id)
            else:
                logger.info(f"on_node_selected() -> node is None or is root, calling clear_property_panel")
                self.clear_property_panel()

    def on_tree_context_menu(self, pos):
        """右键菜单"""
        idx = self.tree_view.indexAt(pos)
        if not idx.isValid():
            return
        node = self.tree_model.getNode(idx)
        if node is None or node == self.ui_tree_root:
            return
        menu = QMenu()
        delete_action = menu.addAction("删除节点")
        action = menu.exec(self.tree_view.viewport().mapToGlobal(pos))
        if action == delete_action:
            self.delete_node(node)

    def delete_node(self, node: UIWidgetNode):
        """删除节点"""
        logger.info(f"delete_node() -> deleting node: {node.name}, id={node.id}")
        parent = node.parent
        if parent is None:
            logger.warning("delete_node() -> cannot delete root node")
            return

        self.tree_view.selectionModel().blockSignals(True)
        self.tree_view.setCurrentIndex(QModelIndex())

        row = parent.children.index(node)
        if parent == self.ui_tree_root:
            parent_idx = QModelIndex()
        else:
            parent_row = parent.parent.children.index(parent) if parent.parent else 0
            parent_idx = self.tree_model.createIndex(parent_row, 0, parent)
        self.tree_model.beginRemoveRows(parent_idx, row, row)
        parent.children.remove(node)
        self.tree_model.endRemoveRows()
        if node.id in self.scene.rect_items:
            rect_item = self.scene.rect_items.pop(node.id)
            rect_item.setVisible(False)
            self.scene.removeItem(rect_item)
        self.clear_property_panel()
        self.tree_view.selectionModel().blockSignals(False)
        logger.info(f"delete_node() -> node deleted successfully")

    def show_node_properties(self, node: UIWidgetNode):
        """在属性面板中显示节点信息"""
        logger.info(f"show_node_properties() -> node.name={node.name}, node.template_id={node.template_id}")
        self.prop_name_edit.setText(node.name)
        template = template_manager.get_template(node.template_id)
        logger.info(f"show_node_properties() -> template lookup: template_manager.get_template('{node.template_id}') = {template}")
        if template:
            idx = self.prop_template_combo.findData(template.id)
            logger.info(f"show_node_properties() -> combo idx by data({template.id}): {idx}")
            if idx >= 0:
                self.prop_template_combo.setCurrentIndex(idx)
            else:
                idx_text = self.prop_template_combo.findText(template.display_name)
                logger.info(f"show_node_properties() -> combo idx by text({template.display_name}): {idx_text}")
                if idx_text >= 0:
                    self.prop_template_combo.setCurrentIndex(idx_text)
        else:
            logger.warning(f"show_node_properties() -> template not found for node.template_id={node.template_id}")
            logger.info(f"show_node_properties() -> available templates: {[t.id for t in template_manager.get_all()]}")
        x, y, w, h = node.bbox
        self.prop_x.setValue(x)
        self.prop_y.setValue(y)
        self.prop_w.setValue(w)
        self.prop_h.setValue(h)

    def clear_property_panel(self):
        """清空属性面板"""
        self.prop_name_edit.clear()
        self.prop_x.setValue(0)
        self.prop_y.setValue(0)
        self.prop_w.setValue(0)
        self.prop_h.setValue(0)

    def update_current_node(self):
        """用属性面板的值更新当前选中节点"""
        idx = self.tree_view.currentIndex()
        if not idx.isValid():
            return
        node = self.tree_model.getNode(idx)
        if node and node != self.ui_tree_root:
            node.name = self.prop_name_edit.text()
            node.template_id = self.prop_template_combo.currentData()
            node.bbox = (
                self.prop_x.value(),
                self.prop_y.value(),
                self.prop_w.value(),
                self.prop_h.value(),
            )
            if node.id in self.scene.rect_items:
                self.scene.rect_items[node.id].updateGeometry()
            self.tree_model.dataChanged.emit(idx, idx)
            self.on_node_updated(node)

    def on_node_updated(self, node: UIWidgetNode):
        """节点更新回调（可扩展）"""
        pass

    # ---------- 保存 / 加载 ----------

    def save_structure(self):
        """保存标注结构到JSON文件"""
        if not self.current_image_path:
            QMessageBox.warning(self, "警告", "请先打开图片")
            return
        from models.data_schema import structure_to_schema, save_structure_to_json
        schema = structure_to_schema(self.current_image_path, self.ui_tree_root)
        path, _ = QFileDialog.getSaveFileName(self, "保存结构", "", "JSON (*.json)")
        if path:
            save_structure_to_json(schema, path)
            QMessageBox.information(self, "成功", "结构已保存")

    def load_structure(self):
        """从JSON文件加载标注结构"""
        path, _ = QFileDialog.getOpenFileName(self, "加载结构", "", "JSON (*.json)")
        if not path:
            return
        from models.data_schema import load_structure_from_json, schema_to_structure
        
        # 加载并验证数据
        schema = load_structure_from_json(path)
        img_path, self.ui_tree_root = schema_to_structure(schema)

        # 先清空旧数据
        for rect_item in list(self.scene.rect_items.values()):
            self.scene.removeItem(rect_item)
        self.scene.rect_items.clear()

        # 重建树模型
        self.tree_model = WidgetTreeModel(self.ui_tree_root)
        try:
            self.tree_view.selectionModel().selectionChanged.disconnect(self.on_node_selected)
        except Exception:
            pass
        self.tree_view.setModel(self.tree_model)
        self.tree_view.selectionModel().selectionChanged.connect(self.on_node_selected)

        # 加载图片
        if img_path:
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                self.current_image_path = img_path
                self.scene.setImage(pixmap)
                self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

        # 重建场景矩形
        self.rebuild_scene_rects()
        QMessageBox.information(self, "成功", "结构已加载")

    # ---------- 层级过滤 ----------

    def show_only_current_level(self):
        """只显示与当前选中节点同一层级的节点"""
        current_idx = self.tree_view.currentIndex()
        if not current_idx.isValid():
            return
        current_node = self.tree_model.getNode(current_idx)
        if current_node == self.ui_tree_root:
            return
        depth = self.get_node_depth(current_node)
        self.filter_tree_by_depth(depth)

    def go_up_one_level(self):
        """显示上一层级（深度减1）"""
        if self.current_filter_depth is None:
            idx = self.tree_view.currentIndex()
            if idx.isValid():
                node = self.tree_model.getNode(idx)
                depth = self.get_node_depth(node)
                self.filter_tree_by_depth(depth - 1)
            else:
                self.filter_tree_by_depth(0)
        else:
            new_depth = self.current_filter_depth - 1
            if new_depth >= 0:
                self.filter_tree_by_depth(new_depth)
            else:
                self.reset_level_filter()

    def reset_level_filter(self):
        """重置层级过滤，显示全部"""
        self.current_filter_depth = None
        self.tree_view.setModel(self.tree_model)
        self.tree_view.expandAll()
        self.scene.clearFilter()

    def filter_tree_by_depth(self, depth: int):
        """构建一个只显示指定深度节点的临时模型"""
        self.current_filter_depth = depth
        filtered_root = UIWidgetNode("FilteredRoot", "", (0, 0, 1, 1))

        def copy_node_with_depth(
            node: UIWidgetNode, current_depth: int, target_depth: int, parent_copy
        ):
            if current_depth == target_depth:
                copy = UIWidgetNode(node.name, node.template_id, node.bbox)
                copy.id = node.id
                copy.props = node.props.copy()
                copy.parent = parent_copy
                parent_copy.children.append(copy)
            elif current_depth < target_depth:
                for child in node.children:
                    copy_node_with_depth(child, current_depth + 1, target_depth, parent_copy)

        for child in self.ui_tree_root.children:
            copy_node_with_depth(child, 1, depth, filtered_root)

        filtered_model = WidgetTreeModel(filtered_root)
        try:
            self.tree_view.selectionModel().selectionChanged.disconnect(self.on_node_selected)
        except Exception:
            pass
        self.tree_view.setModel(filtered_model)
        self.tree_view.selectionModel().selectionChanged.connect(self.on_node_selected)

        self.scene.filterByDepth(depth, self.ui_tree_root)

    @staticmethod
    def get_node_depth(node: UIWidgetNode) -> int:
        """计算节点深度"""
        depth = 0
        cur = node
        while cur.parent and cur.parent.parent:  # 不算Root本身
            depth += 1
            cur = cur.parent
        return depth + 1  # 根的直接孩子深度为1