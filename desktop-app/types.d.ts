type Statistics = {
    cpuUsage: number;
    ramUsage: number;
    storageUsage: number;
};

type StaticData = {
    totalStorage: number;
    cpuModel: string;
    totalMemoryGB: number;
};

type EventPayloadMapping = {
    statistics: Statistics;
    getStaticData: StaticData;
}

interface FileNode {
    name: string;
    type: 'file' | 'folder';
    path: string;
    children?: FileNode[];
    summary?: string;
    source?: string;
    destination?: string;
    size?: string;
    lastModified?: string;
    fileType?: string;
    status?: string;
  }
  interface BatchOrganizeRequest {
    path: string; // Define the expected structure of the request body
  }

  interface WatchDogStartRequest {
    watch_directory: string;
    target_directory: string;
  }
  
  interface CommitRequest {
    base_path: string;
    src_path: string;
    dst_path: string;
  }

interface Window {
    electron:  {
        subscribeStatistics: (callback: (statistics: Statistics)=> void) => Unsubcsribe;
        getStaticData: ()=> Promise<StaticData>;
    }
}

type Unsubcsribe = () => void;