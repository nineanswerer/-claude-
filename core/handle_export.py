#!/usr/bin/env python
"""
处理数据导出任务，供Electron桌面应用调用。
"""

import sys
import json
import os
from plugins import PluginManager
from core.engine import SpiderEngine

def main():
    if len(sys.argv) < 2:
        print("错误：缺少配置参数")
        sys.exit(1)

    config_json = sys.argv[1]
    config = json.loads(config_json)

    data = config.get('data')
    filepath = config.get('filePath')  # 注意IPC传参的字段名
    export_format = config.get('format', 'json')

    if not data or not filepath:
        print("错误：缺少data或filepath参数")
        sys.exit(1)

    # 确保目录存在
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # 使用ExporterPlugin
    plugin_manager = PluginManager()

    exporter_config = {
        'output_dir': os.path.dirname(filepath),
        'format': export_format,
        'file_prefix': os.path.splitext(os.path.basename(filepath))[0]
    }

    engine = SpiderEngine({})

    try:
        result = plugin_manager.run_plugin(
            'ExporterPlugin',
            engine,
            exporter_config,
            data=data,
            filename=os.path.splitext(os.path.basename(filepath))[0]
        )
        print(f"导出成功: {result}")
        sys.exit(0)
    except Exception as e:
        print(f"导出失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
