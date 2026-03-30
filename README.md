## 可配置网络爬虫框架

一个基于Python的灵活爬虫框架，支持插件化架构，提供Web界面和桌面应用两种使用方式。

### 特性

- **可配置插件系统**：通过YAML配置文件动态选择爬虫策略
- **模块化设计**：核心引擎 + 插件架构，易于扩展
- **多种界面**：
  - Flask Web应用（浏览器访问）
  - Electron桌面应用（本地运行）
- **内置插件**：
  - `KeywordSearchPlugin` - 关键词搜索（Google/Bing/DuckDuckGo）
  - `GenericCrawlerPlugin` - 通用网站爬取（自定义选择器）
  - `MultiPageCrawlerPlugin` - 分页爬取
  - `ExporterPlugin` - 数据导出（JSON/CSV/TXT）
  - `LoggingPlugin` - 日志记录
- **反爬虫措施**：随机User-Agent、请求延迟、代理支持
- **安全设计**：本地数据存储，不依赖外部服务

---

### 结构

```
.
├── core/
│   ├── engine.py              # 核心爬虫引擎
│   ├── crawler_task.py        # Electron任务脚本
│   └── handle_export.py       # 导出处理脚本
├── plugins/
│   ├── __init__.py            # 插件基类和管理器
│   ├── keyword_search.py      # 搜索插件
│   ├── generic_crawler.py     # 通用爬取插件
│   └── exporters.py           # 导出和日志插件
├── frontend/
│   ├── web_app/               # Flask Web应用
│   │   ├── app.py
│   │   ├── templates/
│   │   │   └── index.html
│   │   └── static/
│   │       ├── style.css
│   │       └── script.js
│   └── desktop_app/           # Electron桌面应用
│       ├── main.js
│       ├── preload.js
│       ├── index.html
│       ├── renderer.js
│       └── package.json
├── data/                      # 导出数据存储目录
├── logs/                      # 日志文件目录
├── config.yaml                # 配置文件
└── README.md                  # 本文件
```

---

### 快速开始

#### 1. 环境准备

**Python依赖**（需Python 3.7+）：
```bash
pip install requests beautifulsoup4 fake-useragent pyyaml
```

**Node.js依赖**（用于Electron桌面应用）：
```bash
cd frontend/desktop_app
npm install
```

---

#### 2. 运行Web应用

```bash
cd frontend/web_app
python app.py
```

然后在浏览器中访问：http://localhost:5000

---

#### 3. 运行桌面应用

```bash
cd frontend/desktop_app
npm start
```

注意：桌面应用依赖Python环境，确保Python已在系统中安装并可在命令行中使用。

---

### 使用说明

#### Web应用

1. **关键词搜索**：
   - 输入关键词
   - 选择搜索引擎
   - 设置最大结果数
   - 点击“执行搜索”
2. **通用爬取**：
   - 输入目标URL
   - 提供JSON格式的选择器（如 `{"title": "h1", "content": "div.content"}`）
   - 点击“执行爬取”
3. **数据导出**：
   - 输入导出的JSON数组数据
   - 选择格式（JSON/CSV/TXT）
   - 保存到本地

#### 桌面应用

界面与Web应用类似，但所有爬取任务在本地Python进程中执行，不依赖网络服务器，更加隐私安全。

---

### 配置说明

通过根目录下的 `config.yaml` 文件管理全局设置和插件配置：

```yaml
global:
  use_proxy: false
  delay_range: [1.0, 3.0]
  timeout: 15

plugins:
  - name: KeywordSearchPlugin
    config:
      search_engine: google
      max_results: 10
  - name: ExporterPlugin
    config:
      format: json

tasks:
  my_task:
    plugin: GenericCrawlerPlugin
    params:
      url: "https://example.com"
      selectors: {...}
```

---

### 扩展插件

创建新插件只需：

1. 在 `plugins/` 目录下创建新文件
2. 定义类继承 `SpiderPlugin` 并实现 `run()` 和 `validate_config()` 方法
3. 插件会自动被 `PluginManager` 发现和加载

示例：
```python
from plugins import SpiderPlugin

class MyPlugin(SpiderPlugin):
    def run(self, engine, **kwargs):
        # 使用 engine.fetch(url) 等
        return {"result": "done"}

    def validate_config(self):
        return []  # 或返回错误列表
```

---

### 注意事项

- **遵守robots.txt**：请确保您的爬取行为符合目标网站的规则
- **速率限制**：避免高频请求，配置合理的延迟
- **法律合规**：仅爬取允许公开访问的数据，尊重版权和隐私
- **代理使用**：如需大量爬取，请使用代理并遵守服务条款

---

### 许可证

本项目仅供学习和研究使用，请勿用于非法用途。
