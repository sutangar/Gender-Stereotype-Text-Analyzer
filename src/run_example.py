#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
示例运行脚本
"""

import os
import sys
from pathlib import Path

# 获取项目根目录
project_root = Path(__file__).parent.parent.absolute()

# 添加示例命令
example_commands = [
    # 首次使用引导
    f"python {project_root}/src/main.py {project_root}/data/example.txt --setup",
    
    # 分析单个文件
    f"python {project_root}/src/main.py {project_root}/data/example.txt -o {project_root}/output",
    
    # 分析整个目录
    f"python {project_root}/src/main.py {project_root}/data -o {project_root}/output",
    
    # 使用自定义配置
    f"python {project_root}/src/main.py {project_root}/data/example.txt -c {project_root}/src/config.json -o {project_root}/output"
]

if __name__ == "__main__":
    # 打印可用命令
    print("===== 性别刻板印象文本分析工具示例命令 =====")
    for i, cmd in enumerate(example_commands, 1):
        print(f"{i}. {cmd}")
    
    # 询问用户选择
    try:
        choice = int(input("\n请选择要运行的命令 (1-4): "))
        if 1 <= choice <= len(example_commands):
            print(f"\n正在运行: {example_commands[choice-1]}\n")
            os.system(example_commands[choice-1])
        else:
            print(f"无效选择，请输入1-{len(example_commands)}之间的数字")
    except ValueError:
        print("请输入有效的数字")
    except KeyboardInterrupt:
        print("\n操作已取消") 