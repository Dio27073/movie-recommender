import { Info } from 'lucide-react';
import { Movie } from '../../features/movies/types';
import { MovieCard } from './MovieCard';
import { ViewType } from '../ui/ViewSwitcher';

interface RecommendationCardProps {
  movie: Movie;
  confidenceScore: number;
  recommendationReason?: string;
  onMovieClick: (movie: Movie) => void;
  viewType: ViewType;
}

// Helper function to ensure genres is always an array
const normalizeGenres = (genres: string | string[]): string[] => {
  if (Array.isArray(genres)) {
    return genres;
  }
  return genres.split(',').map(g => g.trim());
};

export const RecommendationCard = ({
  movie,
  confidenceScore,
  recommendationReason,
  onMovieClick,
  viewType
}: RecommendationCardProps) => {
  // Create a new movie object with normalized genres
  const normalizedMovie = {
    ...movie,
    genres: normalizeGenres(movie.genres)
  };

  return (
    <div className="relative group">
      {/* Confidence Score Indicator */}
      <div className="absolute top-2 right-2 z-10 bg-black/70 px-2 py-1 rounded-full text-xs text-white">
        {Math.round(confidenceScore * 100)}% Match
      </div>
      
      {/* Recommendation Reason Tooltip */}
      {recommendationReason && (
        <div className="absolute top-2 left-2 z-10 group">
          <Info className="w-5 h-5 text-white bg-black/70 rounded-full p-1" />
          <div className="invisible group-hover:visible absolute left-0 mt-1 w-48 p-2 bg-black/90 text-white text-xs rounded shadow-lg">
            {recommendationReason}
          </div>
        </div>
      )}
      
      {/* Reuse existing MovieCard with normalized movie data */}
      <MovieCard
        movie={normalizedMovie}
        onMovieClick={onMovieClick}
        viewType={viewType}
      />
    </div>
  );
};