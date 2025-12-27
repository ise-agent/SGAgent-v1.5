# TODO : 类的继承 ， 引用的函数同名问题 ，测试类判断问题 ， 编码问题

# main.py

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

# 导入模块
from kg import construct_tags
from retriever.ckg_retriever import CKGRetriever

try:
    from settings import settings
    TEST_BED = settings.TEST_BED
    PROJECT_NAME = settings.PROJECT_NAME
except ImportError:
    # 如果 settings 不可用，使用默认值
    TEST_BED = "/root/hy/projects"
    PROJECT_NAME = "sympy"


def build_knowledge_graph(dir_name):
    """
    构建知识图谱（内存版）

    Args:
        dir_name: 项目目录路径

    Returns:
        CKGRetriever: 初始化好的检索器实例
    """
    print("✅ Step 1: Constructing Knowledge Graph and Tags in memory...\n")

    # 构建 structure 和 tags（都在内存中）
    structure, tags = construct_tags.run(dir_name)

    print("✅ Step 2: Initializing Memory-based Retriever...\n")

    # 初始化内存版检索器
    retriever = CKGRetriever(structure, tags)

    print("🎉 Knowledge Graph built successfully in memory!\n")
    return retriever


if __name__ == "__main__":
    dir_name = Path(TEST_BED) / PROJECT_NAME

    # 构建知识图谱并获取检索器
    retriever = build_knowledge_graph(dir_name)

    # 示例：使用检索器进行查询
    print("📊 Retriever Statistics:")
    print(f"  - Total Classes: {len(retriever.classes)}")
    print(f"  - Total Methods: {len(retriever.methods)}")
    print(f"  - Total Variables: {len(retriever.variables)}")
    print(f"  - Total Tags: {len(retriever.tags)}")

    print("\n✨ Retriever is ready for use!")
