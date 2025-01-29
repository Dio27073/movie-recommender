import { useState, useEffect, useCallback, useMemo } from 'react';
import apiService from '../../services/api';
import { Movie, Rating, FilterParams } from './types';

interface PaginationData {
  total: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

// Generic debounce hook for any value
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

// Main movies fetching hook
export const useMovies = (page: number = 1, filters: FilterParams) => {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState<PaginationData>({
    total: 0,
    totalPages: 0,
    hasNext: false,
    hasPrev: false
  });

  const params = useMemo(() => {
    const urlParams = new URLSearchParams({
      page: page.toString(),
      per_page: '12',
    });

    if (filters.genres?.size) {
      Array.from(filters.genres).forEach(genre => {
        urlParams.append('genres', genre);
      });
    }
    
    if (filters.castCrew?.size) {
      Array.from(filters.castCrew).forEach(person => {
        console.log('Adding cast/crew filter:', person);
        urlParams.append('cast_crew', person);
      });
    }
    
    if (filters.yearRange) {
      urlParams.append('min_year', filters.yearRange[0].toString());
      urlParams.append('max_year', filters.yearRange[1].toString());
    }
    
    if (filters.ratingRange) {
      urlParams.append('min_rating', filters.ratingRange[0].toString());
      urlParams.append('max_rating', filters.ratingRange[1].toString());
    }

    if (filters.sort) {
      urlParams.append('sort', filters.sort);
    }

    if (filters.searchQuery?.trim()) {
      urlParams.append('search', filters.searchQuery);
      if (filters.searchType) {
        urlParams.append('search_type', filters.searchType);
      }
    }
    console.log('Final URL params:', urlParams.toString());

    return urlParams;
  }, [
    page, 
    filters.genres, 
    filters.yearRange, 
    filters.ratingRange, 
    filters.sort, 
    filters.castCrew,
    filters.searchQuery,
    filters.searchType
  ]);

  const fetchMovies = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const url = `http://localhost:8000/movies/?${params}`;
      console.log('Fetching movies with URL:', url); // Add this log
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch movies: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('API Response:', data); // Add this log
      
      setMovies(data.items);
      setPagination({
        total: data.total,
        totalPages: data.total_pages,
        hasNext: data.has_next,
        hasPrev: data.has_prev
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch movies';
      setError(errorMessage);
      setMovies([]);
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    fetchMovies();
  }, [fetchMovies]);

  return { movies, loading, error, pagination };
};

// Movie search hook
export const useMovieSearch = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<Movie[]>([]);
  const [searchPagination, setSearchPagination] = useState<PaginationData>({
    total: 0,
    totalPages: 0,
    hasNext: false,
    hasPrev: false
  });

  const searchMovies = useCallback(async (query: string, page: number = 1) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `http://localhost:8000/movies/search/?query=${encodeURIComponent(query)}&page=${page}`
      );
      
      if (!response.ok) {
        throw new Error(`Failed to search movies: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      setSearchResults(data.items);
      setSearchPagination({
        total: data.total,
        totalPages: data.total_pages,
        hasNext: data.has_next,
        hasPrev: data.has_prev
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to search movies';
      setError(errorMessage);
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  return { searchMovies, searchResults, loading, error, searchPagination };
};

// Movie rating hook
export const useRateMovie = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const rateMovie = useCallback(async (rating: Rating) => {
    setLoading(true);
    setError(null);

    try {
      await apiService.rateMovie(rating);
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to rate movie';
      setError(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  return { rateMovie, loading, error };
};