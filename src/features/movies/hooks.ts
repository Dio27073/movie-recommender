import { useState, useEffect, useCallback, useMemo } from 'react';
import apiService from '../../services/api';
import { Movie, Rating, FilterParams } from './types';

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
}

export const useMovies = (page: number = 1, filters: FilterParams) => {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    total: 0,
    totalPages: 0,
    hasNext: false,
    hasPrev: false
  });

  // Memoize the URL parameters
  // In useMovies hook, update the params useMemo
  const params = useMemo(() => {
    const urlParams = new URLSearchParams({
      page: page.toString(),
      per_page: '10',
    });

    if (filters.genres?.size) {
      urlParams.append('genres', Array.from(filters.genres).join(','));
    }
    
    if (filters.yearRange) {
      urlParams.append('min_year', filters.yearRange[0].toString());
      urlParams.append('max_year', filters.yearRange[1].toString());
    }
    
    if (filters.minRating !== undefined) {
      urlParams.append('min_rating', filters.minRating.toString());
    }

    if (filters.sort) {
      urlParams.append('sort', filters.sort);
    }
    
    return urlParams;
  }, [page, filters.genres, filters.yearRange, filters.minRating, filters.sort]);

  // Memoize the fetch function
  const fetchMovies = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/movies/?${params}`);
      const data = await response.json();
      
      setMovies(data.items);
      setPagination({
        total: data.total,
        totalPages: data.total_pages,
        hasNext: data.has_next,
        hasPrev: data.has_prev
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch movies');
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    fetchMovies();
  }, [fetchMovies]);

  return { movies, loading, error, pagination };
};

export const useRateMovie = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const rateMovie = useCallback(async (rating: Rating) => {
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
  }, []);

  return { rateMovie, loading, error };
};