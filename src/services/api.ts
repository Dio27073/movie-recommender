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

class ApiService {
  private token: string | null = null;

  constructor() {
    // Initialize token from storage when service is created
    const token = localStorage.getItem('auth_token');
    if (token) {
      this.setToken(token);
    }
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
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

      return data as T;
    } catch (error) {
      console.error('Request error:', error);
      throw error instanceof Error ? error : new Error('An error occurred');
    }
  }

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    return this.request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials)
    });
  }

  async register(credentials: RegisterCredentials): Promise<AuthResponse> {
    return this.request<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(credentials)
    });
  }

  async getCurrentUser(): Promise<User> {
    if (!this.token) {
      throw new Error('No authentication token');
    }
    return this.request<User>('/auth/me', {
      method: 'GET'
    });
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
    streaming_platforms?: string;  // Add this
    mood_tags?: string; 
    release_date_lte?: string;  // Add this line       
  } = {}): Promise<MovieResponse> {
    const queryParams = new URLSearchParams();

    //debug logging
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

    const response = await this.request<MovieResponse>(`/movies/?${queryString}`);
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
    
    return this.request<void>(`/movies/${movieId}/view`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateRecommendationPreferences(preferences: UserPreferences): Promise<void> {
    if (!this.token) {
      throw new Error('Authentication required');
    }

    return this.request<void>('/api/recommender/preferences', {
      method: 'PUT',
      body: JSON.stringify(preferences),
    });
  }

  async rateMovie(rating: Rating): Promise<RatingResponse> {
    return this.request<RatingResponse>(`/movies/${rating.movie_id}/rate`, {
      method: 'POST',
      body: JSON.stringify(rating)
    });
  }

  async getTrendingRecommendations(): Promise<Movie[]> {
    return this.request<Movie[]>('/api/recommender/trending');
  }

  async getGenreRecommendations(genre: string): Promise<Movie[]> {
    return this.request<Movie[]>(`/api/recommender/genre/${genre}`);
  }

  // View History Methods
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

  // User Preferences Methods
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
    return this.request<any>(`/api/movies/${movieId}/view`, {
      method: 'POST',
      body: JSON.stringify({ completed: true })
    });
  }
  
  async removeFromLibrary(movieId: number) {
    return this.request<any>(`/api/movies/${movieId}/view`, {
      method: 'DELETE'
    });
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