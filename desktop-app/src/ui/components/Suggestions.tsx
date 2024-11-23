import React, { useState } from 'react';
import { FolderTree, Bell, Settings, CheckCircle, XCircle, ArrowLeft, FileText } from 'lucide-react';

const SuggestionDetail = ({ file, suggestions, onBack, onAccept, onReject }: any) => {
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
        {suggestions.map((suggestion, index) => (
          <div key={index} className="bg-gray-800 rounded-lg p-4 text-gray-300">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-medium text-white mb-2">
                  Suggestion {index + 1}: {suggestion.path}
                </h3>
                <p className="text-sm text-gray-400 mb-2">Confidence: {suggestion.confidence}%</p>
                <p>{suggestion.reason}</p>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => onAccept(suggestion)}
                  className="p-2 rounded-full hover:bg-gray-700 text-green-500"
                  title="Accept"
                >
                  <CheckCircle size={24} />
                </button>
                <button
                  onClick={() => onReject(suggestion)}
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

  // Example data - replace with your actual data
  const files = [
    {
      name: "quarterly_report.pdf",
      size: "2.4 MB",
      downloadDate: "2024-11-23 14:30",
      currentPath: "/downloads/quarterly_report.pdf",
      summary: "Quarterly financial report containing revenue analysis and forecasts",
      suggestions: [
        {
          path: "/Documents/Financial/Reports/2024/Q4",
          confidence: 95,
          reason: "Similar quarterly reports are stored in this location"
        },
        {
          path: "/Documents/Work/Finance",
          confidence: 85,
          reason: "Contains other financial documents"
        },
        {
          path: "/Documents/Reports",
          confidence: 75,
          reason: "General reports directory"
        }
      ]
    },
    {
      name: "project_proposal.docx",
      size: "1.1 MB",
      downloadDate: "2024-11-23 15:45",
      currentPath: "/downloads/project_proposal.docx",
      summary: "Project proposal document for new client initiative",
      suggestions: [
        {
          path: "/Documents/Projects/Proposals",
          confidence: 90,
          reason: "Contains other project proposals"
        },
        {
          path: "/Documents/Work/2024",
          confidence: 80,
          reason: "Contains current year work documents"
        },
        {
          path: "/Documents/Client_Projects",
          confidence: 70,
          reason: "Contains other client-related documents"
        }
      ]
    }
  ];

  const handleAccept = (suggestion: any) => {
    console.log('Accepted suggestion:', suggestion);
    // Implement your file moving logic here
    setSelectedFile(null); // Return to list view after accepting
  };

  const handleReject = (suggestion: any) => {
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