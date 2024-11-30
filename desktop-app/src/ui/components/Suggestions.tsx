import React, { useEffect, useState } from 'react';
import { FolderTree, Bell, Settings, CheckCircle, XCircle, ArrowLeft, FileText, X} from 'lucide-react';
import axios, { AxiosRequestConfig } from 'axios';
import { send } from 'vite';

const SuggestionDetail = ({ file, suggestions, onBack, onAccept, onReject }: any) => {
  useEffect(() => {
    window.electron.subscribeSuggestions((suggestion: any) => {
      // console.log('Received suggestion:', suggestion);
      // Update the suggestions
      // console.log(file)
    });
  }, []);

  return (
    <div className="p-6">
      <button 
        onClick={onBack}
        className="flex items-center text-gray-400 hover:text-white mb-6"
      >
        <ArrowLeft className="mr-2" size={20} />
        Back to Suggestions
      </button>

      <div className="mb-6">
        <h2 className="text-xl font-semibold text-white mb-4">File Summary</h2>
        <div className="bg-gray-800 rounded-lg p-4 text-gray-300">
          <div className="flex items-start space-x-3">
            <FileText size={24} />
            <div>
              <h3 className="font-medium text-white">{file.name}</h3>
              <p className="text-sm text-gray-400 mt-1">Size: {file.size}</p>
              <p className="text-sm text-gray-400">Downloaded: {file.downloadDate}</p>
              <p className="text-sm text-gray-400">Current Location: {file.currentPath}</p>
              <p className="mt-2">{file.summary}</p>
            </div>
          </div>
        </div>
      </div>

      <h2 className="text-xl font-semibold text-white mb-4">Top Suggestions</h2>
      <div className="space-y-4">
        {suggestions.map((suggestedPath: string, index) => (
          <div key={index} className="bg-gray-800 rounded-lg p-4 text-gray-300">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-medium text-white mb-2">
                  {index + 1}. {suggestedPath}
                </h3>
                {/* <p className="text-sm text-gray-400 mb-2">Confidence: {suggestion.confidence}%</p>
                <p>{suggestion.reason}</p> */}
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => onAccept(suggestedPath, file.currentPath, file.id)}
                  className="p-2 rounded-full hover:bg-gray-700 text-green-500"
                  title="Accept"
                >
                  <CheckCircle size={24} />
                </button>
                <button
                  onClick={() => onReject(suggestedPath)}
                  className="p-2 rounded-full hover:bg-gray-700 text-red-500"
                  title="Reject"
                >
                  <XCircle size={24} />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const SuggestionsList = ({ files, onSelectFile, onDeleteSuggestion }: any) => {
  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold text-white mb-4">Recent File Suggestions</h2>
      <div className="space-y-4">
        {files.map((file: any, index: number) => (
          <div 
            key={index} 
            className="relative bg-gray-800 rounded-lg p-4 text-gray-300 hover:bg-gray-700 transition-colors duration-200"
          >
            <button
              onClick={() => {
                onSelectFile(file)
              }}
              className="w-full text-left flex items-start space-x-3"
            >
              <FileText size={24} />
              <div>
                <h3 className="font-medium text-white mb-1">{file.name}</h3>
                <p className="text-sm text-gray-400">Downloaded: {file.downloadDate}</p>
                <p className="text-sm text-gray-400">Current Location: {file.currentPath}</p>
                <p className="text-sm text-blue-400 mt-2">
                  {file.suggestions.length} suggestions available
                </p>
              </div>
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation(); // Prevent selecting the file when clicking delete
                onDeleteSuggestion(file.id);
              }}
              className="absolute top-4 right-4 text-gray-400 hover:text-red-500 transition-colors"
              title="Remove Suggestion"
            >
              <X size={20} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

const SuggestionsView = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  async function fetchSuggestions() {
    const suggestions = await window.electron.getSuggestions();
    // Update the suggestions
    setSuggestions(suggestions);
  }

  useEffect(() => {
    fetchSuggestions();
  }, []);

  const files = suggestions?.map((suggestion: any) => ({
    id: suggestion.id,
    name: suggestion.name,
    size: `${(suggestion.size / (1024 * 1024)).toFixed(2)} MB`,
    downloadDate: suggestion.downloadDate,
    currentPath: suggestion.currentPath,
    summary: suggestion.summary,
    suggestions: suggestion.suggestions
  }));

  const sendCommitRequest =  async (source_path: string, destination_path: string) => {
    const data: CommitSuggestionRequest = {src_path: source_path, dst_path: destination_path};

    const config: AxiosRequestConfig = {
      headers: {
        'Content-Type': 'application/json',
      },
  };
  try {
    const response = await axios.post('http://0.0.0.0:8000/commit-suggestion', data, config);
    return response.data;
  } catch (error) {
    alert('Error Occured: '+ error)
    console.error('Error occurred:', error);
  }
  return null;
}


  const handleAccept = async (suggestedPath: string, currentPath: string, id: number) => {
    // console.log('Accepted suggestion:', suggestedPath);
    const response = await sendCommitRequest(currentPath, suggestedPath);
    await window.electron.deleteSuggestion(id);
    fetchSuggestions();
    setSelectedFile(null); // Return to list view after accepting
  };

  const handleReject = (suggestion: string) => {
    // console.log('Rejected suggestion:', suggestion);
    // Implement your rejection logic here
  };

  const handleDeleteSuggestion = async (id: number) => {
    await window.electron.deleteSuggestion(id);
    fetchSuggestions();
  };

  return selectedFile ? (
    <SuggestionDetail
      file={selectedFile}
      suggestions={selectedFile?selectedFile?.suggestions:[]}
      onBack={() => setSelectedFile(null)}
      onAccept={handleAccept}
      onReject={handleReject}
    />
  ) : (
    <SuggestionsList
      files={files}
      onSelectFile={setSelectedFile}
      onDeleteSuggestion={handleDeleteSuggestion}
    />
  );
};

export default SuggestionsView;