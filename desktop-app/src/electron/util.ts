import {ipcMain} from 'electron';
import {WebContents, WebFrameMain} from 'electron/main';
import {pathToFileURL} from 'url';
import { getUIPath } from './pathResolver.js';

export function isDev() : boolean {
  return process.env.NODE_ENV === 'development';
}

export function ipcMainHandle<Key extends keyof EventPayloadMapping>(key: Key, handler: (args: any) => EventPayloadMapping[Key]){
    ipcMain.handle(key, (event, args)=> {
        validateEventFrame(event.senderFrame!);
        return handler(args);
    });
}

export function ipcWebContent<Key extends keyof EventPayloadMapping>(
    key: Key,
    webContents: WebContents,
    payload: EventPayloadMapping[Key]
) {
    webContents.send(key, payload);
}

export function validateEventFrame(frame: WebFrameMain) {
    console.log(frame.url);
    if (isDev()  && new URL(frame.url).host === 'localhost:5123'){
        return;
    }
    if (frame.url !== pathToFileURL(getUIPath()).toString()){
        throw new Error('Malicious event');
    }
}