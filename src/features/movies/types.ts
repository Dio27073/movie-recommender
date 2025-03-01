// View and Display Types
export type ViewType = 'grid' | 'list' | 'compact';

export type SortOption = 
  | 'release_date_desc' 
  | 'release_date_asc' 
  | 'imdb_rating_desc' 
  | 'imdb_rating_asc' 
  | 'random'
  | 'title_asc' 
  | 'title_desc';

export type SearchType = 'title' | 'cast_crew';

export type RecommendationType = 'content' | 'collaborative' | 'hybrid';

// Movie Related Types
export interface Movie {
  id: number;
  title: string;
  description?: string;
  genres: string[] | string;  // Changed to always be string[]
  release_year: number;
  average_rating: number;
  imageurl?: string;
  imdb_id?: string;
  imdb_rating?: number;
  imdb_votes?: number;
  trailer_url?: string;
  cast?: string[];   // Changed to always be string[]
  crew?: string[];   // Changed to always be string[]
}

export type MovieCreate = Omit<Movie, 'id' | 'imageurl' | 'trailer_url' | 'cast' | 'crew'> & {
  imdb_id?: string;
};

// Recommendation Types
export interface MovieRecommendation extends Movie {
  movie_id: number;
  confidence_score: number;
  recommendation_type: RecommendationType;
  reason: string;
}

export interface RecommendationResponse {
  items: MovieRecommendation[];
  total: number;
  page: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface RecommendationFilters {
  strategy?: RecommendationType;
  excludeWatched?: boolean;
  minRating?: number;
  genres?: string[];
  page?: number;
  per_page?: number;
}

// Filter Types
export interface FilterParams {
  genre?: Set<string>;  // Changed from genres to genre
  yearRange?: [number, number];
  ratingRange?: [number, number];
  page?: number;
  per_page?: number;
  sort?: SortOption;
  randomSeed?: number;  
  view?: ViewType;
  castCrew?: Set<string>;
  searchQuery?: string;
  searchType?: SearchType;
  contentRating?: Set<string>;
  moodTags?: Set<string>;
  streamingPlatforms?: Set<string>;
}

export interface MovieApiParams {
  sort?: string;
  per_page?: number;
  max_year?: number;
  min_year?: number;
  genres?: string[];
  page?: number;
  streaming_platforms?: string;  // For Netflix, Hulu, etc.
  mood_tags?: string;           // For Funny, etc.
  release_date_lte?: string;  // Add this line
}

export type FilterValue = 
  | { type: 'genre'; genre: string; checked: boolean }
  | { type: 'yearRange'; value: [number, number] }
  | { type: 'ratingRange'; value: [number, number] }
  | { type: 'view'; value: ViewType }
  | { type: 'sort'; value: SortOption; randomSeed?: number }
  | { type: 'castCrew'; value: Set<string> }
  | { type: 'contentRating'; value: Set<string> }
  | { type: 'moodTags'; value: Set<string> }
  | { type: 'streamingPlatforms'; value: Set<string> };

// Component Props Types
export interface MovieCardProps {
  movie: Movie;  // Using the updated Movie type with string[] genres
  viewType: ViewType;
  onMovieClick: (movie: Movie) => void;
  onAddToLibrary: (movie: Movie) => void;
  onRemoveFromLibrary: (movieId: number) => void;
  isInLibrary: boolean;
}

export interface MovieFilterProps {
  genres: string[];  // This is what the interface expects
  selectedGenres: Set<string>;
  yearRange: [number, number];
  ratingRange: [number, number];
  sortBy: SortOption;
  viewType: ViewType;  // Add this line
  onFilterChange: (filterType: keyof FilterParams, value: FilterValue) => void;
  minYear: number;
  maxYear: number;
  searchQuery: string;
  searchType: SearchType;
  onSearchChange: (query: string, type: SearchType) => void;
  onCastCrewSelect: (name: string) => void;
  selectedCastCrew: Set<string>;
  onMovieSelect: (movie: Movie) => void;
  selectedContentRatings?: Set<string>;
  selectedMoods?: Set<string>;
  selectedPlatforms?: Set<string>;
}

// User and Authentication Types
export interface User {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
}

export type UserCreate = Pick<User, 'email' | 'username'> & {
  password: string;
};

export interface UserPreferences {
  favorite_genres?: string[];
  preferred_languages?: string[];
  content_preferences?: Record<string, unknown>;  // Changed from 'any' to 'unknown'
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface LoginCredentials {
  username: string;  // email is used as username
  password: string;
}

// Rating and History Types
export interface Rating {
  movie_id: number;
  rating: number;  // 1-5 stars
}

export interface ViewingHistoryItem {
  movie_id: number;
  watched_at: string;
  completed: boolean;
  watch_duration?: number;
}

// API Response Types
export interface ApiError {
  detail: string;
}

export interface RatingResponse {
  message: string;
}

export interface LibraryMovie extends Movie {
  movie_id: number;  // ID from the backend
  watched_at?: string;  // ISO date string
  rating?: number;  // 1-5 stars
  rated_at?: string;  // ISO date string
  completed?: boolean;
}

export interface MovieDetailsResponse {
  items: Movie[];
  total: number;
  page: number;
  total_pages: number;
}