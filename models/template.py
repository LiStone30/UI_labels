# -*- coding: utf-8 -*-
"""控件模板定义与模板管理器"""

from typing import Dict, List, Optional, Any


class Template:
    """控件模板定义"""

    def __init__(self, name: str, display_name: str, default_props: Dict[str, Any] = None):
        self.id = name
        self.name = name
        self.display_name = display_name
        self.default_props = default_props or {}


class TemplateManager:
    """管理所有可用的控件模板"""

    def __init__(self):
        self.templates: Dict[str, Template] = {}
        self._name_to_template: Dict[str, Template] = {}
        self._init_default_templates()

    def _init_default_templates(self):
        default_list = [
            Template("Button", "按钮", {"text": "按钮", "enabled": True, "onClickAction": ""}),
            Template("Label", "标签", {"text": "标签", "font_size": 14, "color": "#333333"}),
            Template("EditText", "输入框", {"placeholder": "请输入", "text": "", "maxLength": 255}),
            Template("CheckBox", "复选框", {"text": "复选框", "checked": False}),
            Template("RadioButton", "单选框", {"group": "", "text": "单选框", "selected": False}),
            Template("Switch", "开关", {"onText": "开", "offText": "关", "value": False}),
            Template("Slider", "滑块", {"min": 0, "max": 100, "currentValue": 50}),
            Template("ImageView", "图片视图", {"src": "", "scaleType": "centerCrop"}),
            Template("ListView", "列表", {"itemTemplate": "", "dataSource": ""}),
            Template("Container", "容器", {"layout": "vertical", "children": []}),
            Template("Panel", "折叠面板", {"title": "面板", "expanded": True, "collapsedHeight": 0}),
            Template("Dialog", "弹窗", {"title": "提示", "buttons": ["确定"], "visible": False}),
        ]
        for t in default_list:
            self.templates[t.id] = t
            self._name_to_template[t.name] = t

    def add_template(self, template: Template):
        self.templates[template.id] = template
        self._name_to_template[template.name] = template

    def get_template(self, tid: str) -> Optional[Template]:
        return self.templates.get(tid)

    def get_template_by_name(self, name: str) -> Optional[Template]:
        return self._name_to_template.get(name)

    def get_all(self) -> List[Template]:
        return list(self.templates.values())


# 全局单例
template_manager = TemplateManager()