import React, { useState } from 'react';
import { MovieFilterProps, SortOption } from '../../features/movies/types';
import { useTheme } from '../../features/theme/themeContext';
import { 
  SlidersHorizontal, 
  Calendar, 
  Star, 
  ArrowUpDown,
  X,
  Filter,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

const sortOptions: { value: SortOption; label: string }[] = [
  { value: 'release_date_desc', label: 'Release Date (Newest)' },
  { value: 'release_date_asc', label: 'Release Date (Oldest)' },
  { value: 'rating_desc', label: 'Rating (High to Low)' },
  { value: 'rating_asc', label: 'Rating (Low to High)' },
  { value: 'title_asc', label: 'Title (A-Z)' },
  { value: 'title_desc', label: 'Title (Z-A)' },
];

export const MovieFilter = ({ 
  genres, 
  selectedGenres, 
  yearRange,
  minRating,
  sortBy,
  onFilterChange,
  minYear,
  maxYear
}: MovieFilterProps) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const { theme } = useTheme();

  return (
    <div className="bg-white dark:bg-dark-secondary shadow-sm dark:shadow-gray-800 rounded-lg p-6 space-y-6 mb-8 transition-colors">
      {/* Header with total filters count */}
      <div className="flex items-center justify-between cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="flex items-center space-x-2">
          <Filter 
            className={`w-5 h-5 transition-all duration-200 
              ${isExpanded 
                ? 'text-blue-500 dark:text-blue-400 fill-blue-500 dark:fill-blue-400' 
                : 'text-gray-600 dark:text-gray-400 hover:text-blue-500 dark:hover:text-blue-400 hover:fill-blue-500 dark:hover:fill-blue-400'
              }`} 
          />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Filters
          </h3>
        </div>
        <div className="flex items-center space-x-3">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {selectedGenres.size} active filters
          </span>
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          )}
        </div>
      </div>

      {isExpanded && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Genre Selection */}
            <div className="space-y-2">
              <label className="flex items-center space-x-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                <SlidersHorizontal className="w-4 h-4" />
                <span>Genre</span>
              </label>
              <select
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md text-gray-900 dark:text-gray-100"
                onChange={(e) => onFilterChange('genres', { 
                  genre: e.target.value, 
                  checked: !selectedGenres.has(e.target.value) 
                })}
                value=""
              >
                <option value="" disabled>Select genre</option>
                {genres.map((genre) => (
                  <option 
                    key={genre} 
                    value={genre}
                    disabled={selectedGenres.has(genre)}
                  >
                    {genre}
                  </option>
                ))}
              </select>
            </div>

            {/* Sort Selection */}
            <div className="space-y-2">
              <label className="flex items-center space-x-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                <ArrowUpDown className="w-4 h-4" />
                <span>Sort By</span>
              </label>
              <select
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md text-gray-900 dark:text-gray-100"
                value={sortBy}
                onChange={(e) => onFilterChange('sort', e.target.value as SortOption)}
              >
                {sortOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Year Range */}
            <div className="space-y-2">
              <label className="flex items-center space-x-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                <Calendar className="w-4 h-4" />
                <span>Year Range: {yearRange[0]} - {yearRange[1]}</span>
              </label>
              <input
                type="range"
                className="w-full accent-blue-600 dark:accent-blue-400"
                min={minYear}
                max={maxYear}
                value={yearRange[1]}
                onChange={(e) => onFilterChange('yearRange', [yearRange[0], parseInt(e.target.value)])}
              />
              <input
                type="range"
                className="w-full accent-blue-600 dark:accent-blue-400"
                min={minYear}
                max={maxYear}
                value={yearRange[0]}
                onChange={(e) => onFilterChange('yearRange', [parseInt(e.target.value), yearRange[1]])}
              />
            </div>

            {/* Rating Filter */}
            <div className="space-y-2">
              <label className="flex items-center space-x-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                <Star className="w-4 h-4" />
                <span>Min Rating: {minRating}</span>
              </label>
              <input
                type="range"
                className="w-full accent-blue-600 dark:accent-blue-400"
                min={0}
                max={5}
                step={0.5}
                value={minRating}
                onChange={(e) => onFilterChange('minRating', parseFloat(e.target.value))}
              />
            </div>
          </div>

          {/* Selected Genres Tags */}
          {selectedGenres.size > 0 && (
            <div className="flex flex-wrap gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
              {Array.from(selectedGenres).map((genre) => (
                <span
                  key={genre}
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                >
                  {genre}
                  <button
                    onClick={() => onFilterChange('genres', { genre, checked: false })}
                    className="ml-2 inline-flex items-center justify-center hover:text-blue-600 dark:hover:text-blue-300"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
};