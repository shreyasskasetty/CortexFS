import React from 'react'
import { AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from "./ui/alert";
export default function SettingsView({ isDarkMode, toggleDarkMode, watchDir, 
                                    setWatchDir, targetDir, setTargetDir, isWatchMode, 
                                    toggleWatchMode, validationError }: any) {
  return (
        <div className="p-6 space-y-6">
        {/* General Settings Section */}
        <div>
        <h2 className="text-xl font-semibold text-white dark:text-white mb-4">General Settings</h2>
        <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 text-gray-700 dark:text-gray-300">
            <div className="space-y-4">
            <div className="flex items-center justify-between">
                <span>Dark Mode</span>
                <button
                onClick={toggleDarkMode}
                className={`w-12 h-6 rounded-full relative transition-colors duration-200 ${
                    isDarkMode ? 'bg-blue-500' : 'bg-gray-400'
                }`}
                >
                <div
                    className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform duration-200 ${
                    isDarkMode ? 'right-1' : 'left-1'
                    }`}
                ></div>
                </button>
            </div>
            </div>
        </div>
        </div>

        {/* File Organization Settings Section */}
        <div>
        <h2 className="text-xl font-semibold text-white dark:text-white mb-4">File Organization Settings</h2>
        <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 text-gray-700 dark:text-gray-300 space-y-4">
            {validationError && (
            <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                {validationError}
                </AlertDescription>
            </Alert>
            )}
            
            <div className="space-y-4">
            <div className="flex flex-col space-y-2">
                <label htmlFor="watchDir">Watch Directory</label>
                <input
                id="watchDir"
                type="text"
                value={watchDir}
                onChange={(e) => setWatchDir(e.target.value)}
                placeholder="/path/to/watch/directory"
                className="w-full px-3 py-2 rounded-md bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600"
                />
            </div>

            <div className="flex flex-col space-y-2">
                <label htmlFor="targetDir">Target Directory</label>
                <input
                id="targetDir"
                type="text"
                value={targetDir}
                onChange={(e) => setTargetDir(e.target.value)}
                placeholder="/path/to/target/directory"
                className="w-full px-3 py-2 rounded-md bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600"
                />
            </div>

            <div className="flex items-center justify-between">
                <span>Watch Mode</span>
                <button
                onClick={toggleWatchMode}
                className={`w-12 h-6 rounded-full relative transition-colors duration-200 ${
                    isWatchMode ? 'bg-blue-500' : 'bg-gray-400'
                }`}
                >
                <div
                    className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform duration-200 ${
                    isWatchMode ? 'right-1' : 'left-1'
                    }`}
                ></div>
                </button>
            </div>
            </div>
        </div>
        </div>
    </div>
  )
}
