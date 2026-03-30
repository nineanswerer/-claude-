from . import SpiderPlugin
from typing import Dict, Any, List

class GenericCrawlerPlugin(SpiderPlugin):
    """
    通用爬虫插件：允许用户传入URL和CSS选择器，使用SpiderEngine执行抓取。
    这是最灵活的插件，适用于任何网站。
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # 从配置中预定义选择器（可选）
        self.default_selectors = config.get('selectors', {})

    def validate_config(self) -> List[str]:
        # 此插件不需要严格验证，selectors可为空
        return []

    def run(self, engine, url: str, selectors: Dict[str, str] = None) -> Dict[str, Any]:
        """
        执行通用爬取。

        :param engine: SpiderEngine实例
        :param url: 目标URL
        :param selectors: CSS选择器字典，如果为None则使用配置中的default_selectors
        :return: 提取的数据字典
        """
        selectors = selectors or self.default_selectors
        if not selectors:
            raise ValueError("必须提供selectors参数或在配置中设置default_selectors")

        return engine.crawl(url, selectors=selectors)


class MultiPageCrawlerPlugin(SpiderPlugin):
    """
    多页爬虫插件：从一个起始URL开始，跟随分页链接抓取多页内容。
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.max_pages = config.get('max_pages', 5)
        self.next_page_selector = config.get('next_page_selector', 'a.next')
        self.item_selector = config.get('item_selector', 'div.item')
        self.fields = config.get('fields', {})

    def validate_config(self) -> List[str]:
        errors = []
        if not isinstance(self.max_pages, int) or self.max_pages <= 0:
            errors.append("max_pages必须是正整数")
        if not self.next_page_selector:
            errors.append("必须配置next_page_selector")
        if not self.item_selector:
            errors.append("必须配置item_selector")
        return errors

    def run(self, engine, start_url: str) -> List[Dict[str, Any]]:
        """
        从起始URL开始，抓取多页。

        :param engine: SpiderEngine实例
        :param start_url: 起始页面URL
        :return: 所有页面提取的数据列表
        """
        all_items = []
        current_url = start_url
        pages_crawled = 0

        while current_url and pages_crawled < self.max_pages:
            print(f"正在抓取第 {pages_crawled + 1} 页: {current_url}")

            # 抓取当前页
            response = engine.fetch(current_url)
            if response is None:
                break

            soup = engine.parse_html(response.text)

            # 提取当前页的所有项目
            items = self._extract_items(soup)
            all_items.extend(items)

            # 获取下一页链接
            next_link = soup.select_one(self.next_page_selector)
            if next_link and next_link.get('href'):
                current_url = next_link['href']
                # 处理相对URL
                if not current_url.startswith('http'):
                    from urllib.parse import urljoin
                    current_url = urljoin(start_url, current_url)
            else:
                break

            pages_crawled += 1

        return all_items

    def _extract_items(self, soup) -> List[Dict[str, Any]]:
        """
        从页面中提取多个项目数据。

        :param soup: BeautifulSoup对象
        :return: 提取的数据列表
        """
        items = []
        item_elements = soup.select(self.item_selector)

        for item_elem in item_elements:
            item_data = {}
            for field_name, selector in self.fields.items():
                elements = item_elem.select(selector)
                if elements:
                    if len(elements) == 1:
                        item_data[field_name] = elements[0].get_text(strip=True)
                    else:
                        item_data[field_name] = [el.get_text(strip=True) for el in elements]
                else:
                    item_data[field_name] = None
            items.append(item_data)

        return items
