"""
插件系统：允许动态加载和配置不同的爬虫插件。
通过配置YAML/JSON文件选择和管理插件。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import importlib
import inspect
import os
import yaml

class SpiderPlugin(ABC):
    """
    爬虫插件基类，所有具体插件都必须继承此类并实现run方法。
    """
    def __init__(self, config: Dict[str, Any]):
        """
        初始化插件。

        :param config: 插件的配置字典
        """
        self.config = config
        self.name = self.__class__.__name__

    @abstractmethod
    def run(self, engine, *args, **kwargs) -> Any:
        """
        执行插件的主要功能。

        :param engine: SpiderEngine实例，用于执行底层爬取操作
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 插件的执行结果
        """
        pass

    @abstractmethod
    def validate_config(self) -> List[str]:
        """
        验证插件配置是否有效。
        如果配置无效，返回错误消息列表；否则返回空列表。

        :return: 错误消息列表
        """
        pass


class PluginManager:
    """
    插件管理器，负责发现、加载和运行插件。
    """
    def __init__(self, plugins_dir: str = 'plugins'):
        """
        初始化插件管理器。

        :param plugins_dir: 存放插件的目录路径
        """
        self.plugins_dir = plugins_dir
        self.plugins: Dict[str, SpiderPlugin] = {}
        self._discover_plugins()

    def _discover_plugins(self):
        """自动发现并加载plugins目录下的所有插件。"""
        plugins_path = os.path.join(os.getcwd(), self.plugins_dir)
        if not os.path.exists(plugins_path):
            print(f"插件目录不存在: {plugins_path}")
            return

        # 遍历plugins目录下的所有.py文件（排除__init__.py）
        for filename in os.listdir(plugins_path):
            if filename.endswith('.py') and filename != '__init__.py':
                module_name = filename[:-3]  # 去掉.py后缀
                try:
                    module = importlib.import_module(f'plugins.{module_name}')
                    # 查找模块中继承自SpiderPlugin的类
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, SpiderPlugin) and obj != SpiderPlugin:
                            plugin_instance = obj({})
                            self.plugins[plugin_instance.name] = {
                                'class': obj,
                                'module': module,
                                'description': obj.__doc__ or '无描述'
                            }
                except Exception as e:
                    print(f"加载插件 {filename} 时出错: {e}")

    def get_available_plugins(self) -> List[str]:
        """
        获取所有可用插件的名称列表。

        :return: 插件名称列表
        """
        return list(self.plugins.keys())

    def load_plugin(self, plugin_name: str, config: Dict[str, Any]) -> SpiderPlugin:
        """
        根据名称加载指定插件。

        :param plugin_name: 插件名称
        :param config: 插件配置
        :return: 插件实例
        :raises ValueError: 如果插件不存在
        """
        if plugin_name not in self.plugins:
            raise ValueError(f"插件 '{plugin_name}' 不存在")

        plugin_class = self.plugins[plugin_name]['class']
        return plugin_class(config)

    def run_plugin(self, plugin_name: str, engine, config: Dict[str, Any], *args, **kwargs) -> Any:
        """
        加载并运行指定插件。

        :param plugin_name: 插件名称
        :param engine: SpiderEngine实例
        :param config: 插件配置
        :param args: 传递给插件的位置参数
        :param kwargs: 传递给插件关键字参数
        :return: 插件执行结果
        """
        plugin = self.load_plugin(plugin_name, config)
        errors = plugin.validate_config()
        if errors:
            raise ValueError(f"插件配置错误: {', '.join(errors)}")
        return plugin.run(engine, *args, **kwargs)


def load_plugins_from_config(config_file: str, plugin_manager: PluginManager) -> List[SpiderPlugin]:
    """
    根据配置文件加载插件列表。

    :param config_file: 配置文件路径（YAML格式）
    :param plugin_manager: 插件管理器实例
    :return: 加载的插件实例列表
    """
    with open(config_file, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)

    plugins = []
    for plugin_conf in config_data.get('plugins', []):
        name = plugin_conf['name']
        config = plugin_conf.get('config', {})
        plugin = plugin_manager.load_plugin(name, config)
        plugins.append(plugin)

    return plugins


# 示例：创建一个简单的插件配置模板
DEFAULT_CONFIG_TEMPLATE = {
    'plugins': [
        {
            'name': 'KeywordSearchPlugin',
            'config': {
                'search_engine': 'google',
                'max_results': 10,
                'output_format': 'json'
            }
        }
    ]
}
