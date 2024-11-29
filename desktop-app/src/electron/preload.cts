const electron = require('electron');

electron.contextBridge.exposeInMainWorld('electron', {
    subscribeStatistics: (callback) => {
        return ipcOn('statistics', (stats) => callback(stats))
    },
    getStaticData: () => ipcInvoke("getStaticData"),
    getSuggestions: () => ipcInvoke("getSuggestions"),
    subscribeSuggestions: (callback) =>{
        return ipcOn('suggestions', (suggestion) => callback(suggestion))
    },
} satisfies Window['electron']);

function ipcInvoke<Key extends keyof EventPayloadMapping>(
    key: Key,
): Promise<EventPayloadMapping[Key]>{
    return electron.ipcRenderer.invoke(key);
}

function ipcOn<Key extends keyof EventPayloadMapping>(
    key: Key, 
    callback: (payload: EventPayloadMapping[Key]) => void
) {
    const cb = (_: Electron.IpcRendererEvent, payload: any) => callback(payload);
    electron.ipcRenderer.on(key, cb);
    return () => electron.ipcRenderer.off(key, cb);
}

ipcOn('showNotification', (payload) => {
    const notification = new Notification(payload.title, {body: payload.body});
    notification.onclick = () => {
        console.log('Notification clicked');
    };
});