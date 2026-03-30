const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    startCrawler: (config) => ipcRenderer.invoke('start-crawler', config),
    stopCrawler: () => ipcRenderer.invoke('stop-crawler'),
    selectFile: (options) => ipcRenderer.invoke('select-file', options),
    selectDirectory: (options) => ipcRenderer.invoke('select-directory', options),
    getVersion: () => ipcRenderer.invoke('get-version')
});
