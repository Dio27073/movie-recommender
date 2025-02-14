import { useState } from 'react';

interface LoadMoviesResponse {
  status: string;
  processed: number;
  skipped: number;
  start_page: number;
  end_page: number;
  next_page: number;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:10000';

const MovieLoaderButton = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LoadMoviesResponse | null>(null);
  const [startPage, setStartPage] = useState(1);

  const loadMoreMovies = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_URL}/admin/load-more-movies`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start_page: startPage,
          num_pages: 50
        })
      });

      if (!response.ok) {
        throw new Error('Failed to load movies');
      }

      const data: LoadMoviesResponse = await response.json();
      setResult(data);
      setStartPage(data.next_page);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative w-72">
          <strong className="font-bold">Error!</strong>
          <div className="mt-1">{error}</div>
        </div>
      )}
      
      {result && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative w-72">
          <strong className="font-bold">Success!</strong>
          <div className="mt-1">Added {result.processed} new movies</div>
        </div>
      )}

      <button 
        onClick={loadMoreMovies} 
        disabled={loading}
        className={`w-72 bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded
          ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        {loading ? (
          <div className="flex items-center justify-center">
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Loading Movies...
          </div>
        ) : (
          'Load More Movies'
        )}
      </button>
    </div>
  );
};

export default MovieLoaderButton;