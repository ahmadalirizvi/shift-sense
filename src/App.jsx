import React, { useState } from 'react';
import HistoricalFileUpload from './components/HistoricalFileUpload';
import PredictionUpload from './components/PredictionUpload';
import PredictionDisplay from './components/PredictionDisplay';

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [predictionData, setPredictionData] = useState(null);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col items-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Shift Sense
            </h1>
            <p className="text-gray-600">
              AI-Powered Shift Allocation System
            </p>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-md">
          <nav className="flex items-center px-4 pt-5 border-b border-gray-200">
            <button
              onClick={() => setActiveTab('upload')}
              className={`${activeTab === 'upload'
                ? 'border-b-2 border-primary text-primary'
                : 'text-gray-500 hover:text-gray-700'
              } px-3 py-2 text-sm font-medium`
            >
              Upload & Predict
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`${activeTab === 'history'
                ? 'border-b-2 border-primary text-primary'
                : 'text-gray-500 hover:text-gray-700'
              } px-3 py-2 text-sm font-medium ml-4`
            >
              Data History
            </button>
          </nav>

          <div className="px-6 pt-4">
            {activeTab === 'upload' && (
              <>
                <HistoricalFileUpload />
                <div className="mt-8">
                  <PredictionUpload
                    onPredictionComplete={setPredictionData}
                  predictionData={predictionData}
                  onClear={() => setPredictionData(null)}
                  />
                </div>
                {predictionData && (
                  <div className="mt-8">
                    <PredictionDisplay predictions={predictionData.predictions} />
                  </div>
                )}
              </>
            )}

            {activeTab === 'history' && (
              <div className="text-center py-12">
                <h3 className="text-xl font-bold text-gray-900 mb-4">
                  Data History & Analytics
                </h3>
                <p className="text-gray-600">
                  View historical data patterns and model performance metrics
                </p>
                <div className="mt-8 bg-gray-50 rounded-lg p-6">
                  <p className="text-gray-500">
                    Feature coming soon: View uploaded datasets, training progress,
                    and model accuracy metrics
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 text-center text-gray-600">
          <p className="text-sm">
            Shift Sense &copy; {new Date().getFullYear()} - Powered by AI
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;