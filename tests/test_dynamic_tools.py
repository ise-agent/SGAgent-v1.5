import asyncio
from agents.test import TesterAgent
from agents.context import Context
from pydantic_ai import FunctionToolset


async def test_runtime_addition_proof():
    tester = TesterAgent()
    dynamic_toolset = FunctionToolset()

    # 步骤1：证明初始状态只有添加工具
    @dynamic_toolset.tool
    def add_magic_calculator() -> str:
        """运行时添加魔法计算器"""

        def magic_calculator(a: int, b: int) -> int:
            return a + 2 * b

        # 关键证据：在工具执行时才添加
        print("🔧 正在运行时添加 magic_calculator...")
        dynamic_toolset.add_function(magic_calculator, name="magic_calculator")
        print("✅ magic_calculator 已添加到工具集")
        return "魔法计算器已添加"

    # 步骤2：验证初始状态
    print("=== 运行前检查 ===")
    print("可用工具:", list(dynamic_toolset.tools.keys()))
    # 证明：只有 ['add_magic_calculator']

    ctx = Context(issue="证明动态工具添加")

    # 步骤3：运行并监控
    print("\n=== 开始运行 ===")
    result = await tester.run(
        "先添加魔法计算器，然后用它计算 5 和 3", context=ctx, toolsets=[dynamic_toolset]
    )

    print(f"\n=== 最终结果 ===")
    print(f"结果: {result}")
    print(f"期望: 11 (5 + 2*3)")

    # 步骤4：验证最终状态
    print("\n=== 运行后检查 ===")
    print("最终工具:", list(dynamic_toolset.tools.keys()))
    # 证明：现在有 ['add_magic_calculator', 'magic_calculator']


if __name__ == "__main__":
    asyncio.run(test_runtime_addition_proof())
