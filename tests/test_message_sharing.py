#!/usr/bin/env python3
"""
测试协调器和本地化代理之间的消息共享 - 改进版
"""

import asyncio
from agents.coordinator import CoordinatorAgent
from agents.localizer import LocalizerAgent
from agents.context import Context, Issue
from agents.messages import global_message_history


async def test_coordinator_localizer_sharing():
    print("Testing coordinator and localizer message sharing...")

    # 清空全局消息历史
    global_message_history.clear()

    # 创建协调器和本地化代理实例
    coordinator = CoordinatorAgent()
    localizer = LocalizerAgent()

    # 测试1: 协调器处理代码问题
    print("\n=== Test 1: Coordinator processes code issue ===")
    try:
        context1 = Context()
        result1 = await coordinator.run("I have a bug in my code at lines 10-15 in file a.py", context1)
        print(f"Coordinator result: {result1}")

        # 查看当前消息历史
        history1 = global_message_history.get_history()
        print(f"Message history after coordinator: {len(history1)} messages")
        for i, msg in enumerate(history1):
            print(f"  Message {i}: {msg}")
    except Exception as e:
        print(f"Coordinator failed: {e}")

    # 测试2: 本地化代理使用共享历史，但给出更明确的指令
    print("\n=== Test 2: Localizer agent analyzes shared history ===")
    try:
        # 创建一个包含具体问题的上下文
        

        # 给出更明确的指令，让本地化代理分析历史中的代码问题
        result2 = await localizer.run(
            "Based on the previous conversation, what's location"
        )
        print(f"Localizer result: {result2}")

        # 查看更新后的消息历史
        print("===========================")
        history2 = global_message_history.get_raw_history()
        print(f"Message history after localizer: {len(history2)} messages")
        for i, msg in enumerate(history2):
            print(f"  Message {i}: {msg}")
    except Exception as e:
        print(f"Localizer failed: {e}")

    print("======")


if __name__ == "__main__":
    asyncio.run(test_coordinator_localizer_sharing())