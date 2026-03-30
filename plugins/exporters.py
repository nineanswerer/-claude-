from . import SpiderPlugin
from typing import Dict, Any, List
import json
import csv
import os
from datetime import datetime

class ExporterPlugin(SpiderPlugin):
    """
    数据导出插件：将爬取的数据导出为不同格式的文件。
    支持JSON、CSV、Excel（需要openpyxl或xlsxwriter）。
    """

    SUPPORTED_FORMATS = ['json', 'csv', 'txt']

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.output_dir = config.get('output_dir', 'data')
        self.file_prefix = config.get('file_prefix', 'crawl_result')
        self.format = config.get('format', 'json')
        self.encoding = config.get('encoding', 'utf-8')

        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

    def validate_config(self) -> List[str]:
        errors = []
        if self.format not in self.SUPPORTED_FORMATS:
            errors.append(f"不支持的导出格式: {self.format}，支持: {self.SUPPORTED_FORMATS}")
        return errors

    def run(self, engine, data: List[Dict[str, Any]] or Dict[str, Any], filename: str = None) -> str:
        """
        导出数据到文件。

        :param engine: SpiderEngine实例（此处未使用，保留接口一致性）
        :param data: 要导出的数据（列表或字典）
        :param filename: 自定义文件名（不含扩展名），如果为None则自动生成
        :return: 保存的文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.file_prefix}_{timestamp}"

        filepath = os.path.join(self.output_dir, f"{filename}.{self.format}")

        try:
            if self.format == 'json':
                self._export_json(data, filepath)
            elif self.format == 'csv':
                self._export_csv(data, filepath)
            elif self.format == 'txt':
                self._export_txt(data, filepath)
            else:
                raise ValueError(f"不支持的导出格式: {self.format}")
            return filepath
        except Exception as e:
            return f"导出失败: {e}"

    def _export_json(self, data, filepath):
        """导出为JSON文件。"""
        with open(filepath, 'w', encoding=self.encoding) as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _export_csv(self, data, filepath):
        """导出为CSV文件。"""
        if not data:
            raise ValueError("没有数据可导出")

        # data应为列表，每个元素是字典
        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list) or not isinstance(data[0], dict):
            raise ValueError("CSV导出需要列表格式的数据，且每个元素是字典")

        fieldnames = data[0].keys()
        with open(filepath, 'w', newline='', encoding=self.encoding) as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    def _export_txt(self, data, filepath):
        """导出为纯文本文件（每个字段一行）。"""
        with open(filepath, 'w', encoding=self.encoding) as f:
            if isinstance(data, list):
                for i, item in enumerate(data, 1):
                    f.write(f"=== 项目 {i} ===\n")
                    for key, value in item.items():
                        f.write(f"{key}: {value}\n")
                    f.write("\n")
            else:
                for key, value in data.items():
                    f.write(f"{key}: {value}\n")


class LoggingPlugin(SpiderPlugin):
    """
    日志插件：记录爬取操作的日志到文件。
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.log_file = config.get('log_file', 'logs/crawl.log')
        self.log_dir = os.path.dirname(self.log_file)
        if self.log_dir:
            os.makedirs(self.log_dir, exist_ok=True)

    def validate_config(self) -> List[str]:
        return []

    def run(self, engine, log_data: Dict[str, Any]):
        """
        记录日志条目到文件。

        :param engine: SpiderEngine实例（此处未使用）
        :param log_data: 日志数据字典，至少包含'message'键
        """
        timestamp = datetime.now().isoformat()
        message = log_data.get('message', '无消息')
        level = log_data.get('level', 'INFO')
        extra = log_data.get('extra', {})

        log_entry = f"[{timestamp}] [{level}] {message}"
        if extra:
            extra_str = ' | '.join(f"{k}={v}" for k, v in extra.items())
            log_entry += f" | {extra_str}"
        log_entry += "\n"

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
