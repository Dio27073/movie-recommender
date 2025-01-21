export interface Movie {
    id: number;
    title: string;
    year: number;
    rating: number;
    imageUrl?: string;
  }
  
  export interface MovieCardProps {
    title: string;
    year: number;
    rating: number;
    imageUrl?: string;
    onRate: (rating: number) => void;
  }
  
  export interface MovieFilterProps {
    genres: string[];
    onFilterChange: (genre: string, checked: boolean) => void;
  }
  
  export interface MovieGridProps {
    movies: Movie[];
    onRate: (movieId: number, rating: number) => void;
  }