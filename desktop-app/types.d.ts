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

type Suggestion = {
    fileName: string;
    size: string;
    downloadDate: string;
    currentPath: string;
    summary: string;
    suggestions: string[];
}
type EventPayloadMapping = {
    statistics: Statistics;
    getStaticData: StaticData;
    suggestions: any;
    showNotification: {title: string, body: string};
    getSuggestions: Suggestion[];
    deleteSuggestion: void;
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

  interface CommitSuggestionRequest {
    src_path: string;
    dst_path: string;
  }

interface Window {
    electron:  {
        subscribeStatistics: (callback: (statistics: Statistics)=> void) => Unsubcsribe;
        getStaticData: ()=> Promise<StaticData>;
        subscribeSuggestions: (callback: (suggestion: any) => void) => Unsubcsribe;
        getSuggestions: () => Promise<any>;
        deleteSuggestion: (id: number) => Promise<void>;
        // showNotification: (callback: (payload: {title: string, body: string}) => void) => Unsubcsribe;
    }
}

type Unsubcsribe = () => void;