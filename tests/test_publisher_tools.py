import asyncio
from pathlib import Path
from agents.context import Patch
from tools.publisher_tools import apply_patches


async def test_publisher_tools():
    test_file = Path("test_file.py")
    patches = [
        Patch(
            operation="insert",
            path=str(test_file),
            start_line=6,
            end_line=6,
            content="    # Inserted line\n    print('Inserted content')"
        ),
        Patch(
            operation="replace",
            path=str(test_file),
            start_line=2,
            end_line=4,
            content="    print('Updated line')\n    new_line_1()\n    new_line_2()\n"
        )
    ]

    # 应用补丁
    result = apply_patches(patches)
    print("应用补丁结果:")
    print(result)

    # 读取并显示修改后的文件
    with open(test_file, "r") as f:
        content = f.read()
        print("\n修改后的文件内容:")
        print(content)

    # 清理测试文件
    if test_file.exists():
        test_file.unlink()


if __name__ == "__main__":
    asyncio.run(test_publisher_tools())