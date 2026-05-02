# UI Labels - UI逆向标注工具

一个基于 PySide6 的 UI 逆向标注工具，用于在图片上标注 UI 控件位置和结构树。

## 功能

- 打开图片并在其上绘制矩形标注框
- 支持多种控件模板（按钮、标签、图片视图、输入框）
- 树形结构展示控件层级关系
- 支持拖拽重组控件父子关系
- 属性编辑面板（名称、模板、位置/大小百分比）
- 层级过滤显示
- 保存/加载标注结构为 JSON 文件

## 安装

```bash
pip install -e .
```

或使用 UV：

```bash
uv sync
```

## 使用

```bash
python -m ui_labels
```

## 项目结构

```
ui_labels/
├── __init__.py              # 包初始化
├── __main__.py              # 入口点
├── main_window.py           # 主窗口
├── tree_model.py            # 树形模型（支持拖拽）
├── models/
│   ├── __init__.py
│   ├── template.py          # 控件模板定义与管理
│   └── widget_node.py       # UI节点数据模型
└── graphics/
    ├── __init__.py
    ├── image_scene.py       # 图形场景
    └── resizable_rect.py    # 可拖动缩放的矩形项
```

# 有些BUG 目前够用了
不要拖动画面中的矩形边框，会出BUG
拖动画面中的矩形边框，属性栏不会更新
点击矩形边框，不对提示UI节点
如果加载现有结构 边框位置不对，需要手动调整。大概率是负值之类的错误
