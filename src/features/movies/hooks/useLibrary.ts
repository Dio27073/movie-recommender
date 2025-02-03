import { useState, useEffect } from 'react';
import api from '../../../services/api';
import { LibraryMovie } from '../types';

interface LibraryData {
  viewed_movies: LibraryMovie[];
  rated_movies: LibraryMovie[];
}

export const useLibrary = () => {
  const [libraryData, setLibraryData] = useState<LibraryData>({ 
    viewed_movies: [], 
    rated_movies: [] 
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLibrary = async () => {
    try {
      setIsLoading(true);
      const response = await api.getUserLibrary();
      setLibraryData({
        viewed_movies: response.viewed_movies,
        rated_movies: response.rated_movies
      });
      setError(null);
    } catch (error) {
      console.error('Error fetching library:', error);
      setError('Failed to fetch library');
    } finally {
      setIsLoading(false);
    }
  };

  const addToLibrary = async (movieId: number) => {
    try {
      await api.addToLibrary(movieId);
      await fetchLibrary(); // Refresh the library after adding
    } catch (error) {
      console.error('Error adding to library:', error);
      throw error;
    }
  };

  const removeFromLibrary = async (movieId: number) => {
    try {
      await api.removeFromLibrary(movieId);
      await fetchLibrary(); // Refresh the library after removing
    } catch (error) {
      console.error('Error removing from library:', error);
      throw error;
    }
  };

  useEffect(() => {
    fetchLibrary();
  }, []);

  return {
    watchedMovies: libraryData.viewed_movies,
    ratedMovies: libraryData.rated_movies,
    isLoading,
    error,
    addToLibrary,
    removeFromLibrary,
    refreshLibrary: fetchLibrary
  };
};