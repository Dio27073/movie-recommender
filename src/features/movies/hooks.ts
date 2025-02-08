import { useState, useEffect, useCallback, useMemo } from 'react';
import apiService from '../../services/api';
import { Movie, Rating, FilterParams } from './types';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { recommendationService, RecommendationFilters } from '../../services/recommendationService';

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

    if (filters.genre?.size) {
      Array.from(filters.genre).forEach(genre => {
        urlParams.append('genres', genre);
      });
    }
    
    if (filters.castCrew?.size) {
      Array.from(filters.castCrew).forEach(person => {
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

    if (filters.contentRating?.size) {
      Array.from(filters.contentRating).forEach(rating => {
        urlParams.append('content_rating', rating);
      });
    }

    if (filters.moodTags?.size) {
      Array.from(filters.moodTags).forEach(mood => {
        urlParams.append('mood_tags', mood);
      });
    }

    if (filters.streamingPlatforms?.size) {
      Array.from(filters.streamingPlatforms).forEach(platform => {
        urlParams.append('streaming_platforms', platform);
      });
    }

    return urlParams;
  }, [
    page, 
    filters.genre, 
    filters.yearRange, 
    filters.ratingRange, 
    filters.sort, 
    filters.castCrew,
    filters.searchQuery,
    filters.searchType,
    filters.contentRating,
    filters.moodTags,
    filters.streamingPlatforms
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


export const useAllGenres = () => {
  const [genres, setGenres] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchGenres = async () => {
      try {
        const response = await fetch('/api/genres'); // Adjust the endpoint as needed
        if (!response.ok) throw new Error('Failed to fetch genres');
        const data = await response.json();
        setGenres(data);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to fetch genres'));
      } finally {
        setIsLoading(false);
      }
    };

    fetchGenres();
  }, []);

  return { genres, isLoading, error };
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

export const useMovieRecommendations = (filters: RecommendationFilters = {}) => {
  return useQuery({
    queryKey: ['recommendations', filters],
    queryFn: () => recommendationService.getRecommendations(filters),
    placeholderData: (previousData) => previousData, // Replace keepPreviousData with placeholderData
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
  });
};

// Hook for getting similar movies
export const useSimilarMovies = (movieId: number) => {
  return useQuery({
    queryKey: ['similar-movies', movieId],
    queryFn: () => recommendationService.getSimilarMovies(movieId),
    enabled: !!movieId, // Only run if movieId is provided
  });
};

// Hook for getting recently watched recommendations
export const useRecentlyWatchedRecommendations = () => {
  return useQuery({
    queryKey: ['recently-watched-recommendations'],
    queryFn: () => recommendationService.getRecentlyWatchedRecommendations(),
    staleTime: 5 * 60 * 1000,
  });
};

// Hook for recording movie views
export const useRecordMovieView = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ 
      movieId, 
      data 
    }: { 
      movieId: number; 
      data: { completed: boolean; watch_duration?: number; }
    }) => recommendationService.recordMovieView(movieId, data),
    onSuccess: () => {
      // Invalidate relevant queries to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['recommendations'] });
      queryClient.invalidateQueries({ queryKey: ['recently-watched-recommendations'] });
    },
  });
};

// Hook for updating user preferences
export const useUpdatePreferences = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: recommendationService.updatePreferences,
    onSuccess: () => {
      // Invalidate recommendations to get fresh data based on new preferences
      queryClient.invalidateQueries({ queryKey: ['recommendations'] });
    },
  });
};

// Hook for getting trending recommendations
export const useTrendingRecommendations = () => {
  return useQuery({
    queryKey: ['trending-recommendations'],
    queryFn: () => recommendationService.getTrendingRecommendations(),
    staleTime: 15 * 60 * 1000, // Keep trending data fresh for 15 minutes
  });
};

// Hook for getting genre-based recommendations
export const useGenreRecommendations = (genre: string) => {
  return useQuery({
    queryKey: ['genre-recommendations', genre],
    queryFn: () => recommendationService.getGenreRecommendations(genre),
    enabled: !!genre,
    staleTime: 5 * 60 * 1000,
  });
};

// Custom hook to combine recommendation sources
export const useCombinedRecommendations = (filters: RecommendationFilters = {}) => {
  const personalizedRecs = useMovieRecommendations(filters);
  const trendingRecs = useTrendingRecommendations();
  const recentlyWatchedRecs = useRecentlyWatchedRecommendations();

  return {
    personalizedRecs: personalizedRecs.data,
    trendingRecs: trendingRecs.data,
    recentlyWatchedRecs: recentlyWatchedRecs.data,
    isLoading: personalizedRecs.isLoading || trendingRecs.isLoading || recentlyWatchedRecs.isLoading,
    isError: personalizedRecs.isError || trendingRecs.isError || recentlyWatchedRecs.isError,
    refetch: () => {
      personalizedRecs.refetch();
      trendingRecs.refetch();
      recentlyWatchedRecs.refetch();
    },
  };
};