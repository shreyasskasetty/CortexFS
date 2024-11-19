import React, { useEffect, useState } from 'react';
import { FolderOpen, File, Check, X, FolderTree, Clock, ArrowRight, Info, FileText } from 'lucide-react';
import { Card, CardContent } from './ui/card';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Alert, AlertTitle, AlertDescription } from './ui/alert';
import axios, { AxiosRequestConfig } from 'axios';

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

interface CommitRequest {
  base_path: string;
  src_path: string;
  dst_path: string;
}

const FileOrganizer = () => {
  const [directoryPath, setDirectoryPath] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);
  const [commitList, setCommitList] = useState<FileNode[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [fileStructure, setFileStructure] = useState<FileNode | null>(null);
  // Sample data structure - replace with your actual data

  useEffect(()=>{
    console.log(commitList)
  })

  const sendRequest = async (directoryPath: string) => {
    const data: BatchOrganizeRequest = { path: directoryPath };

    const config: AxiosRequestConfig = {
      headers: {
        'Content-Type': 'application/json', // Ensure the content type is JSON
      },
    };

    try {
      const response = await axios.post('http://0.0.0.0:8000/batch-organize', data, config);
      console.log(response.data);
      return response.data;
    } catch (error) {
      alert('Error Occured: '+ error)
      console.error('Error occurred:', error);
    }
    return null;
  };

  const handleOrganize = async () => {
    setIsLoading(true);
    // Simulate loading delay (replace with actual logic)
    if(directoryPath === ''){
      alert('Directory path cannot be null!');
      return;
    }
    const data : any = await sendRequest(directoryPath);
    if (data) {
      console.log(data)
      // Update the file structure when the response is received
      setFileStructure(data.treeStructure);
    } else {
      alert('Failed to fetch file structure');
    }
    setTimeout(() => {
      // Add your organization logic here
      console.log('Organizing directory:', directoryPath);
      console.log('Files to be organized:', commitList);
      setIsLoading(false);
    }, 2000);
  };

  const isNodeInCommitList = (node: FileNode): boolean => {
    return commitList.some(item => item.path === node.path);
  };

  const sendCommitRequest =  async (source_path: string, destination_path: string) => {
    const data: CommitRequest = { base_path: directoryPath, src_path: source_path, dst_path: destination_path};

    const config: AxiosRequestConfig = {
      headers: {
        'Content-Type': 'application/json', // Ensure the content type is JSON
      },
    };

    try {
      const response = await axios.post('http://0.0.0.0:8000/commit', data, config);
      console.log(response.data);
      return response.data;
    } catch (error) {
      alert('Error Occured: '+ error)
      console.error('Error occurred:', error);
    }
    return null;
  }

  const handleCommit = (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
      if(commitList.length === 0){
        alert('Commit List is empty')
      }
      commitList.forEach(async (node: FileNode)=>{
        if(node.type === "file"){
          console.log("source:" + node.source! + "\ndestination:" +  node.destination!)
          const data = await sendCommitRequest(node.source!, node.destination!)
          if(data){
            setCommitList([]);
            setFileStructure(null);
          }
        }
      })
      //make a call to the backend
  }

  const handleCommitToggle = (node: FileNode, e: React.MouseEvent) => {
    e.stopPropagation();
    
    const toggleNode = (currentNode: FileNode): FileNode[] => {
      const result: FileNode[] = [];
      result.push(currentNode);
      
      if (currentNode.children) {
        currentNode.children.forEach(child => {
          result.push(...toggleNode(child));
        });
      }
      return result;
    };

    const nodesToToggle = toggleNode(node);
    
    if (isNodeInCommitList(node)) {
      // Remove node and all its children from commit list
      setCommitList(commitList.filter(item => 
        !nodesToToggle.some(toggleItem => toggleItem.path === item.path)
      ));
    } else {
      // Add node and all its children to commit list
      const newCommitList = [...commitList];
      nodesToToggle.forEach(toggleItem => {
        if (!newCommitList.some(item => item.path === toggleItem.path)) {
          newCommitList.push(toggleItem);
        }
      });
      setCommitList(newCommitList);
    }
  };

  const renderFileTree = (node: FileNode, depth = 0): JSX.Element => {
    const isCommitted = isNodeInCommitList(node);
  
    return (
      <div key={node.path} className="relative">
        {/* Render node */}
        <Card
          className={`mb-2 transition-colors duration-200 ${
            isCommitted ? 'bg-green-100' : ''
          }`}
          style={{
            marginLeft: `${depth * 1.5}rem`, // Indentation based on depth
          }}
        >
          <CardContent className="p-4 flex items-center justify-between">
            <div
              className="flex items-center gap-2 cursor-pointer"
              onClick={() => node.type === 'file' && setSelectedFile(node)}
            >
              {node.type === 'folder' ? (
                <FolderOpen className="text-blue-500" size={20} />
              ) : (
                <File className="text-gray-500" size={20} />
              )}
              <span>{node.name}</span>
            </div>
            <div className="flex gap-2">
              <Check
                className={`cursor-pointer ${
                  isCommitted ? 'text-green-500' : 'text-gray-400'
                }`}
                size={20}
                onClick={(e) => handleCommitToggle(node, e)}
              />
              <X
                className="cursor-pointer text-gray-400 hover:text-red-500"
                size={20}
              />
            </div>
          </CardContent>
        </Card>
  
        {/* Recursively render children */}
        {node.type === 'folder' &&
          node.children?.map((child) => renderFileTree(child, depth + 1))}
      </div>
    );
  };
  
  const FileDetailRow: React.FC<{ icon: React.ElementType; label: string; value: string }> = ({ icon: Icon, label, value }) => (
    <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50">
      <Icon size={18} className="text-gray-500" />
      <span className="text-sm text-gray-600">{label}:</span>
      <span className="text-sm font-medium">{value}</span>
    </div>
  );

  const renderSummaryPanel = () => {
    if (!selectedFile) {
      return (
        <div className="h-full flex flex-col items-center justify-center text-center p-8">
          <FileText size={48} className="text-gray-300 mb-4" />
          <h3 className="text-lg font-semibold text-gray-600 mb-2">No File Selected</h3>
          <p className="text-gray-500">Select a file from the directory tree to view its details</p>
        </div>
      );
    }

    const isCommitted = isNodeInCommitList(selectedFile);

    return (
      <div className="space-y-6">
        {/* File Header */}
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-semibold mb-1">{selectedFile.name}</h2>
            <p className="text-sm text-gray-500">{selectedFile.fileType}</p>
          </div>
          <Button 
            variant={isCommitted ? "secondary" : "default"}
            size="sm"
            onClick={(e) => handleCommitToggle(selectedFile, e)}
          >
            {isCommitted ? "Remove from Commit" : "Add to Commit"}
          </Button>
        </div>

        {/* Status Alert */}
        <Alert>
          <Info className="h-4 w-4" />
          <AlertTitle>File Status</AlertTitle>
          <AlertDescription>{selectedFile.status}</AlertDescription>
        </Alert>

        {/* File Details Card */}
        <Card>
          <CardContent className="p-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">File Details</h3>
            <div className="space-y-2">
              <FileDetailRow 
                icon={Info} 
                label="Size" 
                value={selectedFile.size!}
              />
              <FileDetailRow 
                icon={Clock} 
                label="Last Modified" 
                value={selectedFile.lastModified!}
              />
            </div>
          </CardContent>
        </Card>

        {/* Path Information */}
        <Card>
          <CardContent className="p-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Path Information</h3>
            <div className="space-y-4">
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Source</p>
                <p className="text-sm font-medium break-all">{selectedFile.source}</p>
              </div>
              <div className="flex justify-center">
                <ArrowRight className="text-gray-400" />
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Destination</p>
                <p className="text-sm font-medium break-all">{selectedFile.destination}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Summary Section */}
        <Card>
          <CardContent className="p-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Summary</h3>
            <p className="text-sm text-gray-600 leading-relaxed">
              {selectedFile.summary}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  };

  return (
    <div className="h-screen flex flex-col">
      <div className="p-4 flex gap-4 border-b">
        <Input
          value={directoryPath}
          onChange={(e) => setDirectoryPath(e.target.value)}
          placeholder="Enter directory path..."
          className="flex-grow"
        />
        <Button onClick={handleOrganize}>
          Organize
        </Button>
      </div>
      <div className="flex-1 flex">
        {/* Left Panel - Directory Tree */}
        <div className="w-1/2 p-4 border-r overflow-auto">
          <div className="flex items-center gap-2 mb-4">
            <FolderTree className="text-blue-500" />
            <h2 className="text-lg font-semibold">New Directory Structure</h2>
            {fileStructure?
              (<Button 
              variant="default"
              size="sm"
              onClick={(e) => handleCommit(e)}
            >
              Commit Changes
            </Button>):""
            }
          </div>
          {isLoading ? ( // Conditional rendering based on loading state
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-500">Loading...</p> {/* Replace with a loading animation if desired */}
            </div>
          ) : fileStructure ? ( // Check if fileStructure is set
            renderFileTree(fileStructure) // Show file structure when available
          ) : (
            <div className="flex items-center justify-center h-full">
              <img src="src/ui/assets/cortex.svg" alt="Cortex FS" className="max-w-full h-auto" /> {/* Static image */}
            </div>
          )}
        </div>
        
        {/* Right Panel - File Summary */}
        <div className="w-1/2 p-6 overflow-auto bg-gray-50">
          {renderSummaryPanel()}
        </div>
      </div>
    </div>
  );
};

export default FileOrganizer;