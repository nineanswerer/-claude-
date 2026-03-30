# 修复搜索结果显示问题

## Context (问题背景)
用户反馈两个问题：
1. 使用Google搜索引擎时总是显示"没有找到结果"（Bing正常）
2. 搜索结果中URL不可点击跳转，标题仅是黑色文本而非可点击链接

从测试可知：
- Bing API返回正常数据：`[{title: "...", url: "...", snippet: ""}]`
- 前端将所有字段渲染为普通文本`<p>`，没有链接功能

## Objective (目标)
1. 修复Google搜索的解析器，使其能正确提取搜索结果
2. 改进前端显示：title应为蓝色可点击链接，url也应显示为链接
3. 优化结果布局，使信息更清晰易读

## Critical Files (关键文件)
- `frontend/web_app/static/script.js` - 结果渲染逻辑
- `frontend/web_app/static/style.css` - 链接样式
- `plugins/keyword_search.py` - Google搜索解析器

## Implementation Plan (实施计划)

### Phase 1: 修复前端显示 (script.js + style.css)
**修改 `displayResults` 函数：**
- 检测数据中是否包含 `title` 和 `url` 字段
- 如果同时存在，将 title 渲染为 `<a href="url" target="_blank" class="result-title">title</a>`
- 将 url 单独渲染为 `<a href="url" target="_blank" class="result-url">url</a>`
- 保留 snippet 字段（如果有）
- 调整HTML结构为：
  ```html
  <div class="result-item">
    <a class="result-title" href="...">Title text</a>
    <a class="result-url" href="...">URL</a>
    <p class="result-snippet">Snippet text</p>
  </div>
  ```

**更新CSS：**
- `.result-title` 样式：蓝色、下划线、悬停变色
- `.result-url` 样式：小字号、灰色、可点击

### Phase 2: 修复Google搜索解析器
**修改 `plugins/keyword_search.py` 的 `_parse_search_results` 方法：**
- Google经常改版HTML结构，需要更新选择器
- 尝试多个备用选择器策略：
  1. 主选择器：`div.g` (旧的)
  2. 备用1：`div[data-header-feature="0"]`
  3. 备用2：`div.VkpGBb` (常见容器)
- 提取 title: `h3` 元素
- 提取 url: `a` 元素的href
- 提取 snippet: `div.VwiC3b` 或 `span.aCOpRe`

**添加调试日志**到Google解析过程，查看实际获取的HTML片段。

### Phase 3: 测试验证
1. 重启Flask应用
2. 清空浏览器缓存，强制刷新
3. 测试Google搜索（关键词："Python"）
4. 测试Bing搜索（确保仍然正常）
5. 验证：
   - 结果显示为可点击链接
   - 标题为蓝色
   - URL可点击跳转
   - Google返回正确结果（非空）

### Phase 4: Edge Cases处理
- 如果解析失败，返回错误信息而非空列表
- 考虑添加更详细的日志记录
- 处理title或url缺失的情况

## How to Test (测试方法)
1. 打开 http://localhost:5000
2. 强制刷新（Ctrl+F5）
3. 测试Google搜索：
   - Keyword: "Python"
   - Engine: Google
   - Max results: 5
   - Expected: 显示5条可点击结果
4. 测试Bing搜索（确认未破坏）
5. 点击任一结果链接，应在新标签页打开

## Rollback Plan (回滚计划)
如遇问题，可：
1. 恢复 `script.js` 和 `keyword_search.py` 的旧版本
2. 保留修改记录在版本控制中
