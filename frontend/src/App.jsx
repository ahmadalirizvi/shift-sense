import React from 'react';

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            Shift Sense
          </h1>
          <p className="mt-2 text-gray-600">
            AI-Powered Shift Allocation System
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">
            Welcome to Shift Sense
          </h2>
          <p className="text-gray-700">
            The backend API is running on <code className="bg-gray-100 px-1 rounded">http://localhost:8000</code>
          </p>
          <p className="mt-4 text-gray-600">
            Frontend is running on <code className="bg-gray-100 px-1 rounded">http://localhost:3000</code>
          </p>
        </div>
      </main>
    </div>
  );
}

export default App;