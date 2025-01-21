// src/components/movies/MovieFilter.tsx
import React from 'react';
import { MovieFilterProps } from '../../features/movies/types';

export const MovieFilter: React.FC<MovieFilterProps> = ({ 
  genres, 
  selectedGenres, 
  onFilterChange 
}) => {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Filter by Genre</h2>
      <div className="space-y-3">
        {genres.map((genre) => (
          <label key={genre} className="flex items-center space-x-3 text-gray-700">
            <input
              type="checkbox"
              checked={selectedGenres.has(genre)}
              className="form-checkbox h-5 w-5 text-blue-600 rounded border-gray-300"
              onChange={(e) => onFilterChange(genre, e.target.checked)}
            />
            <span className="text-base">{genre}</span>
          </label>
        ))}
      </div>
    </div>
  );
};