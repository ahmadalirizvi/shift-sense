import React, { useState } from 'react';

const PredictionUpload = ({ onPredictionComplete, predictionData }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [predictionResult, setPredictionResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0] || null);
    setError(null);
    setPredictionResult(null);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError(null);
    setPredictionResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch('/api/predict', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Prediction failed');
      }

      const result = await response.json();
      setPredictionResult(result);
      // Call the callback function to notify parent component
      if (onPredictionComplete) {
        onPredictionComplete(result);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  if (uploading) {
    return (
      <div className="text-center py-4">
        <div className="flex items-center justify-center space-x-2">
          <div className="animate-spin rounded-full border-2 border-primary border-t-transparent h-8 w-8"></div>
          <span className="text-primary">Generating predictions...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
        <div className="space-y-3">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16h4v2m0 0l-2-2m2 2l2-2m0 0l2-2m-2 2l-2-2m0 0l2 2m0-4l2-2m-2 2l-2-2m0 0l2-2m-2 2l-2-2"></path>
          </svg>
          <p className="text-gray-600">
            Drag & drop your blank week Excel file here, or
            <span className="font-medium text-primary cursor-pointer">
              Browse File
            </span>
          </p>
          <p className="text-xs text-gray-500">
            Upload a .xlsx file with blank shift schedule to get AI-powered predictions
          </p>
        </div>
        <input
          type="file"
          accept=".xlsx"
          onChange={handleFileChange}
          className="hidden"
        />
        <button
          onClick={() => document.querySelector('input[type="file"]').click()}
          disabled={uploading}
          className="mt-4 flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
        >
          Select File
        </button>
      </div>

      {selectedFile && (
        <div className="border rounded-lg p-4">
          <h3 className="font-medium text-gray-900">Selected File</h3>
          <div className="mt-2 flex items-center text-sm text-gray-600">
            <svg className="h-4 w-4 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 0l6-6m-6 6l6-6"></path>
            </svg>
            <span>{selectedFile.name}</span>
          </div>
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={uploading || !selectedFile}
        className="w-full flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {uploading ? 'Generating...' : 'Get Predictions'}
      </button>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <p>{error}</p>
        </div>
      )}

      {predictionResult && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <h3 className="font-medium mb-4">Predictions Generated!</h3>
          <div className="grid grid-cols-1 gap-4">
            <div className="bg-white rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-2">Summary</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Total Shifts</p>
                  <p className="font-bold text-gray-900">{predictionResult.summary.total_shifts}</p>
                </div>
                <div>
                  <p className="text-gray-500">Confident Predictions</p>
                  <p className="font-bold text-green-600">{predictionResult.summary.confident_predictions}</p>
                </div>
                <div>
                  <p className="text-gray-500">Flagged for Review</p>
                  <p className="font-bold text-yellow-600">{predictionResult.summary.flagged_for_review}</p>
                </div>
                <div>
                  <p className="text-gray-500">Conflicts Resolved</p>
                  <p className="font-bold text-blue-600">{predictionResult.summary.conflicts_resolved}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-2">Download Results</h4>
              <p className="text-gray-600 mb-4">
                Download the Excel file with predictions and color-coding:
              </p>
              <a
                href={`/api/download/${predictionResult.predictions[0]?.assigned_person ? 'predictions_' : ''}${Date.now()}.xlsx`}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
              >
                Download Excel Report
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PredictionUpload;