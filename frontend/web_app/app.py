from flask import Flask, request, jsonify, render_template, send_from_directory
import yaml
import os
import sys

# 添加项目根目录到Python路径，以便导入core和plugins模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core.engine import SpiderEngine
from plugins import PluginManager, load_plugins_from_config

app = Flask(__name__, static_folder='static', template_folder='templates')

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml')

# 初始化插件管理器
plugin_manager = PluginManager()

# 加载配置
def load_config():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

config = load_config()

@app.route('/')
def index():
    """首页 - 显示简单的任务提交表单。"""
    available_plugins = plugin_manager.get_available_plugins()
    return render_template('index.html', plugins=available_plugins)

@app.route('/api/plugins', methods=['GET'])
def list_plugins():
    """API: 列出所有可用插件及其描述。"""
    plugins_info = {
        name: {
            'description': info['description'],
            'class': info['class'].__name__
        }
        for name, info in plugin_manager.plugins.items()
    }
    return jsonify({'plugins': plugins_info})

@app.route('/api/search', methods=['POST'])
def search():
    """
    API: 执行搜索任务（使用KeywordSearchPlugin）。
    请求JSON示例:
    {
        "keyword": "Python爬虫",
        "plugin": "KeywordSearchPlugin",
        "plugin_config": {}
    }
    """
    data = request.json
    keyword = data.get('keyword')
    plugin_name = data.get('plugin', 'KeywordSearchPlugin')
    plugin_config = data.get('plugin_config', {})

    if not keyword:
        return jsonify({'error': '缺少keyword参数'}), 400

    # 创建引擎（使用全局配置中的设置）
    engine_config = config.get('global', {})
    engine = SpiderEngine(engine_config)

    try:
        # 加载指定插件，合并全局配置中的插件配置和请求中的配置
        global_plugin_config = {}
        for p in config.get('plugins', []):
            if p['name'] == plugin_name:
                global_plugin_config = p.get('config', {})
                break
        merged_config = {**global_plugin_config, **plugin_config}

        result = plugin_manager.run_plugin(
            plugin_name,
            engine,
            merged_config,
            keyword
        )
        # 调试日志：输出结果结构和类型
        print(f"[DEBUG] Search API result: {result}")
        print(f"[DEBUG] Result type: {type(result)}")
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/crawl', methods=['POST'])
def crawl():
    """
    API: 通用爬取接口（使用GenericCrawlerPlugin）。
    请求JSON示例:
    {
        "url": "https://example.com/news",
        "selectors": {"title": "h1", "content": "div.content"},
        "plugin": "GenericCrawlerPlugin"
    }
    """
    data = request.json
    url = data.get('url')
    selectors = data.get('selectors')
    plugin_name = data.get('plugin', 'GenericCrawlerPlugin')

    if not url or not selectors:
        return jsonify({'error': '缺少url或selectors参数'}), 400

    engine_config = config.get('global', {})
    engine = SpiderEngine(engine_config)

    try:
        global_plugin_config = {}
        for p in config.get('plugins', []):
            if p['name'] == plugin_name:
                global_plugin_config = p.get('config', {})
                break
        merged_config = {**global_plugin_config, **data.get('plugin_config', {})}

        # 使用GenericCrawlerPlugin
        result = plugin_manager.run_plugin(
            plugin_name,
            engine,
            merged_config,
            url=url,
            selectors=selectors
        )
        # 调试日志
        print(f"[DEBUG] Crawl API result: {result}")
        print(f"[DEBUG] Result type: {type(result)}")
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export', methods=['POST'])
def export():
    """
    API: 导出数据接口（使用ExporterPlugin）。
    请求JSON示例:
    {
        "data": [{"title": "标题1", "content": "内容1"}, ...],
        "filename": "my_result",
        "format": "json"
    }
    """
    data = request.json
    export_data = data.get('data')
    filename = data.get('filename')
    export_format = data.get('format', 'json')

    if export_data is None:
        return jsonify({'error': '缺少data参数'}), 400

    engine = SpiderEngine({})  # 导出不需要引擎功能，但保持接口一致

    try:
        # 获取ExporterPlugin配置
        exporter_config = {}
        for p in config.get('plugins', []):
            if p['name'] == 'ExporterPlugin':
                exporter_config = p.get('config', {})
                break

        merged_config = {**exporter_config, 'format': export_format}
        filepath = plugin_manager.run_plugin(
            'ExporterPlugin',
            engine,
            merged_config,
            data=export_data,
            filename=filename
        )
        return jsonify({'success': True, 'filepath': filepath})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config', methods=['GET', 'POST'])
def config_api():
    """API: 获取或更新配置文件。"""
    if request.method == 'GET':
        return jsonify(config)
    elif request.method == 'POST':
        new_config = request.json
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(new_config, f, allow_unicode=True, sort_keys=False)
        return jsonify({'success': True, 'message': '配置已更新'})

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
