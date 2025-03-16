import {
  Movie,
  Rating,
  RatingResponse,
  ApiError,
  RecommendationResponse,
  RecommendationFilters,
  UserPreferences
} from '../features/movies/types';

import { AuthResponse, LoginCredentials, RegisterCredentials, User } from './authService';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface MovieResponse {
  items: Movie[];
  total: number;
  page: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

// Cache interface
interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

class ApiService {
  private token: string | null = null;
  private cache: Map<string, CacheEntry<any>> = new Map();
  private CACHE_TTL: number = 5 * 60 * 1000; // 5 minutes cache TTL

  constructor() {
    // Initialize token from storage when service is created
    const token = localStorage.getItem('auth_token');
    if (token) {
      this.setToken(token);
    }
    
    // Setup periodic cache cleanup
    setInterval(() => this.cleanupCache(), 15 * 60 * 1000); // Clean every 15 minutes
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }
  
  private cleanupCache() {
    console.log('Cleaning up expired cache entries');
    const now = Date.now();
    let expiredCount = 0;
    
    this.cache.forEach((entry, key) => {
      if (now - entry.timestamp > this.CACHE_TTL) {
        this.cache.delete(key);
        expiredCount++;
      }
    });
    
    console.log(`Removed ${expiredCount} expired cache entries`);
  }

  private getCacheKey(endpoint: string, options: RequestInit): string {
    // Create a unique key based on the endpoint and request options
    return `${endpoint}:${JSON.stringify(options)}`;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    useCache: boolean = true // New parameter to control caching
  ): Promise<T> {
    const url = `${API_URL}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const config: RequestInit = {
      ...options,
      headers: {
        ...headers,
        ...options.headers,
      },
      credentials: 'include' as RequestCredentials,
      mode: 'cors' as RequestMode
    };

    // Don't use cache for non-GET requests or if explicitly disabled
    const shouldUseCache = useCache && (!options.method || options.method === 'GET');
    
    if (shouldUseCache) {
      const cacheKey = this.getCacheKey(endpoint, config);
      const cachedEntry = this.cache.get(cacheKey);
      
      // Return cached data if valid
      if (cachedEntry && (Date.now() - cachedEntry.timestamp < this.CACHE_TTL)) {
        console.log(`Using cached data for: ${url}`);
        return cachedEntry.data;
      }
    }

    try {
      console.log(`Making request to: ${url}`);
      console.log('Request config:', config);

      const response = await fetch(url, config);
      
      console.log('Response status:', response.status);

      let data;
      const textResponse = await response.text();
      console.log('Raw response:', textResponse);

      try {
        data = JSON.parse(textResponse);
      } catch (e) {
        console.error('Failed to parse JSON:', e);
        throw new Error('Invalid JSON response from server');
      }

      if (!response.ok) {
        console.error('Request failed:', data);
        throw new Error((data as ApiError).detail || 'An error occurred');
      }

      // Cache successful GET responses
      if (shouldUseCache) {
        const cacheKey = this.getCacheKey(endpoint, config);
        this.cache.set(cacheKey, {
          data: data,
          timestamp: Date.now()
        });
        console.log(`Cached response for: ${url}`);
      }

      return data as T;
    } catch (error) {
      console.error('Request error:', error);
      throw error instanceof Error ? error : new Error('An error occurred');
    }
  }

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    // Don't cache authentication requests
    return this.request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials)
    }, false);
  }

  async register(credentials: RegisterCredentials): Promise<AuthResponse> {
    // Don't cache registration requests
    return this.request<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(credentials)
    }, false);
  }

  async getCurrentUser(): Promise<User> {
    if (!this.token) {
      throw new Error('No authentication token');
    }
    // Cache current user for 1 minute
    const currentUserCacheTTL = 60 * 1000; 
    const cachedUser = this.cache.get('currentUser');
    
    if (cachedUser && (Date.now() - cachedUser.timestamp < currentUserCacheTTL)) {
      return cachedUser.data;
    }
    
    const user = await this.request<User>('/auth/me', {
      method: 'GET'
    });
    
    this.cache.set('currentUser', {
      data: user,
      timestamp: Date.now()
    });
    
    return user;
  }

  async getRecommendations(filters: RecommendationFilters = {}): Promise<RecommendationResponse> {
    if (!this.token) {
      throw new Error('Authentication required for recommendations');
    }

    // Get current user to get the user ID
    const user = await this.getCurrentUser();

    const queryParams = new URLSearchParams();

    // Convert snake_case to camelCase for backend compatibility
    if (filters.excludeWatched !== undefined) {
      queryParams.append('exclude_watched', filters.excludeWatched.toString());
    }
    if (filters.minRating !== undefined) {
      queryParams.append('min_rating', filters.minRating.toString());
    }
    if (filters.strategy) {
      queryParams.append('strategy', filters.strategy);
    }
    if (filters.genres?.length) {
      filters.genres.forEach(genre => queryParams.append('genres', genre));
    }
    if (filters.page) {
      queryParams.append('page', filters.page.toString());
    }
    if (filters.per_page) {
      queryParams.append('per_page', filters.per_page.toString());
    }

    const queryString = queryParams.toString();
    return this.request<RecommendationResponse>(
      `/api/recommender/recommendations/${user.id}${queryString ? `?${queryString}` : ''}`
    );
  }
  
  async getSimilarMovies(movieId: number): Promise<Movie[]> {
    return this.request<Movie[]>(`/api/recommender/similar/${movieId}`);
  }

  async getRecentlyWatchedRecommendations(): Promise<Movie[]> {
    if (!this.token) {
      throw new Error('Authentication required');
    }
    return this.request<Movie[]>('/api/recommender/recently-watched');
  }

  async getMovies(params: {
    sort?: string;
    per_page?: number;
    max_year?: number;
    min_year?: number;
    genres?: string[];
    page?: number;
    streaming_platforms?: string;
    mood_tags?: string;
    release_date_lte?: string;
  } = {}): Promise<MovieResponse> {
    const queryParams = new URLSearchParams();

    // Debug logging
    console.log('Getting movies with params:', params);

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        if (Array.isArray(value)) {
          value.forEach(v => queryParams.append(key, v.toString()));
        } else {
          queryParams.append(key, value.toString());
        }
      }
    });

    const queryString = queryParams.toString();
    console.log('Final query string:', queryString);

    // Don't cache random sorts
    const shouldCache = !params.sort || params.sort !== 'random';
    
    const response = await this.request<MovieResponse>(
      `/movies/?${queryString}`, 
      {}, 
      shouldCache
    );
    
    console.log('Movies response:', response);
    return response;
  }

  async recordMovieView(
    movieId: number, 
    data: { completed: boolean; watch_duration?: number }
  ): Promise<void> {
    if (!this.token) {
      throw new Error('Authentication required');
    }
    
    // Clear recommendations cache when recording a view
    this.cache.forEach((_, key) => {
      if (key.includes('/api/recommender/recommendations/') || 
          key.includes('/api/recommender/recently-watched')) {
        this.cache.delete(key);
      }
    });
    
    return this.request<void>(`/movies/${movieId}/view`, {
      method: 'POST',
      body: JSON.stringify(data),
    }, false); // Don't cache POST requests
  }

  async updateRecommendationPreferences(preferences: UserPreferences): Promise<void> {
    if (!this.token) {
      throw new Error('Authentication required');
    }

    // Clear all recommendation caches when updating preferences
    this.cache.forEach((_, key) => {
      if (key.includes('/api/recommender/')) {
        this.cache.delete(key);
      }
    });

    return this.request<void>('/api/recommender/preferences', {
      method: 'PUT',
      body: JSON.stringify(preferences),
    }, false);
  }

  async rateMovie(rating: Rating): Promise<RatingResponse> {
    // Don't cache rating requests and invalidate affected movie caches
    const response = await this.request<RatingResponse>(`/movies/${rating.movie_id}/rate`, {
      method: 'POST',
      body: JSON.stringify(rating)
    }, false);
    
    // Invalidate any cached data for this movie
    this.cache.forEach((_, key) => {
      if (key.includes(`${rating.movie_id}`)) {
        this.cache.delete(key);
      }
    });
    
    return response;
  }

  async getTrendingRecommendations(): Promise<Movie[]> {
    return this.request<Movie[]>('/api/recommender/trending');
  }

  async getGenreRecommendations(genre: string): Promise<Movie[]> {
    return this.request<Movie[]>(`/api/recommender/genre/${genre}`);
  }

  async getViewingHistory(): Promise<{
    movie_id: number;
    watched_at: string;
    completed: boolean;
    watch_duration?: number;
  }[]> {
    if (!this.token) {
      throw new Error('Authentication required');
    }
    
    return this.request<any[]>('/movies/history');
  }

  async getUserPreferences(): Promise<UserPreferences> {
    if (!this.token) {
      throw new Error('Authentication required');
    }
    
    return this.request<UserPreferences>('/api/recommender/preferences');
  }

  async getUserLibrary() {
    return this.request<any>('/api/users/me/library', {
      method: 'GET'
    });
  }
  
  async addToLibrary(movieId: number) {
    // Clear library cache
    this.cache.delete('/api/users/me/library');
    
    return this.request<any>(`/api/movies/${movieId}/view`, {
      method: 'POST',
      body: JSON.stringify({ completed: true })
    }, false);
  }
  
  async removeFromLibrary(movieId: number) {
    // Clear library cache
    this.cache.delete('/api/users/me/library');
    
    return this.request<any>(`/api/movies/${movieId}/view`, {
      method: 'DELETE'
    }, false);
  }
  
  async getMovieDetails(movieId: number) {
    const response = await this.request<{
      items: Movie[];
      total: number;
      page: number;
      total_pages: number;
    }>(`/movies/?id=${movieId}`);
    return response;
  }
  
  getStreamUrl(movieId: string): string {
    // Handle both IMDB and TMDB IDs
    const id = movieId.startsWith('tt') ? movieId : `tt${movieId}`;
    return `https://vidsrc.icu/embed/movie/${id}`;
  }

  async getTrendingMovies(params: {
    time_window?: 'month' | 'week';
    page?: number;
    per_page?: number;
  } = {}): Promise<MovieResponse> {
    try {
        const queryParams = new URLSearchParams();
        
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined) {
                queryParams.append(key, value.toString());
            }
        });

        console.log('Fetching trending movies with params:', params);
        const response = await this.request<MovieResponse>(
            `/movies/trending/?${queryParams.toString()}`
        );
        console.log('Trending movies response:', response);

        if (!response) {
            throw new Error('Empty response from trending movies endpoint');
        }

        return {
            items: response.items || [],
            total: response.total || 0,
            page: response.page || 1,
            total_pages: response.total_pages || 1,
            has_next: response.has_next || false,
            has_prev: response.has_prev || false
        };
    } catch (error) {
        console.error('Failed to fetch trending movies:', error);
        return {
            items: [],
            total: 0,
            page: 1,
            total_pages: 1,
            has_next: false,
            has_prev: false
        };
    }
  }
}

// Create a singleton instance
const apiService = new ApiService();

export default apiService;