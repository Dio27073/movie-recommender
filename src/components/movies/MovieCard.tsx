import React from 'react';
import { Star } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { MovieCardProps } from '../../features/movies/types';

export const MovieCard: React.FC<MovieCardProps> = ({ movie }) => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/movie/${movie.id}`, { state: { movie } });
  };

  return (
    <div 
      onClick={handleClick}
      className="cursor-pointer relative bg-white dark:bg-dark-secondary rounded-lg shadow-lg overflow-hidden transform transition-all duration-200 hover:shadow-xl dark:shadow-gray-900"
    >
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
        
        <div className="flex items-center mb-3">
          <Star className="w-5 h-5 text-yellow-400 fill-current" />
          <span className="ml-2 text-gray-700 dark:text-gray-300 font-medium">
            {movie.average_rating.toFixed(1)}
          </span>
        </div>

        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
          {movie.description}
        </p>
        
        <div className="flex flex-wrap gap-2">
          {movie.genres.map((genre) => (
            <span 
              key={genre}
              className="px-2 py-1 text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded-full"
            >
              {genre}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};