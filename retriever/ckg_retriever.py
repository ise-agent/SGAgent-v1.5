"""Code Knowledge Graph Retriever for in-memory database"""
import json
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from bisect import bisect_right

from models.entities import Clazz, Method, Variable
from utils.decorators import singleton
from retriever.converters import _convert_to_clazz, _convert_to_method, _convert_to_variable


@singleton
class CKGRetriever:
    """
    内存版 Code Knowledge Graph Retriever
    不再依赖 Neo4j，所有数据和索引存储在内存中
    """

    def __init__(self, structure: dict, tags: list):
        """
        初始化内存检索器

        Args:
            structure: kg 数据结构（原 kg.json）
            tags: tags 列表（原 tags.json 的内容）
        """
        self.structure = structure
        self.tags = tags
        self.focal_method_id = -1

        # 内存索引结构
        self.classes: Dict[str, dict] = {}  # full_qualified_name -> class_dict
        self.methods: Dict[str, dict] = {}  # full_qualified_name -> method_dict
        self.variables: Dict[str, dict] = {}  # full_qualified_name -> variable_dict

        # 辅助索引
        self.methods_by_name: Dict[str, List[dict]] = defaultdict(list)  # name -> [method_dict]
        self.classes_by_name: Dict[str, List[dict]] = defaultdict(list)  # name -> [class_dict]
        self.variables_by_name: Dict[str, List[dict]] = defaultdict(list)  # name -> [variable_dict]

        # 文件索引
        self.methods_by_file: Dict[str, List[dict]] = defaultdict(list)
        self.classes_by_file: Dict[str, List[dict]] = defaultdict(list)
        self.variables_by_file: Dict[str, List[dict]] = defaultdict(list)

        # 用于动态计算关系的索引
        self.file_intervals: Dict[str, List[Tuple[int, int, str, str, str]]] = defaultdict(list)
        # (absolute_path) -> [(start_line, end_line, fqn, label, name)]

        # 预计算的 CALLS 和 REFERENCES 索引
        self.calls_index: Dict[str, List[dict]] = defaultdict(list)  # caller_fqn -> [callee_info]
        self.references_index: Dict[str, List[dict]] = defaultdict(list)  # referrer_fqn -> [referenced_class_info]

        # 构建索引
        self._build_indexes()

    def _build_indexes(self):
        """从 structure 构建所有内存索引"""
        self._process_structure(self.structure)

        # 对每个文件的 intervals 排序
        for path in self.file_intervals:
            self.file_intervals[path].sort(key=lambda t: t[0])

        # 预计算 CALLS 和 REFERENCES 索引
        self._build_calls_references_index()

    def _build_calls_references_index(self):
        """
        一次性遍历所有 tags，构建 CALLS 和 REFERENCES 反向索引
        这样后续查询时无需重复遍历 tags
        """
        print(f"Building calls/references index from {len(self.tags)} tags...")

        for tag in self.tags:
            if tag.kind != "ref":
                continue

            # 获取引用位置的文件名和行号
            fname = tag.fname or tag.rel_fname
            line_val = tag.line
            if isinstance(line_val, list) and line_val:
                line_no = int(line_val[0])
            elif isinstance(line_val, int):
                line_no = line_val
            else:
                continue

            name = tag.name
            category = (tag.category or "").lower()

            # 找到引用的源容器（调用者）
            src = self._find_container(fname, line_no)
            if not src:
                continue
            src_fqn, src_label = src

            # 根据 category 查找目标并建立索引
            if category == "function":
                # CALLS 关系：函数调用
                candidates = self.methods_by_name.get(name, [])
                if len(candidates) == 1:
                    callee_info = self._entity_to_dict(candidates[0])
                    self.calls_index[src_fqn].append(callee_info)
            elif category == "class":
                # REFERENCES 关系：类引用
                candidates = self.classes_by_name.get(name, [])
                if len(candidates) == 1:
                    class_info = self._entity_to_dict(candidates[0])
                    self.references_index[src_fqn].append(class_info)

        print(f"Index built: {len(self.calls_index)} entities with calls, "
              f"{len(self.references_index)} entities with references")


    def _process_structure(self, structure, current_path=None):
        """递归处理 structure，提取所有实体"""
        if current_path is None:
            current_path = []

        for key, value in structure.items():
            if key.endswith(".py") and isinstance(value, dict):
                # 处理 Python 文件
                for class_data in value.get("classes", []):
                    self._index_class(class_data)
                for func in value.get("functions", []):
                    self._index_method(func)
                for var in value.get("variables", []):
                    self._index_variable(var)
            elif isinstance(value, dict):
                self._process_structure(value, current_path + [key])

    def _index_class(self, class_data: dict):
        """索引一个类"""
        fqn = class_data["full_qualified_name"]
        self.classes[fqn] = class_data
        self.classes_by_name[class_data["name"]].append(class_data)
        self.classes_by_file[class_data["absolute_path"]].append(class_data)

        # 添加到 file_intervals
        self.file_intervals[class_data["absolute_path"]].append((
            class_data["start_line"],
            class_data["end_line"],
            fqn,
            "Class",
            class_data["name"]
        ))

        # 处理类的方法和常量
        for method in class_data.get("methods", []):
            self._index_method(method)
        for const in class_data.get("constants", []):
            self._index_variable(const)

    def _index_method(self, method_data: dict):
        """索引一个方法"""
        fqn = method_data["full_qualified_name"]
        self.methods[fqn] = method_data
        self.methods_by_name[method_data["name"]].append(method_data)
        self.methods_by_file[method_data["absolute_path"]].append(method_data)

        # 添加到 file_intervals
        self.file_intervals[method_data["absolute_path"]].append((
            method_data["start_line"],
            method_data["end_line"],
            fqn,
            "Method",
            method_data["name"]
        ))

    def _index_variable(self, var_data: dict):
        """索引一个变量"""
        fqn = var_data["full_qualified_name"]
        self.variables[fqn] = var_data
        self.variables_by_name[var_data["name"]].append(var_data)
        self.variables_by_file[var_data["absolute_path"]].append(var_data)

    def close(self):
        """兼容接口，内存版无需关闭"""
        pass

    def change_focal_method_id(self, focal_method_id):
        """兼容接口"""
        self.focal_method_id = focal_method_id

    def run_query(self, query: str, parameters: dict) -> List[Any]:
        """
        兼容接口，但不再使用 Cypher 查询
        此方法不应被直接调用
        """
        raise NotImplementedError("Memory-based retriever does not support Cypher queries")

    def search_method_accurately(self, absolute_path: str, full_qualified_name: str = None) -> List[Method]:
        """
        精确查找方法或测试

        Args:
            absolute_path: 文件的绝对路径
            full_qualified_name: 方法的全限定名（可选）

        Returns:
            匹配的方法列表
        """
        candidates = self.methods_by_file.get(absolute_path, [])

        if full_qualified_name is None:
            # 返回该文件中的所有方法
            results = [m for m in candidates]
        else:
            # 过滤包含指定全限定名的方法
            results = [m for m in candidates if full_qualified_name in m["full_qualified_name"]]

        if not results:

            return []

        return [_convert_to_method(m) for m in results]

    def search_method_fuzzy(self, name: str) -> List[Method]:
        """
        模糊查找方法和测试节点

        Args:
            name: 方法名（支持部分匹配）

        Returns:
            匹配的方法列表
        """
        results = []
        for method_name, method_list in self.methods_by_name.items():
            if name in method_name:
                results.extend(method_list)

        if not results:
            print(f"No methods found containing '{name}' in name.")
            return []

        return [_convert_to_method(m) for m in results]

    def get_relevant_entities(self, file: str, full_qualified_name: str) -> dict:
        """
        查找与目标实体相关的所有关系节点（动态计算）

        Args:
            file: 目标实体的绝对路径
            full_qualified_name: 目标实体的全限定名

        Returns:
            包含六类关系的字典
        """
        result = {rt: [] for rt in (
            "BELONGS_TO", "CALLS", "HAS_METHOD",
            "HAS_VARIABLE", "INHERITS", "REFERENCES"
        )}

        # 查找目标实体
        target = None
        target_type = None

        if full_qualified_name in self.methods:
            target = self.methods[full_qualified_name]
            target_type = "Method"
        elif full_qualified_name in self.classes:
            target = self.classes[full_qualified_name]
            target_type = "Class"
        elif full_qualified_name in self.variables:
            target = self.variables[full_qualified_name]
            target_type = "Variable"

        if target is None:
            return result

        # BELONGS_TO: 方法/变量所属的类
        if target_type in ("Method", "Variable"):
            class_name = target.get("class_name")
            if class_name and class_name in self.classes:
                result["BELONGS_TO"].append(self._entity_to_dict(self.classes[class_name]))

        # HAS_METHOD: 类拥有的方法（双向）
        if target_type == "Class":
            for method in target.get("methods", []):
                result["HAS_METHOD"].append(self._entity_to_dict(method))
        elif target_type == "Method":
            class_name = target.get("class_name")
            if class_name and class_name in self.classes:
                for method in self.classes[class_name].get("methods", []):
                    if method["full_qualified_name"] != full_qualified_name:
                        result["HAS_METHOD"].append(self._entity_to_dict(method))

        # HAS_VARIABLE: 类拥有的变量（双向）
        if target_type == "Class":
            for const in target.get("constants", []):
                result["HAS_VARIABLE"].append(self._entity_to_dict(const))
        elif target_type == "Variable":
            class_name = target.get("class_name")
            if class_name and class_name in self.classes:
                for const in self.classes[class_name].get("constants", []):
                    if const["full_qualified_name"] != full_qualified_name:
                        result["HAS_VARIABLE"].append(self._entity_to_dict(const))

        # INHERITS: 类的继承关系
        if target_type == "Class":
            parent_class = target.get("parent_class")
            if parent_class and parent_class in self.classes:
                result["INHERITS"].append(self._entity_to_dict(self.classes[parent_class]))

        # CALLS & REFERENCES: 从 tags 动态计算
        calls, references = self._compute_calls_and_references(file, full_qualified_name)
        result["CALLS"] = calls
        result["REFERENCES"] = references

        return result

    def _entity_to_dict(self, entity: dict) -> dict:
        """将实体转换为字典格式（处理 JSON 字段）"""
        props = dict(entity)
        for field in ("params", "modifiers"):
            if field in props and isinstance(props[field], list):
                # 已经是列表，无需处理
                pass
            elif field in props and isinstance(props[field], str):
                try:
                    props[field] = json.loads(props[field])
                except json.JSONDecodeError:
                    pass
        return props

    def _find_container(self, path: str, line: int) -> Optional[Tuple[str, str]]:
        """
        查找包含指定行的容器（类或方法）

        Returns:
            (fqn, label) or None
        """
        intervals = self.file_intervals.get(path)
        if not intervals:
            return None

        starts = [s for (s, _, _, _, _) in intervals]
        idx = bisect_right(starts, line) - 1
        candidates = []
        for j in range(max(0, idx - 5), min(len(intervals), idx + 6)):
            s, e, fqn, label, name = intervals[j]
            if s <= line <= e:
                candidates.append((s, e, fqn, label, name))
        if not candidates:
            return None
        methods = [c for c in candidates if c[3] == "Method"]
        chosen = methods or candidates
        chosen.sort(key=lambda c: (c[3] != "Method", c[1] - c[0]))
        _, _, fqn, label, _ = chosen[0]
        return fqn, label

    def _compute_calls_and_references(self, file: str, full_qualified_name: str) -> Tuple[List[dict], List[dict]]:
        """
        从预计算的索引中获取 CALLS 和 REFERENCES 关系

        Returns:
            (calls, references) - 两个列表
        """
        # 直接从索引中获取，O(1) 复杂度
        calls = self.calls_index.get(full_qualified_name, [])
        references = self.references_index.get(full_qualified_name, [])

        return calls, references

    def read_all_classes_and_methods(self, file: str) -> Tuple[List[Clazz], List[Method]]:
        """
        读取指定文件中的所有类和方法

        Args:
            file: 文件的绝对路径

        Returns:
            (classes, methods) 元组
        """
        classes = self.classes_by_file.get(file, [])
        methods = self.methods_by_file.get(file, [])

        return (
            [_convert_to_clazz(c) for c in classes],
            [_convert_to_method(m) for m in methods]
        )

    def search_constructor_in_clazz(self, name: str) -> List[Method]:
        """
        根据类名查找对应的构造函数

        Args:
            name: 目标类名（精确匹配）

        Returns:
            匹配到的构造函数对象列表
        """
        results = []
        class_list = self.classes_by_name.get(name, [])

        for cls in class_list:
            for method in cls.get("methods", []):
                if method.get("type") == "constructor":
                    results.append(method)

        return [_convert_to_method(m) for m in results]

    def search_variable_query(self, file: str, variable_name: str) -> List[Variable]:
        """
        查询指定文件中的变量节点

        Args:
            file: 文件路径
            variable_name: 变量名

        Returns:
            包含 Variable 节点的列表
        """
        candidates = self.variables_by_file.get(file, [])

        if '.' not in variable_name:
            # 精确匹配 name
            results = [v for v in candidates if v["name"] == variable_name]
        else:
            # 模糊匹配 full_qualified_name
            results = [v for v in candidates if variable_name in v["full_qualified_name"]]

        return [_convert_to_variable(v) for v in results]

    def search_field_variables_of_class(self, name: str) -> List[Variable]:
        """
        查找类的字段变量

        Args:
            name: 类名

        Returns:
            变量列表
        """
        results = []
        class_list = self.classes_by_name.get(name, [])

        for cls in class_list:
            for const in cls.get("constants", []):
                results.append(const)

        return [_convert_to_variable(v) for v in results]

    def search_file_by_keyword(self, keyword: str) -> List[str]:
        """
        根据关键字搜索文件

        Args:
            keyword: 搜索关键字

        Returns:
            匹配的文件路径列表
        """
        matched_paths = set()

        # 搜索所有类
        for cls in self.classes.values():
            content = cls.get("content")
            if content:
                if isinstance(content, list):
                    content = "\n".join(content)
                if keyword.lower() in content.lower():
                    matched_paths.add(cls["absolute_path"])

        # 搜索独立方法
        for method in self.methods.values():
            if not method.get("class_name"):  # 独立方法
                content = method.get("content")
                if content:
                    if isinstance(content, list):
                        content = "\n".join(content)
                    if keyword.lower() in content.lower():
                        matched_paths.add(method["absolute_path"])

        # 搜索独立变量
        for var in self.variables.values():
            if not var.get("class_name"):  # 独立变量
                content = var.get("content")
                if content:
                    if isinstance(content, list):
                        content = "\n".join(content)
                    if keyword.lower() in content.lower():
                        matched_paths.add(var["absolute_path"])

        return list(matched_paths)

    def search_variable_by_only_name_query(self, variable_name: str) -> List[Variable]:
        """
        根据变量名查询所有匹配的变量

        Args:
            variable_name: 变量名或全限定名片段

        Returns:
            变量对象列表
        """
        if '.' not in variable_name:
            # 精确匹配 name
            results = self.variables_by_name.get(variable_name, [])
        else:
            # 模糊匹配 full_qualified_name
            results = []
            for var in self.variables.values():
                if variable_name in var["full_qualified_name"]:
                    results.append(var)

        # 排序
        results.sort(key=lambda v: (v["absolute_path"], v["start_line"]))
        return [_convert_to_variable(v) for v in results]

    def search_test_cases_by_method_query(self, full_qualified_name: str) -> List[Method]:
        """
        查询方法的测试用例（通过 TESTED 边连接）

        注意：由于没有显式的 TESTED 关系，这里通过命名约定推断
        （例如 test_xxx 对应 xxx 方法）

        Args:
            full_qualified_name: 被测试方法的全限定名

        Returns:
            测试用例列表
        """
        # 提取方法名
        method_name = full_qualified_name.split(".")[-1]
        test_name_patterns = [f"test_{method_name}", f"test{method_name.capitalize()}"]

        results = []
        for pattern in test_name_patterns:
            for method in self.methods.values():
                if pattern in method["name"]:
                    results.append(method)

        # 排序
        results.sort(key=lambda m: (m["absolute_path"], m["start_line"]))
        return [_convert_to_method(m) for m in results]
