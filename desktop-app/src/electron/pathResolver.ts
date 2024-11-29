import path from 'path';
import { app } from 'electron';
import { isDev} from './util.js';

export function getPreloadPath() {
    return path.join(app.getAppPath(),
        isDev() ? '.' : '..', '/dist-electron/preload.cjs'
    )
}

export const getDbPath = () => {
    const dbName = "app-data.db";
    return isDev()
        ? path.join(app.getAppPath(), dbName) // Development environment
        : path.join(app.getPath("userData"), dbName); // Production environment
};

export function getUIPath(){
    return path.join(app.getAppPath(), '/dist-react/index.html')
}

export function getAssetPath() {
    return path.join(app.getAppPath(), isDev() ? '.' : '..', 'src/assets')
}