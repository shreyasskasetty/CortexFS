import osUtils from 'os-utils';
import os from 'os';
import fs from 'fs';
import { BrowserWindow } from 'electron';
import { ipcWebContent } from './util.js';

const POLLING_INTERVAL = 500;

export function pollResources(mainWindow: BrowserWindow){
    setInterval(async ()=>{
        const cpuUsage = await getCpuUsage();
        const ramUsage = getRamUsage();
        const storageData = getStorageData();
        ipcWebContent('statistics', mainWindow.webContents, {cpuUsage, ramUsage, storageUsage: storageData.usage})
        // console.log(`CPU Usage: ${cpuUsage}`);
    }, POLLING_INTERVAL)
}

function getCpuUsage(): Promise<number>{
    return new Promise((resolve)=>{
        osUtils.cpuUsage(resolve);
    });
}

// export function getStaticData() {
//     const totalStorage = getStorageData().total;
//     const cpuModel = os.cpus()[0].model;
//     const totalMemoryGB = Math.floor(osUtils.totalmem() / 1024);
  
//     return {
//       totalStorage,
//       cpuModel,
//       totalMemoryGB,
//     };
//   }

export function getSuggestions(db: any){

  const rows = db.prepare("SELECT * FROM suggestions").all();

    // Convert raw database rows into structured file data
    const suggestions = rows.reduce((acc: any, row: any) => {
        acc.push({
            id: row.id,
            name: row.fileName,
            size: row.fileSize,
            downloadDate: row.downloadDate,
            currentPath: row.currentPath,
            summary: row.summary,
            suggestions: JSON.parse(row.suggestedPaths),
        });
        return acc;
    }, []);

    return suggestions;
}
  
export function deleteSuggestion(db: any, id: number) {
  db.prepare("DELETE FROM suggestions WHERE id = ?").run(id);
}

  function getRamUsage() {
    return 1 - osUtils.freememPercentage();
  }
  
  function getStorageData() {
    // requires node 18
    const stats = fs.statfsSync(process.platform === 'win32' ? 'C://' : '/');
    const total = stats.bsize * stats.blocks;
    const free = stats.bsize * stats.bfree;
  
    return {
      total: Math.floor(total / 1_000_000_000),
      usage: 1 - free / total,
    };
  }