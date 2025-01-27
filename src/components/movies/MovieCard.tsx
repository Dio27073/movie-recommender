import React from 'react';
import { Star } from 'lucide-react';
import { MovieCardProps, Movie } from '../../features/movies/types';
import { ViewType } from '../ui/ViewSwitcher';

interface ExtendedMovieCardProps extends MovieCardProps {
  onMovieClick: (movie: Movie) => void;
  viewType: ViewType;
}

export const MovieCard: React.FC<ExtendedMovieCardProps> = ({ 
  movie, 
  onMovieClick,
  viewType 
}) => {
  const handleClick = () => {
    onMovieClick(movie);
  };

  // Base classes shared across all view types
  const baseClasses = "cursor-pointer bg-white dark:bg-dark-secondary rounded-lg shadow-lg overflow-hidden transform transition-all duration-200 hover:shadow-xl dark:shadow-gray-900";

  // View-specific classes and layouts
  const viewClasses = {
    grid: `${baseClasses}`,
    list: `${baseClasses} flex`,
    compact: `${baseClasses} py-2 px-4`,
  };

  const imageClasses = {
    grid: "w-full h-64 object-cover",
    list: "w-48 h-full object-cover",
    compact: "w-16 h-16 rounded-md object-cover",
  };

  const contentClasses = {
    grid: "p-4",
    list: "p-4 flex-1",
    compact: "flex items-center ml-4 flex-1",
  };

  const renderContent = () => {
    switch (viewType) {
      case 'grid':
        return (
          <>
            <img
              src={movie.imageUrl || '/api/placeholder/200/300'}
              alt={movie.title}
              className={imageClasses[viewType]}
            />
            <div className={contentClasses[viewType]}>
              <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-2 line-clamp-1">
                {movie.title}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                {movie.release_year}
              </p>
              <div className="flex items-center mb-3">
                <Star className="w-5 h-5 text-yellow-400 fill-current" />
                <span className="ml-2 text-gray-700 dark:text-gray-300 font-medium">
                  {movie.imdb_rating?.toFixed(1) || 'N/A'}
                </span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                {movie.description}
              </p>
              <div className="flex flex-wrap gap-2">
                {movie.genres.map((genre) => (
                  <span key={genre} className="px-2 py-1 text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded-full">
                    {genre}
                  </span>
                ))}
              </div>
            </div>
          </>
        );

      case 'list':
        return (
          <>
            <img
              src={movie.imageUrl || '/api/placeholder/200/300'}
              alt={movie.title}
              className={imageClasses[viewType]}
            />
            <div className={contentClasses[viewType]}>
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-1">
                    {movie.title}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {movie.release_year}
                  </p>
                </div>
                <div className="flex items-center">
                  <Star className="w-5 h-5 text-yellow-400 fill-current" />
                  <span className="ml-2 text-gray-700 dark:text-gray-300 font-medium">
                    {movie.imdb_rating?.toFixed(1) || 'N/A'}
                  </span>
                </div>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 my-3 line-clamp-2">
                {movie.description}
              </p>
              <div className="flex flex-wrap gap-2">
                {movie.genres.map((genre) => (
                  <span key={genre} className="px-2 py-1 text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded-full">
                    {genre}
                  </span>
                ))}
              </div>
            </div>
          </>
        );

      case 'compact':
        return (
          <>
            <img
              src={movie.imageUrl || '/api/placeholder/200/300'}
              alt={movie.title}
              className={imageClasses[viewType]}
            />
            <div className={contentClasses[viewType]}>
              <div className="flex-1">
                <h3 className="text-base font-semibold text-gray-800 dark:text-gray-100">
                  {movie.title}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {movie.release_year}
                </p>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center">
                  <Star className="w-4 h-4 text-yellow-400 fill-current" />
                  <span className="ml-1 text-sm text-gray-700 dark:text-gray-300">
                    {movie.imdb_rating?.toFixed(1) || 'N/A'}
                  </span>
                </div>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {movie.genres[0]}
                </span>
              </div>
            </div>
          </>
        );
    }
  };

  return (
    <div onClick={handleClick} className={viewClasses[viewType]}>
      {renderContent()}
    </div>
  );
};