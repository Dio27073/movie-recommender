import { useState } from 'react';

interface CleanupResponse {
  status: string;
  duplicates_found: number;
  movies_removed: number;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:10000';

const CleanupButton = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CleanupResponse | null>(null);

  const cleanupDuplicates = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_URL}/admin/cleanup-duplicates`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error('Failed to cleanup duplicates');
      }

      const data: CleanupResponse = await response.json();
      setResult(data);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-36 right-4 z-50 flex flex-col gap-2">
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative w-72">
          <strong className="font-bold">Error!</strong>
          <div className="mt-1">{error}</div>
        </div>
      )}
      
      {result && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative w-72">
          <strong className="font-bold">Success!</strong>
          <div className="mt-1">
            <p>Duplicates found: {result.duplicates_found}</p>
            <p>Movies removed: {result.movies_removed}</p>
          </div>
        </div>
      )}

      <button 
        onClick={cleanupDuplicates} 
        disabled={loading}
        className={`w-72 bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded
          ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        {loading ? (
          <div className="flex items-center justify-center">
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Cleaning up duplicates...
          </div>
        ) : (
          'Clean Up Duplicates'
        )}
      </button>
    </div>
  );
};

export default CleanupButton;