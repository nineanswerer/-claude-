document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tab');
    const sections = document.querySelectorAll('.section');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetId = tab.getAttribute('data-tab');

            tabs.forEach(t => t.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));

            tab.classList.add('active');
            document.getElementById(targetId).classList.add('active');
        });
    });

    // 搜索任务
    document.getElementById('search-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const config = {
            keyword: formData.get('keyword'),
            plugin: 'KeywordSearchPlugin',
            plugin_config: {
                search_engine: formData.get('engine'),
                max_results: parseInt(formData.get('max_results'))
            }
        };

        startTask('start-btn', 'stop-btn', 'status', 'output', () => window.electronAPI.startCrawler(config));
    });

    // 通用爬取
    document.getElementById('crawl-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        let selectors;
        try {
            selectors = JSON.parse(formData.get('selectors'));
        } catch (err) {
            alert('选择器JSON格式错误');
            return;
        }

        const config = {
            url: formData.get('url'),
            selectors,
            plugin: 'GenericCrawlerPlugin'
        };

        startTask('crawl-start-btn', 'crawl-stop-btn', 'crawl-status', 'crawl-output', () => window.electronAPI.startCrawler(config));
    });

    // 数据导出（这里不通过Python，直接在渲染进程中实现）
    document.getElementById('export-form').addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        let data;
        try {
            data = JSON.parse(formData.get('data'));
        } catch (err) {
            alert('数据JSON格式错误');
            return;
        }

        const filename = formData.get('filename') || 'export';
        const format = formData.get('format');

        // 通知主进程选择保存位置
        const defaultPath = `${filename}.${format}`;
        window.electronAPI.selectFile({ defaultPath, filters: [{ name: format.toUpperCase(), extensions: [format] }] })
            .then(filePath => {
                if (!filePath) return;

                // 这里我们通过本地Node.js fs模块或Python脚本来导出
                // 为简化，我们假设Python脚本handle_export.py接受参数并执行
                const options = {
                    mode: 'text',
                    pythonPath: 'python',
                    args: [JSON.stringify({
                        data,
                        filePath,
                        format
                    })]
                };

                const { PythonShell } = require('python-shell');
                const pythonProcess = new PythonShell('handle_export.py', options);

                const outputDiv = document.getElementById('export-output');
                outputDiv.textContent = '正在导出...';

                pythonProcess.on('message', (message) => {
                    outputDiv.textContent += message + '\n';
                });

                pythonProcess.on('close', (code) => {
                    if (code === 0) {
                        outputDiv.textContent += '\n导出完成！';
                        outputDiv.style.color = '#2ecc71';
                    } else {
                        outputDiv.textContent += '\n导出失败！';
                        outputDiv.style.color = '#e74c3c';
                    }
                });
            });
    });

    // 配置保存
    document.getElementById('config-form').addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const config = {
            global: {
                delay_range: JSON.parse(formData.get('delay_range')),
                timeout: parseInt(formData.get('timeout')),
                use_proxy: formData.get('use_proxy') === 'on',
                proxy_list: formData.get('proxy_list').split('\n').filter(line => line.trim())
            }
        };

        // 保存到配置文件的逻辑（需要主进程或Node.js支持）
        // 这里需要另一个Python脚本或使用electron的fs模块
        const outputDiv = document.getElementById('config-output');
        outputDiv.textContent = '配置保存功能需要额外的Node.js脚本支持，尚未实现完整的保存逻辑。';

        // 实际项目中，应调用主进程IPC保存到YAML
    });

    // 通用任务启动函数
    async function startTask(startBtnId, stopBtnId, statusId, outputId, taskFn) {
        const startBtn = document.getElementById(startBtnId);
        const stopBtn = document.getElementById(stopBtnId);
        const statusDiv = document.getElementById(statusId);
        const outputDiv = document.getElementById(outputId);

        startBtn.disabled = true;
        stopBtn.disabled = false;
        statusDiv.textContent = '运行中...';
        statusDiv.className = 'status-bar status-running';
        outputDiv.textContent = '正在启动任务...';

        try {
            const result = await taskFn();
            outputDiv.textContent = '任务完成！\n' + (result.output || '');
            outputDiv.style.color = '#2ecc71';
        } catch (err) {
            outputDiv.textContent = '任务失败: ' + err.message;
            outputDiv.style.color = '#e74c3c';
        } finally {
            startBtn.disabled = false;
            stopBtn.disabled = true;
            statusDiv.textContent = '就绪';
            statusDiv.className = 'status-bar status-idle';
        }
    }
});
