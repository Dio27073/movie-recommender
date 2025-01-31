import {
  Movie,
  MovieCreate,
  Rating,
  RatingResponse,
  ApiError
} from '../features/movies/types';

import { AuthResponse, LoginCredentials, RegisterCredentials, User } from './authService';

const API_URL = 'http://localhost:8000';

class ApiService {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
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

  // Authentication Methods
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await fetch(`${API_URL}/token`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const data = await response.json();
    this.setToken(data.access_token);
    return data;
  }

  async register(credentials: RegisterCredentials): Promise<void> {
    return this.request<void>('/register', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/users/me');
  }

  async updateUser(userData: Partial<User>): Promise<User> {
    return this.request<User>('/users/me', {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
  }

  // Movie Methods
  async getMovies(params: {
    page?: number;
    per_page?: number;
    genres?: string;
    cast_crew?: string[];
    min_year?: number;
    max_year?: number;
    min_rating?: number;
    sort?: string;
  } = {}): Promise<any> {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        if (Array.isArray(value)) {
          value.forEach(v => queryParams.append(key, v));
        } else {
          queryParams.append(key, value.toString());
        }
      }
    });

    return this.request<any>(`/movies/?${queryParams.toString()}`);
  }

  async getMovie(id: string | number): Promise<Movie> {
    return this.request<Movie>(`/movies/${id}`);
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

  async getMovieTrailer(id: string | number): Promise<string> {
    const response = await this.request<{ trailer_url: string }>(`/movies/${id}/trailer`);
    return response.trailer_url;
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