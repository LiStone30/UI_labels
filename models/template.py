# -*- coding: utf-8 -*-
"""控件模板定义与模板管理器"""

import json
import os
from typing import Dict, List, Optional, Any

from logger import logger


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
        self._load_templates()

    def _load_templates(self):
        json_path = os.path.join(os.path.dirname(__file__), "templates.json")
        with open(json_path, "r", encoding="utf-8") as f:
            templates_data = json.load(f)
        for t_data in templates_data:
            template = Template(
                name=t_data["id"],
                display_name=t_data["display_name"],
                default_props=t_data.get("default_props", {})
            )
            self.templates[template.id] = template
            self._name_to_template[template.name] = template
        logger.info(f"Loaded {len(self.templates)} templates from {json_path}")

    def add_template(self, template: Template):
        self.templates[template.id] = template
        self._name_to_template[template.name] = template

    def get_template(self, tid: str) -> Optional[Template]:
        return self.templates.get(tid)

    def get_template_by_name(self, name: str) -> Optional[Template]:
        return self._name_to_template.get(name)

    def get_all(self) -> List[Template]:
        return list(self.templates.values())


template_manager = TemplateManager()