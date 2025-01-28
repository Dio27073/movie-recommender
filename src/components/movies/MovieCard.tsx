import { Star } from 'lucide-react';
import { MovieCardProps, Movie } from '../../features/movies/types';
import { ViewType } from '../ui/ViewSwitcher';

// Types
interface ExtendedMovieCardProps extends MovieCardProps {
  onMovieClick: (movie: Movie) => void;
  viewType: ViewType;
}

const getGenresArray = (genres: string | string[]): string[] => {
  if (Array.isArray(genres)) {
    return genres;
  }
  return genres.split(',').map((g: string) => g.trim());
};

// Shared Components
const GenreTag = ({ genre }: { genre: string }) => (
  <span className="px-2 py-1 text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded-full">
    {genre}
  </span>
);

const Rating = ({ rating, size = 'medium' }: { rating: number | null | undefined; size?: 'small' | 'medium' }) => (
  <div className="flex items-center">
    <Star className={`${size === 'small' ? 'w-4 h-4' : 'w-5 h-5'} text-yellow-400 fill-current`} />
    <span className={`${size === 'small' ? 'text-sm ml-1' : 'ml-2'} text-gray-700 dark:text-gray-300 font-medium`}>
      {rating?.toFixed(1) || 'N/A'}
    </span>
  </div>
);

// View-specific components
const GridView = ({ movie }: { movie: Movie }) => (
  <>
    <img
      src={movie.imageUrl || '/api/placeholder/200/300'}
      alt={movie.title}
      className="w-full h-64 object-cover"
    />
    <div className="p-4">
      <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-2 line-clamp-1">
        {movie.title}
      </h3>
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
        {movie.release_year}
      </p>
      <div className="mb-3">
        <Rating rating={movie.imdb_rating} />
      </div>
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
        {movie.description}
      </p>
      <div className="flex flex-wrap gap-2">
        {getGenresArray(movie.genres).map((genre: string) => (
          <GenreTag key={genre} genre={genre} />
        ))}
      </div>
    </div>
  </>
);

const ListView = ({ movie }: { movie: Movie }) => (
  <>
    <img
      src={movie.imageUrl || '/api/placeholder/200/300'}
      alt={movie.title}
      className="w-48 h-full object-cover"
    />
    <div className="p-4 flex-1">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-1">
            {movie.title}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {movie.release_year}
          </p>
        </div>
        <Rating rating={movie.imdb_rating} />
      </div>
      <p className="text-sm text-gray-600 dark:text-gray-400 my-3 line-clamp-2">
        {movie.description}
      </p>
      <div className="flex flex-wrap gap-2">
        {getGenresArray(movie.genres).map((genre: string) => (
          <GenreTag key={genre} genre={genre} />
        ))}
      </div>
    </div>
  </>
);

const CompactView = ({ movie }: { movie: Movie }) => (
  <>
    <img
      src={movie.imageUrl || '/api/placeholder/200/300'}
      alt={movie.title}
      className="w-16 h-16 rounded-md object-cover"
    />
    <div className="flex items-center ml-4 flex-1">
      <div className="flex-1">
        <h3 className="text-base font-semibold text-gray-800 dark:text-gray-100">
          {movie.title}
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {movie.release_year}
        </p>
      </div>
      <div className="flex items-center gap-4">
        <Rating rating={movie.imdb_rating} size="small" />
        <span className="text-sm text-gray-600 dark:text-gray-400">
          {getGenresArray(movie.genres)[0]}
        </span>
      </div>
    </div>
  </>
);

// Main component
export const MovieCard = ({ 
  movie, 
  onMovieClick,
  viewType 
}: ExtendedMovieCardProps) => {
  const baseClasses = "cursor-pointer bg-white dark:bg-dark-secondary rounded-lg shadow-lg overflow-hidden transform transition-all duration-200 hover:shadow-xl dark:shadow-gray-900";
  
  const viewClasses = {
    grid: baseClasses,
    list: `${baseClasses} flex`,
    compact: `${baseClasses} py-2 px-4`,
  };

  const ViewComponent = {
    grid: GridView,
    list: ListView,
    compact: CompactView,
  }[viewType];

  return (
    <div 
      onClick={() => onMovieClick(movie)} 
      className={viewClasses[viewType]}
      role="button"
      tabIndex={0}
      onKeyPress={(e) => e.key === 'Enter' && onMovieClick(movie)}
    >
      <ViewComponent movie={movie} />
    </div>
  );
};