# -*- coding: utf-8 -*-
"""数据结构定义 - 使用 Pydantic 定义 JSON Schema"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import json


class UIWidgetNodeSchema(BaseModel):
    """UI控件树节点数据结构"""
    id: str = Field(..., description="节点唯一标识（UUID）")
    name: str = Field(..., description="节点显示名称")
    template_id: str = Field(..., description="模板标识符（如 Button、Container）")
    bbox: List[float] = Field(..., description="边界框坐标 [x, y, width, height]，百分比 0-1")
    props: Dict[str, Any] = Field(default_factory=dict, description="自定义属性")
    children: List["UIWidgetNodeSchema"] = Field(default_factory=list, description="子节点")

    class Config:
        schema_extra = {
            "example": {
                "id": "9868c65c-a738-4373-9b15-d9de5848ac91",
                "name": "按钮（设置-基础）",
                "template_id": "Button",
                "bbox": [0.0276, 0.1011, 0.1434, 0.0568],
                "props": {},
                "children": []
            }
        }


# 更新前向引用
UIWidgetNodeSchema.update_forward_refs()


class UIStructureSchema(BaseModel):
    """UI结构数据整体结构"""
    image_path: Optional[str] = Field(None, description="背景图片路径")
    tree: UIWidgetNodeSchema = Field(..., description="UI控件树根节点")

    class Config:
        schema_extra = {
            "example": {
                "image_path": "D:/projects/UI_labels/screenshot/screenshot.png",
                "tree": {
                    "id": "a16c8492-d666-42f0-aba9-c29262a5dfc6",
                    "name": "Root",
                    "template_id": "",
                    "bbox": [0, 0, 1, 1],
                    "props": {},
                    "children": []
                }
            }
        }


def save_structure_to_json(structure: UIStructureSchema, file_path: str) -> None:
    """将结构数据保存为 JSON 文件"""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(structure.dict(by_alias=True), f, ensure_ascii=False, indent=2)


def load_structure_from_json(file_path: str) -> UIStructureSchema:
    """从 JSON 文件加载结构数据"""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return UIStructureSchema(**data)


def validate_structure(data: dict) -> UIStructureSchema:
    """验证数据结构是否符合 Schema"""
    return UIStructureSchema(**data)


def node_to_schema(node) -> UIWidgetNodeSchema:
    """将 UIWidgetNode 转换为 UIWidgetNodeSchema"""
    return UIWidgetNodeSchema(
        id=node.id,
        name=node.name,
        template_id=node.template_id,
        bbox=list(node.bbox),
        props=node.props,
        children=[node_to_schema(child) for child in node.children]
    )


def schema_to_node(schema: UIWidgetNodeSchema, parent=None):
    """将 UIWidgetNodeSchema 转换为 UIWidgetNode"""
    from models.widget_node import UIWidgetNode
    node = UIWidgetNode(
        name=schema.name,
        template_id=schema.template_id,
        bbox=tuple(schema.bbox)
    )
    node.id = schema.id
    node.props = schema.props
    node.parent = parent
    for child_schema in schema.children:
        child = schema_to_node(child_schema, node)
        node.children.append(child)
    return node


def structure_to_schema(image_path: Optional[str], root_node) -> UIStructureSchema:
    """将整体结构转换为 Schema"""
    return UIStructureSchema(
        image_path=image_path,
        tree=node_to_schema(root_node)
    )


def schema_to_structure(schema: UIStructureSchema):
    """从 Schema 转换回结构数据"""
    return schema.image_path, schema_to_node(schema.tree)


# 生成 JSON Schema 文档
def generate_json_schema() -> dict:
    """生成 JSON Schema 字典"""
    return UIStructureSchema.model_json_schema()
