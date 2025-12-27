"""Converter functions for Neo4j node data to domain objects"""
from typing import Dict, Any
from models.entities import Clazz, Method, Variable


def _convert_to_clazz(node: Dict[str, Any]) -> Clazz:
    """Convert Neo4j node data to Clazz object"""
    return Clazz(
        name=node["name"],
        full_qualified_name=node["full_qualified_name"],
        absolute_path=node.get("absolute_path", ""),
        start_line=node.get("start_line", 0),
        end_line=node.get("end_line", 0),
        content=node.get("content", ""),
        class_type=node.get("class_type", ""),
        parent_classes=node.get("parent_classes", [])
    )


def _convert_to_method(node: Dict[str, Any]) -> Method:
    """Convert Neo4j node data to Method object"""
    return Method(
        name=node["name"],
        full_qualified_name=node["full_qualified_name"],
        absolute_path=node.get("absolute_path", ""),
        start_line=node.get("start_line", 0),
        end_line=node.get("end_line", 0),
        content=node.get("content", ""),
        params=node.get("params", []),
        modifiers=node.get("modifiers", []),
        signature=node.get("signature", ""),
        type=node.get("type", "METHOD").upper() if node.get("type") else None
    )


def _convert_to_variable(node: Dict[str, Any]) -> Variable:
    """Convert Neo4j node data to Variable object"""
    return Variable(
        name=node["name"],
        full_qualified_name=node["full_qualified_name"],
        absolute_path=node.get("absolute_path", ""),
        start_line=node.get("start_line", 0),
        end_line=node.get("end_line", 0),
        content=node.get("content", ""),
        modifiers=node.get("modifiers", []),
        data_type=node.get("data_type", "")
    )