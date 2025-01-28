// View and Sort Types
export type ViewType = 'grid' | 'list' | 'compact';

export type SortOption = 
  | 'release_date_desc' 
  | 'release_date_asc' 
  | 'imdb_rating_desc' 
  | 'imdb_rating_asc' 
  | 'title_asc' 
  | 'title_desc';

export type SearchType = 'title' | 'cast_crew';

// Movie Types
export interface Movie {
  id: number;
  title: string;
  description?: string;
  genres: string | string[];
  release_year: number;
  average_rating: number;
  imageUrl?: string;
  imdb_id?: string;
  imdb_rating?: number;
  imdb_votes?: number;
  trailer_url?: string;
  cast?: string | string[];
  crew?: string | string[];
}

export interface MovieCreate {
  title: string;
  description?: string;
  genres: string[];
  release_year: number;
  average_rating?: number;
  imdb_id?: string;
  imdb_rating?: number;
  imdb_votes?: number;
}

// Component Props Types
export interface MovieCardProps {
  movie: Omit<Movie, 'genres'> & { genres: string[] };
  viewType: ViewType;
}

export interface MovieFilterProps {
  genres: string[];
  selectedGenres: Set<string>;
  yearRange: [number, number];
  ratingRange: [number, number];
  sortBy: SortOption;
  viewType: ViewType;
  onFilterChange: (filterType: keyof FilterParams, value: FilterValue) => void;
  minYear: number;
  maxYear: number;
  searchQuery: string;
  searchType: SearchType;
  onSearchChange: (query: string, type: SearchType) => void;
  selectedCastCrew: Set<string>;
  onCastCrewSelect: (name: string) => void;
  onMovieSelect: (movie: Movie) => void;
}

// Filter Types
export interface FilterParams {
  genres?: Set<string>;
  yearRange?: [number, number];
  ratingRange?: [number, number];
  page?: number;
  per_page?: number;
  sort?: SortOption;
  view?: ViewType;
  castCrew?: Set<string>;
  searchQuery?: string;
  searchType?: SearchType;
}

export type FilterValue = 
  | { genre: string; checked: boolean }
  | [number, number]
  | ViewType
  | SortOption
  | Set<string>;

// Authentication Types
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

export interface Token {
  access_token: string;
  token_type: string;
}

export interface LoginCredentials {
  username: string;  // email is used as username
  password: string;
}

// Rating Types
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