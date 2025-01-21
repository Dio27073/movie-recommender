import {
    Movie,
    MovieCreate,
    User,
    UserCreate,
    Token,
    LoginCredentials,
    Rating,
    RatingResponse,
    ApiError
  } from '../features/movies/types';
  
  const API_URL = 'http://localhost:8000';
  
  class ApiService {
    private token: string | null = null;
  
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
  
      const config = {
        ...options,
        headers: {
          ...headers,
          ...options.headers,
        },
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
  
    // Movie Methods
    async getMovies(skip = 0, limit = 100): Promise<Movie[]> {
      try {
        console.log('Fetching movies...');
        const movies = await this.request<Movie[]>(`/movies/?skip=${skip}&limit=${limit}`);
        console.log('Fetched movies:', movies);
        return movies;
      } catch (error) {
        console.error('Error fetching movies:', error);
        throw error;
      }
    }
  
    async createMovie(movie: MovieCreate): Promise<Movie> {
      return this.request<Movie>('/movies/', {
        method: 'POST',
        body: JSON.stringify(movie),
      });
    }
  
    // Rating Methods
    async rateMovie(rating: Rating): Promise<RatingResponse> {
      if (!this.token) {
        throw new Error('Authentication required');
      }
  
      return this.request<RatingResponse>('/rate/', {
        method: 'POST',
        body: JSON.stringify(rating),
      });
    }
  
    // Test connection method
    async testConnection(): Promise<boolean> {
      try {
        await fetch(API_URL);
        return true;
      } catch (error) {
        console.error('Connection test failed:', error);
        return false;
      }
    }
  }
  
  // Create a singleton instance
  const apiService = new ApiService();
  
  export default apiService;