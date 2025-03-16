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

// Cache for movie data
const movieCache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes in milliseconds

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

      // Add random seed when sort is random
      if (filters.sort === 'random' && 'randomSeed' in filters) {
        urlParams.append('random_seed', filters.randomSeed?.toString() || Math.random().toString());
      }
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
    filters.sort === 'random' ? filters.randomSeed : undefined,
    filters.castCrew,
    filters.searchQuery,
    filters.searchType,
    filters.contentRating,
    filters.moodTags,
    filters.streamingPlatforms
  ]);
  
  const getCacheKey = useCallback(() => {
    return params.toString();
  }, [params]);
  
  const fetchMovies = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    const cacheKey = getCacheKey();
    
    // Check if we have cached data and it's not expired
    const cachedData = movieCache.get(cacheKey);
    if (cachedData && (Date.now() - cachedData.timestamp < CACHE_TTL)) {
      console.log('Using cached movie data');
      setMovies(cachedData.data.items);
      setPagination({
        total: cachedData.data.total,
        totalPages: cachedData.data.total_pages,
        hasNext: cachedData.data.has_next,
        hasPrev: cachedData.data.has_prev
      });
      setLoading(false);
      return;
    }
    
    try {
      const url = `${import.meta.env.VITE_API_URL}/movies/?${params}`;
      console.log('Fetching movies with URL:', url);
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch movies: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('API Response:', data);
      
      // Cache the results
      movieCache.set(cacheKey, {
        data: data,
        timestamp: Date.now()
      });
      
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
  }, [params, getCacheKey]);

  useEffect(() => {
    fetchMovies();
  }, [fetchMovies]);

  // Add a cache cleanup when component unmounts
  useEffect(() => {
    return () => {
      // Clear expired cache entries
      const now = Date.now();
      movieCache.forEach((value, key) => {
        if (now - value.timestamp > CACHE_TTL) {
          movieCache.delete(key);
        }
      });
    };
  }, []);

  return { movies, loading, error, pagination };
};

// Movie search hook with caching
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

  // Cache for search results
  const searchCache = new Map();

  const searchMovies = useCallback(async (query: string, page: number = 1) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    const cacheKey = `${query}:${page}`;
    
    // Check cache
    const cachedResults = searchCache.get(cacheKey);
    if (cachedResults && (Date.now() - cachedResults.timestamp < CACHE_TTL)) {
      console.log('Using cached search results');
      setSearchResults(cachedResults.data.items);
      setSearchPagination({
        total: cachedResults.data.total,
        totalPages: cachedResults.data.total_pages,
        hasNext: cachedResults.data.has_next,
        hasPrev: cachedResults.data.has_prev
      });
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/movies/search/?query=${encodeURIComponent(query)}&page=${page}`
      );
      
      if (!response.ok) {
        throw new Error(`Failed to search movies: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Cache the results
      searchCache.set(cacheKey, {
        data: data,
        timestamp: Date.now()
      });
      
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

  // Cleanup effect for search cache
  useEffect(() => {
    return () => {
      // Clear expired cache entries
      const now = Date.now();
      searchCache.forEach((value, key) => {
        if (now - value.timestamp > CACHE_TTL) {
          searchCache.delete(key);
        }
      });
    };
  }, []);

  return { searchMovies, searchResults, loading, error, searchPagination };
};

// The rest of the hooks remain mostly unchanged
export const useAllGenres = () => {
  const [genres, setGenres] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchGenres = async () => {
      try {
        const response = await fetch('/api/genres'); 
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

// Movie rating hook remains the same
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

// The React-Query hooks remain unchanged since they handle caching internally
export const useMovieRecommendations = (filters: RecommendationFilters = {}) => {
  return useQuery({
    queryKey: ['recommendations', filters],
    queryFn: () => recommendationService.getRecommendations(filters),
    placeholderData: (previousData) => previousData,
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
  });
};

export const useSimilarMovies = (movieId: number) => {
  return useQuery({
    queryKey: ['similar-movies', movieId],
    queryFn: () => recommendationService.getSimilarMovies(movieId),
    enabled: !!movieId,
    staleTime: 10 * 60 * 1000, // Cache similar movies for 10 minutes
  });
};

export const useRecentlyWatchedRecommendations = () => {
  return useQuery({
    queryKey: ['recently-watched-recommendations'],
    queryFn: () => recommendationService.getRecentlyWatchedRecommendations(),
    staleTime: 5 * 60 * 1000,
  });
};

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
      queryClient.invalidateQueries({ queryKey: ['recommendations'] });
      queryClient.invalidateQueries({ queryKey: ['recently-watched-recommendations'] });
    },
  });
};

export const useUpdatePreferences = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: recommendationService.updatePreferences,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recommendations'] });
    },
  });
};

export const useTrendingRecommendations = () => {
  return useQuery({
    queryKey: ['trending-recommendations'],
    queryFn: () => recommendationService.getTrendingRecommendations(),
    staleTime: 15 * 60 * 1000, // Keep trending data fresh for 15 minutes
  });
};

export const useGenreRecommendations = (genre: string) => {
  return useQuery({
    queryKey: ['genre-recommendations', genre],
    queryFn: () => recommendationService.getGenreRecommendations(genre),
    enabled: !!genre,
    staleTime: 5 * 60 * 1000,
  });
};

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