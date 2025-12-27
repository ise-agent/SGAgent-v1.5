import asyncio  
from agents.test import TesterAgent  
from agents.context import Context  
from typing import Dict, Any  
  
async def test_agent_creates_tool_for_problem():  
    """测试 agent 动态创建工具来解决特定问题"""  
      
    # 创建 agent（启用监控）  
    tester = TesterAgent()  
      
    # 使用 tester 的内置 dynamic_toolset  
      
    ctx = Context(issue="你是一个智能助手，可以根据问题动态创建解决工具")  
      
    # 验证初始状态  
    print("=== 运行前检查 ===")  
    print("可用工具:", list(tester.dynamic_toolset.tools.keys()))  
      
    # 测试场景：让 agent 解决一个需要自定义工具的问题  
    problem_prompt = """  
    我需要解决一个数学问题：计算任意数的平方加上另一个数的结果。  
      
    请按以下步骤操作：  
    1. 先创建一个名为 "square_plus_calculator" 的自定义计算工具  
    2. 这个工具接受两个整数参数 x 和 y  
    3. 功能是计算 x² + y  
    4. 然后用这个工具计算 5 和 3 的结果  
    """  
      
    print("\n=== 开始运行 ===")  
    print(f"问题: {problem_prompt.strip()}")  
      
    result = await tester.run(problem_prompt, context=ctx)  
      
    print(f"\n=== 最终结果 ===")  
    print(f"计算结果: {result}")  
    print(f"期望结果: 28 (5² + 3 = 25 + 3)")  
      
    # 验证最终状态  
    print("\n=== 运行后检查 ===")  
    print("最终工具:", list(tester.dynamic_toolset.tools.keys()))  
      
    # 验证结果  
    expected = 28  
    if str(expected) in str(result):  
        print("✅ 测试通过：Agent 成功创建并使用自定义工具解决了问题")  
    else:  
        print("❌ 测试失败：结果不符合预期")  
      
    return result  
  
      
    return result  
  
if __name__ == "__main__":  
    async def run_all_tests():  
        print("🚀 开始动态工具生成测试")  
          
        print("\n" + "="*50)  
        print("测试 1: 基础问题解决")  
        print("="*50)  
        await test_agent_creates_tool_for_problem()  
          
       
          
        print("\n🎉 所有测试完成")  
      
    asyncio.run(run_all_tests())