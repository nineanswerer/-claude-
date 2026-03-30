#!/usr/bin/env python
"""
用于Electron桌面应用调用的爬虫任务脚本。
通过命令行参数接收JSON配置，执行爬虫任务并输出结果到stdout。
"""

import sys
import json
import yaml
import os
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from engine import SpiderEngine
from plugins import PluginManager

def main():
    # 读取命令行参数（第一个参数是脚本名，第二个是配置JSON）
    if len(sys.argv) < 2:
        print("错误：缺少配置参数")
        sys.exit(1)

    config_json = sys.argv[1]
    task_config = json.loads(config_json)

    # 加载项目配置文件（如果存在）
    project_config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    if os.path.exists(project_config_path):
        with open(project_config_path, 'r', encoding='utf-8') as f:
            project_config = yaml.safe_load(f)
    else:
        project_config = {}

    # 创建引擎配置
    engine_config = project_config.get('global', {})
    engine = SpiderEngine(engine_config)

    # 初始化插件管理器并执行指定插件
    plugin_manager = PluginManager()

    try:
        plugin_name = task_config.get('plugin')
        plugin_config = task_config.get('plugin_config', {})
        # 合并全局插件配置
        for p in project_config.get('plugins', []):
            if p['name'] == plugin_name:
                plugin_config = {**p.get('config', {}), **plugin_config}
                break

        # 执行插件（传给插件的参数在task_config中除去plugin和plugin_config的键）
        plugin_params = {k: v for k, v in task_config.items() if k not in ['plugin', 'plugin_config']}

        print(f"开始执行插件: {plugin_name}")
        print(f"参数: {plugin_params}")
        print("-" * 50)

        result = plugin_manager.run_plugin(
            plugin_name,
            engine,
            plugin_config,
            **plugin_params
        )

        print("=" * 50)
        print("任务完成！结果是:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"任务执行失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
