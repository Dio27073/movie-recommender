// src/components/movies/MovieFilter.tsx
import React from 'react';
import { MovieFilterProps } from '../../features/movies/types';
import Box from '@mui/material/Box';
import Slider from '@mui/material/Slider';

export const MovieFilter: React.FC<MovieFilterProps> = ({ 
  genres, 
  selectedGenres, 
  yearRange,
  minRating,
  onFilterChange,
  minYear,
  maxYear
}) => {
  const handleYearRangeChange = (_event: Event, newValue: number | number[]) => {
    onFilterChange('yearRange', newValue as [number, number]);
  };

  const handleRatingChange = (_event: Event, newValue: number | number[]) => {
    onFilterChange('minRating', newValue as number);
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 space-y-8">
      {/* Genre Filter */}
      <div>
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Filter by Genre</h2>
        <div className="space-y-3">
          {genres.map((genre) => (
            <label key={genre} className="flex items-center space-x-3 text-gray-700">
              <input
                type="checkbox"
                checked={selectedGenres.has(genre)}
                className="form-checkbox h-5 w-5 text-blue-600 rounded border-gray-300"
                onChange={(e) => onFilterChange('genres', { genre, checked: e.target.checked })}
              />
              <span className="text-base">{genre}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Year Range Slider */}
      <div>
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Release Year</h2>
        <Box className="px-2">
          <Slider
            value={yearRange}
            onChange={handleYearRangeChange}
            valueLabelDisplay="auto"
            min={minYear}
            max={maxYear}
            size="small"
            marks={[
              { value: minYear, label: minYear.toString() },
              { value: maxYear, label: maxYear.toString() }
            ]}
          />
        </Box>
      </div>

      {/* Rating Threshold */}
      <div>
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Minimum Rating</h2>
        <Box className="px-2">
          <Slider
            value={minRating}
            onChange={handleRatingChange}
            valueLabelDisplay="auto"
            min={0}
            max={5}
            step={0.5}
            size="small"
            marks={[
              { value: 0, label: '0' },
              { value: 5, label: '5' }
            ]}
          />
        </Box>
      </div>
    </div>
  );
};