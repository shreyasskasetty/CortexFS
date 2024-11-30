import {app, BrowserWindow, ipcMain} from 'electron';
import path from 'path';
import Database from "better-sqlite3";
import { getDbPath } from './pathResolver.js';
import {isDev} from './util.js';
// import { pollResources, getStaticData } from './resourceManager.js';
import { getPreloadPath, getUIPath } from './pathResolver.js';
import { startRabbitMQConsumer } from './consumer.js';
import { ipcMainHandle } from './util.js';
import { getSuggestions, deleteSuggestion } from './resourceManager.js';
type test = string;

export const initializeDatabase = () => {
    const dbPath = getDbPath();
    const db = new Database(dbPath, { readonly: false });

    // Create a `suggestions` table if it doesn't exist
    db.prepare(`
        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fileName TEXT NOT NULL,
            fileSize TEXT NOT NULL,
            downloadDate DATETIME NOT NULL,
            currentPath TEXT NOT NULL,
            summary TEXT,
            suggestedPaths TEXT NOT NULL, -- Store the array as a serialized string (e.g., JSON or comma-separated values)
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `).run();

    console.log("Database initialized at:", dbPath);
    return db;
};

app.on('ready', () => {
    const db = initializeDatabase();

    const mainWindow = new BrowserWindow({
        webPreferences:{
            preload: getPreloadPath(),
            contextIsolation: true
        }
    });
    if (isDev()){
        mainWindow.loadURL('http://localhost:5123');
    }else{
        mainWindow.loadFile(getUIPath());
    }
    // pollResources(mainWindow);
    ipcMainHandle("getSuggestions", ()=>{
        return getSuggestions(db);
    })
    ipcMainHandle("deleteSuggestion", (args: any)=>{
        const { id } = args;

        if (typeof id !== "number" || isNaN(id)) {
        throw new Error("Invalid ID provided for deleteSuggestion");
        }

        deleteSuggestion(db, id);
    })
    startRabbitMQConsumer(mainWindow, db);
    
});
    