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

interface Window {
    electron:  {
        subscribeStatistics: (callback: (statistics: Statistics)=> void) => Unsubcsribe;
        getStaticData: ()=> Promise<StaticData>;
    }
}

type Unsubcsribe = () => void;