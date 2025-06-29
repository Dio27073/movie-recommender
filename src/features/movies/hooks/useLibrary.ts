import { useState, useEffect } from 'react';
import api from '../../../services/api';
import { LibraryMovie } from '../types';

export const useLibrary = () => {
  const [libraryMovies, setLibraryMovies] = useState<LibraryMovie[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLibrary = async () => {
    try {
      setIsLoading(true);
      const response = await api.getUserLibrary();
      // The API returns LibraryMovie[] directly
      setLibraryMovies(response);
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

  // Split movies into watched and rated based on their properties
  const watchedMovies = libraryMovies.filter(movie => movie.watched_at);
  const ratedMovies = libraryMovies.filter(movie => movie.rating !== undefined && movie.rating !== null);

  return {
    watchedMovies,
    ratedMovies,
    allMovies: libraryMovies,
    isLoading,
    error,
    addToLibrary,
    removeFromLibrary,
    refreshLibrary: fetchLibrary
  };
};