import React, { useState, useEffect } from 'react';
import { FolderTree, Bell, Settings, AlertCircle } from 'lucide-react';
import FileOrganizer from './FileOrganizer';
import SettingsView from './SettingsView';
import SuggestionsView from './Suggestions';

const Sidebar = () => {
  const [activeView, setActiveView] = useState('files');
  const [notifications] = useState(3);
  const [isDarkMode, setIsDarkMode] = useState(() => {
  const savedMode = localStorage.getItem('darkMode');
    return savedMode !== null ? JSON.parse(savedMode) : true;
  });
  
  // Directory settings state
  const [watchDir, setWatchDir] = useState(() => {
    return localStorage.getItem('watchDirectory') || '';
  });
  const [targetDir, setTargetDir] = useState(() => {
    return localStorage.getItem('targetDirectory') || '';
  });
  const [isWatchMode, setIsWatchMode] = useState(() => {
    return localStorage.getItem('watchMode') === 'true';
  });
  const [validationError, setValidationError] = useState('');

  // Save settings to localStorage
  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(isDarkMode));
    localStorage.setItem('watchDirectory', watchDir);
    localStorage.setItem('targetDirectory', targetDir);
    localStorage.setItem('watchMode', isWatchMode.toString());
    
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode, watchDir, targetDir, isWatchMode]);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  const toggleWatchMode = () => {
    if (!watchDir || !targetDir) {
      setValidationError('Both Watch and Target directories must be set before enabling Watch Mode');
      setIsWatchMode(false);
      return;
    }
    setValidationError('');
    setIsWatchMode(!isWatchMode);
  };

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="w-16 bg-gray-800 flex flex-col items-center py-4 border-r border-gray-700">
        <div className="space-y-4">
          <button
            onClick={() => setActiveView('files')}
            className={`p-3 rounded-lg hover:bg-gray-700 transition-colors relative ${
              activeView === 'files' ? 'bg-gray-700' : ''
            }`}
            title="Files"
          >
            <FolderTree
              size={24}
              className={`${
                activeView === 'files' ? 'text-white' : 'text-gray-400'
              }`}
            />
            {activeView === 'files' && (
              <div className="absolute left-0 top-0 w-0.5 h-full bg-blue-500"></div>
            )}
          </button>

          <button
            onClick={() => setActiveView('suggestions')}
            className={`p-3 rounded-lg hover:bg-gray-700 transition-colors relative ${
              activeView === 'suggestions' ? 'bg-gray-700' : ''
            }`}
            title="Suggestions"
          >
            <div className="relative">
              <Bell
                size={24}
                className={`${
                  activeView === 'suggestions' ? 'text-white' : 'text-gray-400'
                }`}
              />
              {notifications > 0 && (
                <div className="absolute -top-2 -right-2 bg-blue-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                  {notifications}
                </div>
              )}
            </div>
            {activeView === 'suggestions' && (
              <div className="absolute left-0 top-0 w-0.5 h-full bg-blue-500"></div>
            )}
          </button>

          <button
            onClick={() => setActiveView('settings')}
            className={`p-3 rounded-lg hover:bg-gray-700 transition-colors relative ${
              activeView === 'settings' ? 'bg-gray-700' : ''
            }`}
            title="Settings"
          >
            <Settings
              size={24}
              className={`${
                activeView === 'settings' ? 'text-white' : 'text-gray-400'
              }`}
            />
            {activeView === 'settings' && (
              <div className="absolute left-0 top-0 w-0.5 h-full bg-blue-500"></div>
            )}
          </button>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 bg-gray-900">
        {activeView === 'files' && (
            <FileOrganizer />
        )}
        
        {activeView === 'suggestions' && (
            <SuggestionsView />
        )}

        {activeView === 'settings' && 
        (
            <SettingsView 
                watchDir={watchDir}
                setWatchDir={setWatchDir}
                targetDir={targetDir}
                setTargetDir={setTargetDir}
                isWatchMode={isWatchMode}
                toggleWatchMode={toggleWatchMode}
                validationError={validationError}
                isDarkMode={isDarkMode}
                toggleDarkMode={toggleDarkMode}
            />
        )}
      </div>
    </div>
  );
};

export default Sidebar;