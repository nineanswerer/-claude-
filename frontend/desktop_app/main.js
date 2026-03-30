const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { PythonShell } = require('python-shell');
const axios = require('axios');

let mainWindow;
let pythonProcess = null;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        title: '可配置网络爬虫桌面版'
    });

    // 加载本地HTML页面（或可以选择加载Flask服务器页面）
    // 这里我们使用内嵌的HTML，而不是连接Flask
    mainWindow.loadFile(path.join(__dirname, 'index.html'));

    // 开发时打开DevTools
    // mainWindow.webContents.openDevTools();

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

app.whenReady().then(() => {
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

// IPC处理器

// 启动爬虫任务（通过Python后端）
ipcMain.handle('start-crawler', async (event, config) => {
    return new Promise((resolve, reject) => {
        const options = {
            mode: 'text',
            pythonPath: 'python',
            pythonOptions: ['-u'],
            scriptPath: path.join(__dirname, '..', '..', 'core'),
            args: [JSON.stringify(config)]
        };

        pythonProcess = new PythonShell('crawler_task.py', options);

        let result = '';
        let error = '';

        pythonProcess.on('message', (message) => {
            result += message + '\n';
        });

        pythonProcess.on('error', (err) => {
            error = err.message;
        });

        pythonProcess.on('close', (code) => {
            if (code === 0) {
                resolve({ success: true, output: result });
            } else {
                reject(new Error(error || `Python进程退出码: ${code}`));
            }
        });
    });
});

// 停止爬虫
ipcMain.handle('stop-crawler', async () => {
    if (pythonProcess) {
        pythonProcess.kill();
        pythonProcess = null;
        return { success: true, message: '已停止' };
    }
    return { success: false, message: '没有运行中的任务' };
});

// 选择文件保存位置
ipcMain.handle('select-file', async (event, { defaultPath, filters }) => {
    const result = await dialog.showSaveDialog(mainWindow, {
        defaultPath,
        filters: filters || [{ name: '所有文件', extensions: ['*'] }]
    });
    return result.canceled ? null : result.filePath;
});

// 选择目录
ipcMain.handle('select-directory', async (event, { defaultPath }) => {
    const result = await dialog.showOpenDialog(mainWindow, {
        properties: ['openDirectory'],
        defaultPath
    });
    return result.canceled ? null : result.filePaths[0];
});

// 获取应用版本
ipcMain.handle('get-version', async () => {
    return app.getVersion();
});
