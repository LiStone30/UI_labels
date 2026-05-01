# -*- coding: utf-8 -*-
"""控件模板定义与模板管理器"""

import uuid
from typing import Dict, List, Optional, Any


class Template:
    """控件模板定义"""

    def __init__(self, name: str, display_name: str, default_props: Dict[str, Any] = None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.display_name = display_name
        self.default_props = default_props or {}


class TemplateManager:
    """管理所有可用的控件模板"""

    def __init__(self):
        self.templates: Dict[str, Template] = {}
        self._init_default_templates()

    def _init_default_templates(self):
        default_list = [
            Template("Button", "按钮", {"text": "按钮", "enabled": True}),
            Template("Label", "标签", {"text": "标签", "font_size": 14}),
            Template("ImageView", "图片视图", {"src": ""}),
            Template("EditText", "输入框", {"placeholder": "请输入"}),
        ]
        for t in default_list:
            self.templates[t.id] = t

    def add_template(self, template: Template):
        self.templates[template.id] = template

    def get_template(self, tid: str) -> Optional[Template]:
        return self.templates.get(tid)

    def get_all(self) -> List[Template]:
        return list(self.templates.values())


# 全局单例
template_manager = TemplateManager()