import { useState, useEffect } from 'react';
import apiService from '../../services/api';
import { Movie, Rating } from './types';

export const useMovies = (initialSkip = 0, initialLimit = 100) => {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMovies = async () => {
      try {
        setLoading(true);
        const data = await apiService.getMovies(initialSkip, initialLimit);
        setMovies(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch movies');
      } finally {
        setLoading(false);
      }
    };

    fetchMovies();
  }, [initialSkip, initialLimit]);

  return { movies, loading, error };
};

export const useRateMovie = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const rateMovie = async (rating: Rating) => {
    try {
      setLoading(true);
      await apiService.rateMovie(rating);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to rate movie');
      return false;
    } finally {
      setLoading(false);
    }
  };

  return { rateMovie, loading, error };
};