document.addEventListener('DOMContentLoaded', function() {
    const navButtons = document.querySelectorAll('.nav-btn');
    const sections = document.querySelectorAll('.section');

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.id.replace('btn-', '') + '-section';

            navButtons.forEach(b => b.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));

            btn.classList.add('active');
            document.getElementById(targetId).classList.add('active');
        });
    });

    // 搜索表单提交
    document.getElementById('search-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const keyword = document.getElementById('search-keyword').value;
        const engine = document.getElementById('search-engine').value;
        const maxResults = document.getElementById('max-results').value;

        const payload = {
            keyword,
            plugin: 'KeywordSearchPlugin',
            plugin_config: {
                search_engine: engine,
                max_results: parseInt(maxResults)
            }
        };

        showLoading('search-results');

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            displayResults('search-results', result);
        } catch (error) {
            showError('search-results', '请求失败: ' + error.message);
        }
    });

    // 爬取表单提交
    document.getElementById('crawl-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = document.getElementById('crawl-url').value;
        const selectorsText = document.getElementById('crawl-selectors').value;
        let selectors;

        try {
            selectors = JSON.parse(selectorsText);
        } catch (err) {
            showError('crawl-results', '选择器格式错误，必须是有效的JSON');
            return;
        }

        const payload = {
            url,
            selectors,
            plugin: 'GenericCrawlerPlugin'
        };

        showLoading('crawl-results');

        try {
            const response = await fetch('/api/crawl', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            displayResults('crawl-results', result);
        } catch (error) {
            showError('crawl-results', '请求失败: ' + error.message);
        }
    });

    // 导出表单提交
    document.getElementById('export-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const dataText = document.getElementById('export-data').value;
        const filename = document.getElementById('export-filename').value || 'export';
        const format = document.getElementById('export-format').value;

        let data;
        try {
            data = JSON.parse(dataText);
        } catch (err) {
            showError('export-results', '数据格式错误，必须是有效的JSON');
            return;
        }

        const payload = {
            data,
            filename,
            format
        };

        showLoading('export-results');

        try {
            const response = await fetch('/api/export', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            displayResults('export-results', result);
        } catch (error) {
            showError('export-results', '请求失败: ' + error.message);
        }
    });
});

function showLoading(containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = '<p class="info">加载中...</p>';
}

function showError(containerId, message) {
    const container = document.getElementById(containerId);
    container.innerHTML = `<p class="error">${message}</p>`;
}

function displayResults(containerId, result) {
    const container = document.getElementById(containerId);
    console.log('[displayResults] container element:', container);
    container.innerHTML = '<p class="info">正在处理结果...</p>';

    console.log('[displayResults] result:', result);
    console.log('[displayResults] containerId:', containerId);

    // 给一个小延迟让用户看到加载状态
    setTimeout(() => {
        container.innerHTML = '';

        if (!result.success) {
            console.log('[displayResults] result.error:', result.error);
            container.innerHTML = `<p class="error">错误: ${result.error}</p>`;
            return;
        }

        const data = result.data;
        console.log('[displayResults] data:', data, 'type:', typeof data);

        if (Array.isArray(data)) {
            if (data.length === 0) {
                container.innerHTML = '<p class="info">没有找到结果</p>';
            } else {
                data.forEach(item => {
                    if (typeof item === 'object' && item !== null) {
                        const div = document.createElement('div');
                        div.className = 'result-item';

                        // 特殊处理：title和url组合成标题链接
                        const title = item.title || item.Title;
                        const url = item.url || item.URL || item.link;
                        const snippet = item.snippet || item.Snippet || item.description || '';

                        // 1. 标题链接 (如果有title和url)
                        if (title && url) {
                            const titleLink = document.createElement('a');
                            titleLink.className = 'result-title';
                            titleLink.href = url;
                            titleLink.textContent = title;
                            titleLink.target = '_blank';
                            titleLink.rel = 'noopener noreferrer';
                            div.appendChild(titleLink);
                        } else if (title) {
                            // 只有标题无链接
                            const titleElem = document.createElement('div');
                            titleElem.className = 'result-title';
                            titleElem.textContent = title;
                            div.appendChild(titleElem);
                        }

                        // 2. URL链接显示
                        if (url) {
                            const urlLink = document.createElement('a');
                            urlLink.className = 'result-url';
                            urlLink.href = url;
                            urlLink.textContent = url;
                            urlLink.target = '_blank';
                            urlLink.rel = 'noopener noreferrer';
                            div.appendChild(urlLink);
                        }

                        // 3. Snippet摘要
                        if (snippet) {
                            const snippetElem = document.createElement('p');
                            snippetElem.className = 'result-snippet';
                            snippetElem.textContent = snippet;
                            div.appendChild(snippetElem);
                        }

                        // 4. 其他字段
                        for (const [key, value] of Object.entries(item)) {
                            if (key !== 'title' && key !== 'url' && key !== 'link' && key !== 'snippet' && key !== 'Snippet' && key !== 'description') {
                                const p = document.createElement('p');
                                p.innerHTML = `<strong>${key}:</strong> ${value !== null && value !== undefined ? value : 'N/A'}`;
                                div.appendChild(p);
                            }
                        }

                        container.appendChild(div);
                    } else {
                        const p = document.createElement('p');
                        p.textContent = item;
                        container.appendChild(p);
                    }
                });
            }
        } else if (typeof data === 'object' && data !== null) {
            const div = document.createElement('div');
            div.className = 'result-item';
            let content = '';
            for (const [key, value] of Object.entries(data)) {
                const displayValue = (value === null || value === undefined) ? 'N/A' : value;
                content += `<p><strong>${key}:</strong> ${displayValue}</p>`;
            }
            div.innerHTML = content || '<p class="info">(无数据)</p>';
            container.appendChild(div);
        } else if (typeof data === 'string') {
            const p = document.createElement('p');
            p.textContent = data;
            container.appendChild(p);
        } else {
            container.innerHTML = '<p class="info">没有结果</p>';
        }

        if (result.filepath) {
            const p = document.createElement('p');
            p.className = 'success';
            p.textContent = `已导出到: ${result.filepath}`;
            container.appendChild(p);
        }
    }, 100); // 100ms延迟后显示结果
}
