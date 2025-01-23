// src/features/movies/types.ts
export type SortOption = 'release_date_desc' | 'release_date_asc' | 'rating_desc' | 'rating_asc' | 'title_asc' | 'title_desc';

export interface Movie {
  id: number;
  title: string;
  description?: string;
  genres: string | string[];  // can be either string or string array
  release_year: number;
  average_rating: number;
  imageUrl?: string;
}

export interface MovieCardProps {
  movie: Omit<Movie, 'genres'> & { genres: string[] };  // ensure genres is always string[]
  onRate: (rating: number) => Promise<void>;
}

export interface FilterParams {
  genres?: Set<string>;
  yearRange?: [number, number];
  minRating?: number;
  page?: number;
  per_page?: number;
  sort?: SortOption;
}

// Update MovieFilterProps to include sort props
export interface MovieFilterProps {
  genres: string[];
  selectedGenres: Set<string>;
  yearRange: [number, number];
  minRating: number;
  sortBy: SortOption;
  onFilterChange: (filterType: keyof FilterParams, value: FilterValue | SortOption) => void;
  minYear: number;
  maxYear: number;
}

// Add this type to handle different filter value types
export type FilterValue = 
  | { genre: string; checked: boolean }  // for genre changes
  | [number, number]                     // for year range
  | number 
  | SortOption; // for rating

export interface MovieCreate {
  title: string;
  description?: string;
  genres: string[];  // Changed to match Movie interface
  release_year: number;
  average_rating?: number;
}

// User Types
export interface User {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
}

export interface UserCreate {
  email: string;
  username: string;
  password: string;
}

// Auth Types
export interface Token {
  access_token: string;
  token_type: string;
}

export interface LoginCredentials {
  username: string;  // email is used as username
  password: string;
}

// Rating Type
export interface Rating {
  movie_id: number;
  rating: number;  // 1-5 stars
}

// API Response Types
export interface ApiError {
  detail: string;
}

export interface RatingResponse {
  message: string;
}

