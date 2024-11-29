import React, { useEffect, useState } from 'react';
import { FolderTree, Bell, Settings, CheckCircle, XCircle, ArrowLeft, FileText } from 'lucide-react';

const SuggestionDetail = ({ file, suggestions, onBack, onAccept, onReject }: any) => {
  useEffect(() => {
    window.electron.subscribeSuggestions((suggestion: any) => {
      console.log('Received suggestion:', suggestion);
      // Update the suggestions
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
                  onClick={() => onAccept(suggestedPath)}
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

const SuggestionsList = ({ files, onSelectFile }: any) => {
  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold text-white mb-4">Recent File Suggestions</h2>
      <div className="space-y-4">
        {files.map((file: any, index: number) => (
          <button
            key={index}
            onClick={() => onSelectFile(file)}
            className="w-full text-left bg-gray-800 rounded-lg p-4 text-gray-300 hover:bg-gray-700 transition-colors duration-200"
          >
            <div className="flex items-start space-x-3">
              <FileText size={24} />
              <div>
                <h3 className="font-medium text-white mb-1">{file.name}</h3>
                <p className="text-sm text-gray-400">Downloaded: {file.downloadDate}</p>
                <p className="text-sm text-gray-400">Current Location: {file.currentPath}</p>
                <p className="text-sm text-blue-400 mt-2">
                  {file.suggestions.length} suggestions available
                </p>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

const SuggestionsView = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  useEffect(() => {
    async function fetchSuggestions() {
      const suggestions = await window.electron.getSuggestions();
      console.log('Fetched suggestions:', suggestions);
      // Update the suggestions
      setSuggestions(suggestions);
    }
    fetchSuggestions();
  }, []);

  const files = suggestions?.map((suggestion: any) => ({
    name: suggestion.name,
    size: `${(suggestion.size / (1024 * 1024)).toFixed(2)} MB`,
    downloadDate: suggestion.downloadDate,
    currentPath: suggestion.currentPath,
    summary: suggestion.summary,
    suggestions: suggestion.suggestions
  }));

  const handleAccept = (suggestion: string) => {
    console.log('Accepted suggestion:', suggestion);
    // Implement your file moving logic here
    setSelectedFile(null); // Return to list view after accepting
  };

  const handleReject = (suggestion: string) => {
    console.log('Rejected suggestion:', suggestion);
    // Implement your rejection logic here
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
    />
  );
};

export default SuggestionsView;