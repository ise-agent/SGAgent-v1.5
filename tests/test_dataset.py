#!/usr/bin/settings python3
"""
测试脚本用于验证从数据集加载PROBLEM_STATEMENT的功能
"""


from settings import settings

def test_problem_statement_loading():
    """测试问题陈述加载功能"""
    print("=== 测试问题陈述加载功能 ===")
    print(f"DATASET: {settings.DATASET}")
    print(f"INSTANCE_ID: {settings.INSTANCE_ID}")
    print(f"环境变量中的PROBLEM_STATEMENT: '{settings.PROBLEM_STATEMENT}'")
    print(f"PROBLEM_STATEMENT长度: {len(settings.PROBLEM_STATEMENT)}")

    # 手动调用加载方法（如果需要）
    if not settings.PROBLEM_STATEMENT:
        print("PROBLEM_STATEMENT为空，尝试从数据集加载...")
        settings.load_problem_statement()
        print(f"加载后PROBLEM_STATEMENT: '{settings.PROBLEM_STATEMENT}'")
        print(f"加载后PROBLEM_STATEMENT长度: {len(settings.PROBLEM_STATEMENT)}")

    

if __name__ == "__main__":
    test_problem_statement_loading()