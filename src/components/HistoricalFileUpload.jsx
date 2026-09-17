import React, { useState } from 'react';

const HistoricalFileUpload = () => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setSelectedFiles(Array.from(e.target.files));
    setError(null);
    setUploadResult(null);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (selectedFiles.length === 0) {
      setError('Please select at least one file');
      return;
    }

    setUploading(true);
    setError(null);
    setUploadResult(null);

    try {
      const formData = new FormData();
      selectedFiles.forEach(file => {
        formData.append('files', file);
      });

      const response = await fetch('/api/upload-historical', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const result = await response.json();
      setUploadResult(result);
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
          <span className="text-primary">Uploading...</span>
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
            Drag & drop your historical Excel files here, or
            <span className="font-medium text-primary cursor-pointer">
              Browse Files
            </span>
          </p>
          <p className="text-xs text-gray-500">
            Upload multiple .xlsx files to train the shift prediction model
          </p>
        </div>
        <input
          type="file"
          multiple
          accept=".xlsx"
          onChange={handleFileChange}
          className="hidden"
        />
        <button
          onClick={() => document.querySelector('input[type="file"]').click()}
          disabled={uploading}
          className="mt-4 flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
        >
          Select Files
        </button>
      </div>

      {selectedFiles.length > 0 && (
        <div className="border rounded-lg p-4">
          <h3 className="font-medium text-gray-900">Selected Files ({selectedFiles.length})</h3>
          <ul className="mt-2 space-y-1 text-sm text-gray-600">
            {selectedFiles.map((file, index) => (
              <li key={index} className="flex items-center">
                <svg className="h-4 w-4 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 0l6-6m-6 6l6-6"></path>
                </svg>
                <span>{file.name}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={uploading || selectedFiles.length === 0}
        className="w-full flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {uploading ? 'Uploading...' : 'Upload Historical Files'}
      </button>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <p>{error}</p>
        </div>
      )}

      {uploadResult && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
          <h3 className="font-medium">Upload Successful!</h3>
          <p className="mt-2">
            Processed {uploadResult.total_records_added} records from {uploadResult.files.length} file(s)
          </p>
          <ul className="mt-2 space-y-1 text-xs">
            {uploadResult.files.map((file, index) => (
              <li key={index}>
                {file.filename}: {file.records_count} records (week offset: {file.week_offset})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default HistoricalFileUpload;