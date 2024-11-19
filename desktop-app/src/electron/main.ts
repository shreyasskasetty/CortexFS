import {app, BrowserWindow, ipcMain} from 'electron';
import path from 'path';
import {isDev} from './util.js';
// import { pollResources, getStaticData } from './resourceManager.js';
import { getPreloadPath, getUIPath } from './pathResolver.js';
// import { ipcMainHandle } from './util.js';
type test = string;

app.on('ready', () => {
    const mainWindow = new BrowserWindow({
        webPreferences:{
            preload: getPreloadPath()
        }
    });

    if (isDev()){
        mainWindow.loadURL('http://localhost:5123');
    }else{
        mainWindow.loadFile(getUIPath());
    }
    // pollResources(mainWindow);
    // ipcMainHandle("getStaticData", ()=>{
    //     return getStaticData();
    // })
    
});
    