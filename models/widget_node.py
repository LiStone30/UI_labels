# -*- coding: utf-8 -*-
"""UI结构树节点数据模型"""

import uuid
from typing import Dict, List, Optional, Any, Tuple


class UIWidgetNode:
    """UI结构树节点，使用百分比坐标存储 bbox"""

    def __init__(self, name: str, template_id: str, bbox: Tuple[float, float, float, float]):
        self.id = str(uuid.uuid4())
        self.name = name
        self.template_id = template_id
        self.bbox = bbox  # (x, y, w, h) 百分比 0-1
        self.props: Dict[str, Any] = {}
        self.parent: Optional["UIWidgetNode"] = None
        self.children: List["UIWidgetNode"] = []

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "template_id": self.template_id,
            "bbox": list(self.bbox),
            "props": self.props,
            "children": [c.to_dict() for c in self.children],
        }

    @classmethod
    def from_dict(cls, data: Dict, parent=None) -> "UIWidgetNode":
        node = cls(data["name"], data["template_id"], tuple(data["bbox"]))
        node.id = data["id"]
        node.props = data["props"]
        node.parent = parent
        for child_data in data["children"]:
            child = cls.from_dict(child_data, node)
            node.children.append(child)
        return node

    def __repr__(self) -> str:
        return f"UIWidgetNode({self.name!r}, template={self.template_id}, bbox={self.bbox})"