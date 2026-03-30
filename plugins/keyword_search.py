from . import SpiderPlugin
from typing import Dict, Any, List
import requests
from urllib.parse import quote_plus

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
        self.output_format = config.get('output_format', 'list')  # 'list' or 'dict'
        self.user_agent = config.get('user_agent',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    def validate_config(self) -> List[str]:
        errors = []
        if self.search_engine not in self.SEARCH_ENGINES:
            errors.append(f"不支持的搜索引擎: {self.search_engine}")
        if not isinstance(self.max_results, int) or self.max_results <= 0:
            errors.append("max_results必须是正整数")
        return errors

    def run(self, engine, keyword: str) -> List[Dict[str, str]]:
        """
        执行搜索并返回结果。

        :param engine: SpiderEngine实例（此处未直接使用，但保留接口一致性）
        :param keyword: 搜索关键词
        :return: 搜索结果列表，每个结果是一个字典，包含'title', 'url', 'snippet'
        """
        if self.search_engine not in self.SEARCH_ENGINES:
            raise ValueError(f"不支持的搜索引擎: {self.search_engine}")

        url = self.SEARCH_ENGINES[self.search_engine].format(quote_plus(keyword))
        headers = {'User-Agent': self.user_agent}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as e:
            return [{'error': f"请求失败: {e}"}]

        # 根据不同搜索引擎解析结果（简化版）
        results = self._parse_search_results(response.text)

        # 限制返回数量
        return results[:self.max_results]

    def _parse_search_results(self, html: str) -> List[Dict[str, str]]:
        """
        解析搜索引擎结果页面。
        注意：实际网站HTML结构可能变化，需要维护选择器。

        :param html: 搜索结果页面HTML
        :return: 解析后的结果列表
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        results = []

        if self.search_engine == 'google':
            # 旧的Google选择器，可能需要更新
            for item in soup.select('div.g'):
                title_elem = item.select_one('h3')
                link_elem = item.select_one('a')
                snippet_elem = item.select_one('div.VwiC3b')
                if title_elem and link_elem:
                    results.append({
                        'title': title_elem.get_text(strip=True),
                        'url': link_elem.get('href', ''),
                        'snippet': snippet_elem.get_text(strip=True) if snippet_elem else ''
                    })
        elif self.search_engine == 'bing':
            for item in soup.select('li.b_algo'):
                title_elem = item.select_one('h2 a')
                snippet_elem = item.select_one('div.b_lineclamp2')
                if title_elem:
                    results.append({
                        'title': title_elem.get_text(strip=True),
                        'url': title_elem.get('href', ''),
                        'snippet': snippet_elem.get_text(strip=True) if snippet_elem else ''
                    })
        else:
            # 对于其他搜索引擎，返回原始HTML（可扩展）
            results.append({
                'title': f'{self.search_engine} search result',
                'url': '',
                'snippet': html[:200]  # 仅预览部分内容
            })

        return results
