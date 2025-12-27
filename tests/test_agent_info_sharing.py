#!/usr/bin/env python3
"""
测试代理之间的真正信息共享
"""

import asyncio
from agents.coordinator import CoordinatorAgent
from agents.localizer import LocalizerAgent
from agents.context import Context
from agents.messages import global_message_history


async def test_agent_info_sharing():
    print("Testing true information sharing between agents...")

    # 清空全局消息历史
    global_message_history.clear()

    # 创建协调器和本地化代理实例
    coordinator = CoordinatorAgent()
    localizer = LocalizerAgent()

    # 步骤1: 让协调器处理一个具体的代码问题
    print("\n=== Step 1: Coordinator processes a specific code issue ===")
    try:
        result1 = await coordinator.run(
            "I found a bug in my Python code. There's a null pointer exception at lines 25-30 in src/main.py. "
            "The error occurs when processing user input data.",
            Context()
        )
        print(f"Coordinator result: {result1}")

        # 查看消息历史
        history1 = global_message_history.get_history()
        print(f"Message history after coordinator: {len(history1)} messages")
    except Exception as e:
        print(f"Coordinator failed: {e}")
        return

    # 步骤2: 让本地化代理直接询问关于之前处理的bug，不提供任何上下文
    print("\n=== Step 2: Localizer asks about the previously processed bug ===")
    try:
        # 关键测试：本地化代理不应该需要我们提供上下文，它应该能从共享历史中获取信息
        result2 = await localizer.run(
            "What was the bug that was just discussed? Can you tell me the file name and line numbers?",
            Context(),  # 空的上下文
            use_shared_history=True
        )
        print(f"Localizer result: {result2}")

        # 检查本地化代理是否正确识别了之前的信息
        if "src/main.py" in result2 and "25-30" in result2:
            print("✅ SUCCESS: Localizer correctly identified the file and line numbers from shared history!")
        else:
            print("❌ FAILED: Localizer did not correctly identify the information from shared history")

    except Exception as e:
        print(f"Localizer failed: {e}")

    # 步骤3: 进一步测试，让另一个代理询问相同的信息
    print("\n=== Step 3: Another query to test consistency ===")
    try:
        result3 = await localizer.run(
            "Can you summarize what we discussed about the bug location?",
            Context(),
            use_shared_history=True
        )
        print(f"Localizer result 2: {result3}")
    except Exception as e:
        print(f"Localizer failed on second query: {e}")

    # 显示完整的消息历史
    print("\n=== Complete Message History ===")
    final_history = global_message_history.get_history()
    for i, msg in enumerate(final_history):
        print(f"  Message {i}: [{msg.type}] {msg.content}")


if __name__ == "__main__":
    asyncio.run(test_agent_info_sharing())