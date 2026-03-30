from . import SpiderPlugin
from typing import Dict, Any, List
import requests
from urllib.parse import quote_plus
import re

class KeywordSearchPlugin(SpiderPlugin):
    """
    关键词搜索插件：通过搜索引擎搜索关键词，返回搜索结果。
    支持Google、Bing、DuckDuckGo等。
    """

    SEARCH_ENGINES = {
        'google': 'https://www.google.com/search?q={}',
        'bing': 'https://www.bing.com/search?q={}',
        'duckduckgo': 'https://duckduckgo.com/?q={}'
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.search_engine = config.get('search_engine', 'google')
        self.max_results = config.get('max_results', 10)
        self.output_format = config.get('output_format', 'list')

        # 使用简单的UA，避免触发反爬
        self.user_agent = config.get('user_agent',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        # 最小化请求头
        self.additional_headers = config.get('additional_headers', {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

    def validate_config(self) -> List[str]:
        errors = []
        if self.search_engine not in self.SEARCH_ENGINES:
            errors.append(f"不支持的搜索引擎: {self.search_engine}")
        if not isinstance(self.max_results, int) or self.max_results <= 0:
            errors.append("max_results必须是正整数")
        return errors

    def run(self, engine, keyword: str) -> List[Dict[str, str]]:
        if self.search_engine not in self.SEARCH_ENGINES:
            raise ValueError(f"不支持的搜索引擎: {self.search_engine}")

        url = self.SEARCH_ENGINES[self.search_engine].format(quote_plus(keyword))

        headers = {'User-Agent': self.user_agent}
        headers.update(self.additional_headers)

        params = {}
        if self.search_engine == 'google':
            params = {'hl': 'en', 'gl': 'us'}

        try:
            print(f"[DEBUG] 正在请求: {url}")
            response = requests.get(url, headers=headers, params=params, timeout=15, allow_redirects=True)
            response.raise_for_status()

            content_length = len(response.text)
            print(f"[DEBUG] 响应大小: {content_length} 字节")

            if self.search_engine == 'google':
                if 'unusual traffic' in response.text.lower() or 'captcha' in response.text.lower() or content_length < 5000:
                    return [{'error': 'Google检测到异常流量，已被屏蔽', 'partial': True}]

        except Exception as e:
            print(f"[ERROR] 搜索请求失败: {e}")
            return [{'error': f"请求失败: {e}"}]

        results = self._parse_search_results(response.text)
        print(f"[DEBUG] 解析到 {len(results)} 条结果")
        return results[:self.max_results]

    def _parse_search_results(self, html: str) -> List[Dict[str, str]]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        results = []

        if self.search_engine == 'google':
            print(f"[DEBUG] Google parsing...")
            # Google现在不使用/url?q=格式，直接返回屏蔽页面或JS渲染
            # 尝试查找所有h3元素
            h3s = soup.find_all('h3')
            print(f"[DEBUG] Found {len(h3s)} h3 elements")
            for h3 in h3s[:self.max_results]:
                parent_link = h3.find_parent('a')
                if parent_link and parent_link.get('href'):
                    title = h3.get_text(strip=True)
                    url = parent_link['href']
                    if url.startswith('/url?q='):
                        url = url.split('/url?q=')[1].split('&')[0]
                    if title and url.startswith('http'):
                        results.append({'title': title, 'url': url, 'snippet': ''})
            if not results:
                print(f"[DEBUG] Google未找到结果，可能被屏蔽")

        elif self.search_engine == 'bing':
            print(f"[DEBUG] Bing parsing...")
            items = soup.select('li.b_algo')
            print(f"[DEBUG] Found {len(items)} li.b_algo items")
            for item in items[:self.max_results]:
                title_elem = item.select_one('h2 a')
                snippet_elem = item.select_one('div.b_lineclamp2, div.b_caption, p')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                    print(f"[DEBUG] Bing result: title='{title[:50]}'")
                    results.append({'title': title, 'url': url, 'snippet': snippet})
        else:
            results.append({
                'title': f'{self.search_engine} search completed',
                'url': '',
                'snippet': f'Search for "{keyword}" completed. Add parser for this engine.'
            })

        return results
