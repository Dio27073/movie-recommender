import {
  Movie,
  RatingResponse,
  ApiError,
  RecommendationResponse,
  RecommendationFilters,
  UserPreferences,
  LibraryMovie,
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

interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

class ApiService {
  private token: string | null = null;
  private cache: Map<string, CacheEntry<any>> = new Map();
  private CACHE_TTL: number = 5 * 60 * 1000; // 5 minutes
  private keepAliveInterval: NodeJS.Timeout | null = null;
  private isBackendReady: boolean = false;

  constructor() {
    const token = localStorage.getItem('auth_token');
    if (token) {
      this.setToken(token);
    }
    
    // Setup periodic cache cleanup
    setInterval(() => this.cleanupCache(), 15 * 60 * 1000);
    
    // Start keep-alive ping
    this.startKeepAlive();
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }

  private startKeepAlive() {
    // Ping every 10 minutes to keep backend warm
    this.keepAliveInterval = setInterval(async () => {
      try {
        await fetch(`${API_URL}/keep-alive`);
        console.log('Keep-alive ping sent');
      } catch (error) {
        console.warn('Keep-alive ping failed:', error);
      }
    }, 10 * 60 * 1000); // 10 minutes
  }

  private stopKeepAlive() {
    if (this.keepAliveInterval) {
      clearInterval(this.keepAliveInterval);
      this.keepAliveInterval = null;
    }
  }

  private cleanupCache() {
    const now = Date.now();
    let expiredCount = 0;
    
    this.cache.forEach((entry, key) => {
      if (now - entry.timestamp > this.CACHE_TTL) {
        this.cache.delete(key);
        expiredCount++;
      }
    });
    
    if (expiredCount > 0) {
      console.log(`Removed ${expiredCount} expired cache entries`);
    }
  }

  private getCacheKey(endpoint: string, options: RequestInit): string {
    return `${endpoint}:${JSON.stringify(options)}`;
  }

  // Enhanced request method with cold start handling
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    useCache: boolean = true,
    retries: number = 3
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

    // Check cache first for GET requests
    const shouldUseCache = useCache && (!options.method || options.method === 'GET');
    
    if (shouldUseCache) {
      const cacheKey = this.getCacheKey(endpoint, config);
      const cachedEntry = this.cache.get(cacheKey);
      
      if (cachedEntry && (Date.now() - cachedEntry.timestamp < this.CACHE_TTL)) {
        console.log(`Using cached data for: ${url}`);
        return cachedEntry.data;
      }
    }

    // Retry logic for cold starts
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        console.log(`Making request to: ${url} (attempt ${attempt})`);
        
        // Longer timeout for first attempt (cold start)
        const timeoutMs = attempt === 1 ? 90000 : 30000; // 90s first attempt, 30s others
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
        
        const response = await fetch(url, {
          ...config,
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        console.log(`Response status: ${response.status}`);

        let data;
        const textResponse = await response.text();

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

        // Mark backend as ready after first successful request
        if (!this.isBackendReady) {
          this.isBackendReady = true;
          console.log('Backend is now ready');
        }

        // Cache successful GET responses
        if (shouldUseCache) {
          const cacheKey = this.getCacheKey(endpoint, config);
          this.cache.set(cacheKey, {
            data: data,
            timestamp: Date.now()
          });
        }

        return data as T;
        
      } catch (error) {
        console.error(`Request attempt ${attempt} failed:`, error);
        
        // If it's the last attempt, throw the error
        if (attempt === retries) {
          throw error instanceof Error ? error : new Error('An error occurred');
        }
        
        // Wait before retrying (exponential backoff)
        const waitTime = Math.min(1000 * Math.pow(2, attempt - 1), 10000);
        console.log(`Waiting ${waitTime}ms before retry...`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }

    throw new Error('Max retries exceeded');
  }

  // Health check method
  async checkHealth(): Promise<{ status: string; initialization_complete: boolean }> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 second timeout
    
    try {
      const response = await fetch(`${API_URL}/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        mode: 'cors',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        return { status: 'unhealthy', initialization_complete: false };
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      clearTimeout(timeoutId);
      return { status: 'unhealthy', initialization_complete: false };
    }
  }

  // Wait for backend to be ready
  async waitForBackend(maxWaitMs: number = 90000): Promise<void> {
    const startTime = Date.now();
    
    while (Date.now() - startTime < maxWaitMs) {
      try {
        const health = await this.checkHealth();
        if (health.status === 'healthy') {
          this.isBackendReady = true;
          console.log('Backend is ready!');
          return;
        }
      } catch (error) {
        // Continue waiting
      }
      
      // Wait 2 seconds before next check
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    throw new Error('Backend failed to start within timeout period');
  }

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    return this.request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials)
    }, false);
  }

  async register(credentials: RegisterCredentials): Promise<AuthResponse> {
    return this.request<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(credentials)
    }, false);
  }

  async getCurrentUser(): Promise<User> {
    if (!this.token) {
      throw new Error('No authentication token');
    }
    
    const cachedUser = this.cache.get('currentUser');
    if (cachedUser && (Date.now() - cachedUser.timestamp < 60000)) {
      return cachedUser.data;
    }
    
    const user = await this.request<User>('/auth/me', { method: 'GET' });
    
    this.cache.set('currentUser', {
      data: user,
      timestamp: Date.now()
    });
    
    return user;
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
    const shouldCache = !params.sort || params.sort !== 'random';
    
    return await this.request<MovieResponse>(
      `/movies/?${queryString}`, 
      {}, 
      shouldCache
    );
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

      const response = await this.request<MovieResponse>(
        `/movies/trending/?${queryParams.toString()}`
      );

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

  // Movie Details
  async getMovieDetails(movieId: number): Promise<Movie> {
    return this.request<Movie>(`/movies/${movieId}`);
  }

  // Rating Methods
  async rateMovie(movieId: number, rating: number): Promise<RatingResponse> {
    if (!this.token) {
      throw new Error('Authentication required');
    }
    
    // Clear relevant caches
    this.cache.forEach((_, key) => {
      if (key.includes(`/movies/${movieId}`) || 
          key.includes('/api/users/me/library')) {
        this.cache.delete(key);
      }
    });
    
    return this.request<RatingResponse>(`/movies/${movieId}/rate`, {
      method: 'POST',
      body: JSON.stringify({ rating })
    }, false);
  }

  // Library Methods
  async addToLibrary(movieId: number): Promise<void> {
    if (!this.token) {
      throw new Error('Authentication required');
    }
    
    // Clear library cache
    this.cache.forEach((_, key) => {
      if (key.includes('/api/users/me/library')) {
        this.cache.delete(key);
      }
    });
    
    return this.request<void>(`/api/users/me/library/add`, {
      method: 'POST',
      body: JSON.stringify({ movie_id: movieId })
    }, false);
  }

  async removeFromLibrary(movieId: number): Promise<void> {
    if (!this.token) {
      throw new Error('Authentication required');
    }
    
    // Clear library cache
    this.cache.forEach((_, key) => {
      if (key.includes('/api/users/me/library')) {
        this.cache.delete(key);
      }
    });
    
    return this.request<void>(`/api/users/me/library/remove/${movieId}`, {
      method: 'DELETE'
    }, false);
  }

  async getUserLibrary(): Promise<LibraryMovie[]> {
    if (!this.token) {
      throw new Error('Authentication required');
    }
    
    return this.request<LibraryMovie[]>('/api/users/me/library', {
      method: 'GET'
    });
  }

  // Recommendation Methods
  async getRecommendations(filters: RecommendationFilters = {}): Promise<RecommendationResponse> {
    if (!this.token) {
      throw new Error('Authentication required');
    }
    
    const queryParams = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) {
        if (Array.isArray(value)) {
          value.forEach(v => queryParams.append(key, v.toString()));
        } else {
          queryParams.append(key, value.toString());
        }
      }
    });
    
    return this.request<RecommendationResponse>(
      `/api/recommender/recommendations/?${queryParams.toString()}`
    );
  }

  async getSimilarMovies(movieId: number): Promise<Movie[]> {
    return this.request<Movie[]>(`/api/recommender/movies/${movieId}/similar`);
  }

  async getRecentlyWatchedRecommendations(): Promise<Movie[]> {
    if (!this.token) {
      throw new Error('Authentication required');
    }
    
    return this.request<Movie[]>('/api/recommender/recently-watched');
  }

  async getTrendingRecommendations(): Promise<Movie[]> {
    return this.request<Movie[]>('/api/recommender/trending');
  }

  async getGenreRecommendations(genre: string): Promise<Movie[]> {
    return this.request<Movie[]>(`/api/recommender/genre/${encodeURIComponent(genre)}`);
  }

  // User Preferences
  async updateRecommendationPreferences(preferences: UserPreferences): Promise<void> {
    if (!this.token) {
      throw new Error('Authentication required');
    }
    
    // Clear preferences and recommendations cache
    this.cache.forEach((_, key) => {
      if (key.includes('/api/users/me/preferences') || 
          key.includes('/api/recommender/')) {
        this.cache.delete(key);
      }
    });
    
    return this.request<void>('/api/users/me/preferences', {
      method: 'PUT',
      body: JSON.stringify(preferences)
    }, false);
  }

  async getUserPreferences(): Promise<UserPreferences> {
    if (!this.token) {
      throw new Error('Authentication required');
    }
    
    return this.request<UserPreferences>('/api/users/me/preferences');
  }

  // Viewing History
  async recordMovieView(
    movieId: number, 
    data: { completed: boolean; watch_duration?: number }
  ): Promise<void> {
    if (!this.token) {
      throw new Error('Authentication required');
    }
    
    // Clear recommendations and history cache
    this.cache.forEach((_, key) => {
      if (key.includes('/api/recommender/') || 
          key.includes('/api/users/me/history')) {
        this.cache.delete(key);
      }
    });
    
    return this.request<void>(`/movies/${movieId}/view`, {
      method: 'POST',
      body: JSON.stringify(data),
    }, false);
  }

  async getViewingHistory(): Promise<any> {
    if (!this.token) {
      throw new Error('Authentication required');
    }
    
    return this.request<any>('/api/users/me/history');
  }

  // Cleanup method
  destroy() {
    this.stopKeepAlive();
    this.cache.clear();
  }
}

// Create singleton instance
const apiService = new ApiService();

export default apiService;