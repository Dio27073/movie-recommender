import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Star, ArrowLeft } from 'lucide-react';
import { Movie } from '../../features/movies/types';
import apiService from '../../services/api';

export const MovieDetails: React.FC = () => {
  // In Electron, we'll use location state to pass movie data
  const location = useLocation();
  const navigate = useNavigate();
  const movie = location.state?.movie as Movie;
  const [loading, setLoading] = useState(!movie);
  const [error, setError] = useState<string | null>(null);
  const [movieData, setMovieData] = useState<Movie | null>(movie || null);

  useEffect(() => {
    // Only fetch if we don't have the movie data from navigation state
    if (!movie) {
      const fetchMovie = async () => {
        try {
          setLoading(true);
          // Get movie ID from the location pathname
          const id = location.pathname.split('/').pop();
          const response = await apiService.getMovie(id!);
          setMovieData(response);
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Failed to fetch movie details');
        } finally {
          setLoading(false);
        }
      };

      fetchMovie();
    }
  }, [movie, location.pathname]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="bg-red-50 text-red-800 p-4 rounded-lg">
          Error: {error}
        </div>
        <button 
          onClick={() => navigate(-1)}
          className="mt-4 inline-flex items-center text-blue-600 hover:text-blue-800"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Movies
        </button>
      </div>
    );
  }

  if (!movieData) return null;

  return (
    <div className="p-6 bg-gray-100 dark:bg-dark-primary min-h-screen">
      <button 
        onClick={() => navigate(-1)}
        className="mb-6 inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Movies
      </button>
      
      <div className="bg-white dark:bg-dark-secondary rounded-xl shadow-lg overflow-hidden">
        <div className="md:flex">
          <div className="md:flex-shrink-0">
            <img
              src={movieData.imageUrl || '/api/placeholder/400/600'}
              alt={movieData.title}
              className="h-96 w-full object-cover md:w-96"
            />
          </div>
          
          <div className="p-8">
            <div className="flex items-center justify-between">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                {movieData.title}
              </h1>
              <div className="flex items-center">
                <Star className="w-6 h-6 text-yellow-400 fill-current" />
                <span className="ml-2 text-lg font-semibold dark:text-gray-200">
                  {movieData.average_rating.toFixed(1)}
                </span>
              </div>
            </div>
            
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Released: {movieData.release_year}
            </p>
            
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              {movieData.description}
            </p>
            
            <div className="mt-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Genres
              </h2>
              <div className="flex flex-wrap gap-2">
                {(Array.isArray(movieData.genres) ? movieData.genres : [movieData.genres]).map((genre) => (
                  <span
                    key={genre}
                    className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full text-sm"
                  >
                    {genre}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MovieDetails;