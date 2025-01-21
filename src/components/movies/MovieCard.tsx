// src/components/movies/MovieCard.tsx
import React, { useState } from 'react';
import { Star, Loader } from 'lucide-react';
import { MovieCardProps } from '../../features/movies/types';

export const MovieCard: React.FC<MovieCardProps> = ({ movie, onRate }) => {
  const [isHovered, setIsHovered] = useState(false);
  const [isRating, setIsRating] = useState(false);
  
  const handleRate = async (rating: number) => {
    setIsRating(true);
    try {
      await onRate(rating);
    } finally {
      setIsRating(false);
    }
  };

  return (
    <div 
      className="relative bg-white rounded-lg shadow-lg overflow-hidden transform transition-all duration-200 hover:shadow-xl"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <img
        src={movie.imageUrl || '/api/placeholder/200/300'}
        alt={movie.title}
        className="w-full h-64 object-cover"
      />
      <div className="p-4">
        <h3 className="text-xl font-semibold text-gray-800 mb-2 line-clamp-1">{movie.title}</h3>
        <p className="text-sm text-gray-600 mb-2">{movie.release_year}</p>
        
        <div className="flex items-center mb-3">
          <Star className="w-5 h-5 text-yellow-400 fill-current" />
          <span className="ml-2 text-gray-700 font-medium">{movie.average_rating.toFixed(1)}</span>
        </div>

        <p className="text-sm text-gray-600 mb-3 line-clamp-2">
          {movie.description}
        </p>
        
        <div className="flex flex-wrap gap-2">
          {movie.genres.map((genre) => (
            <span 
              key={genre}
              className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-600 rounded-full"
            >
              {genre}
            </span>
          ))}
        </div>
      </div>

      {isHovered && (
        <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center transition-opacity duration-200">
          {isRating ? (
            <Loader className="w-8 h-8 text-white animate-spin" />
          ) : (
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((rating) => (
                <button 
                  key={rating}
                  onClick={() => handleRate(rating)}
                  className="p-2 hover:scale-110 transition-transform duration-150"
                >
                  <Star 
                    className="w-8 h-8 text-yellow-400 fill-current" 
                    data-rating={rating}
                  />
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};