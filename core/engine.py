import requests
from bs4 import BeautifulSoup
import random
from typing import Optional, Dict, Any, List
import time
from fake_useragent import UserAgent

class SpiderEngine:
    """
    核心爬虫引擎，负责发送HTTP请求、解析HTML内容和提取数据。
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化爬虫引擎。

        :param config: 配置字典，可包括：
            - use_proxy: 是否使用代理 (bool)
            - proxy_list: 代理列表 (List[str])
            - delay_range: 请求间隔范围 (tuple of float, e.g., (1, 3))
            - headers: 自定义请求头 (Dict[str, str])
            - timeout: 请求超时时间 (int, 秒)
        """
        self.config = config or {}
        self.session = requests.Session()
        self.ua = UserAgent()
        self._setup_session()

    def _setup_session(self):
        """配置会话，包括请求头、代理等。"""
        # 设置默认请求头
        default_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        # 如果用户提供了自定义headers，则合并
        if 'headers' in self.config:
            default_headers.update(self.config['headers'])

        # 设置User-Agent
        default_headers['User-Agent'] = self.ua.random

        self.session.headers.update(default_headers)

        # 设置代理（如果配置了）
        if self.config.get('use_proxy') and self.config.get('proxy_list'):
            proxy = random.choice(self.config['proxy_list'])
            self.session.proxies = {
                'http': proxy,
                'https': proxy
            }

        # 设置超时
        self.timeout = self.config.get('timeout', 10)

    def fetch(self, url: str, params: Optional[Dict] = None,
              method: str = 'GET', data: Optional[Dict] = None) -> Optional[requests.Response]:
        """
        发送HTTP请求并返回响应对象。

        :param url: 目标URL
        :param params: URL参数 (用于GET请求)
        :param method: HTTP方法 ('GET' 或 'POST')
        :param data: 表单数据 (用于POST请求)
        :return: 响应对象，如果请求失败则返回None
        """
        try:
            # 添加随机延迟以避免被反爬
            delay_range = self.config.get('delay_range', (1, 3))
            time.sleep(random.uniform(*delay_range))

            if method.upper() == 'GET':
                response = self.session.get(url, params=params, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, params=params, data=data, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # 检查响应状态
            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
            return None

    def parse_html(self, html_content: str) -> BeautifulSoup:
        """
        解析HTML内容并返回BeautifulSoup对象。

        :param html_content: HTML字符串
        :return: BeautifulSoup对象
        """
        return BeautifulSoup(html_content, 'lxml')

    def extract_data(self, soup: BeautifulSoup, selectors: Dict[str, str]) -> Dict[str, Any]:
        """
        根据CSS选择器从BeautifulSoup对象中提取数据。

        :param soup: BeautifulSoup对象
        :param selectors: 选择器字典，键为字段名，值为CSS选择器
        :return: 提取的数据字典
        """
        extracted_data = {}
        for key, selector in selectors.items():
            elements = soup.select(selector)
            if elements:
                # 如果只有一个元素，返回其文本；如果有多个，返回文本列表
                if len(elements) == 1:
                    extracted_data[key] = elements[0].get_text(strip=True)
                else:
                    extracted_data[key] = [el.get_text(strip=True) for el in elements]
            else:
                extracted_data[key] = None
        return extracted_data

    def crawl(self, url: str, selectors: Dict[str, str],
              params: Optional[Dict] = None, method: str = 'GET',
              data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        执行完整的爬取流程：请求 -> 解析 -> 提取。

        :param url: 目标URL
        :param selectors: CSS选择器字典
        :param params: URL参数
        :param method: HTTP方法
        :param data: 表单数据
        :return: 提取的数据字典，如果失败则返回None
        """
        response = self.fetch(url, params=params, method=method, data=data)
        if response is None:
            return None

        soup = self.parse_html(response.text)
        return self.extract_data(soup, selectors)

# 示例用法
if __name__ == "__main__":
    # 配置示例
    config = {
        'use_proxy': False,  # 如果有代理可设为True并提供列表
        # 'proxy_list': ['http://proxy1:port', 'http://proxy2:port'],
        'delay_range': (1, 2),
        'headers': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        },
        'timeout': 15
    }

    engine = SpiderEngine(config)

    # 定义要提取的数据选择器（以爬取新闻标题为例）
    selectors = {
        'title': 'h1.title',
        'content': 'div.article-content',
        'author': 'span.author',
        'publish_time': 'time.publish-time'
    }

    # 执行爬取（这里使用一个示例URL，实际使用时请替换为目标网站）
    # 注意：请遵守目标网站的robots.txt和服务条款
    result = engine.crawl(
        url='https://example.com/news/article',
        selectors=selectors
    )

    if result:
        print("爬取成功:")
        for key, value in result.items():
            print(f"{key}: {value}")
    else:
        print("爬取失败")