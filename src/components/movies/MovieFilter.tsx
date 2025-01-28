import { useState } from 'react';
import { MovieFilterProps, SortOption } from '../../features/movies/types';
import { MovieSearch } from './MovieSearch';
import { 
  SlidersHorizontal, 
  Calendar, 
  Star, 
  ArrowUpDown,
  X,
  Filter,
  ChevronDown,
  Search,
  ChevronUp
} from 'lucide-react';

// Constants
const sortOptions: { value: SortOption; label: string }[] = [
  { value: 'imdb_rating_desc', label: 'IMDB Rating (High to Low)' },
  { value: 'imdb_rating_asc', label: 'IMDB Rating (Low to High)' },
  { value: 'release_date_desc', label: 'Release Date (Newest)' },
  { value: 'release_date_asc', label: 'Release Date (Oldest)' },
  { value: 'title_asc', label: 'Title (A-Z)' },
  { value: 'title_desc', label: 'Title (Z-A)' },
];

// Subcomponents
interface FilterTagProps {
  label: string;
  onRemove: () => void;
  variant?: 'blue' | 'purple';
}

const FilterTag = ({ label, onRemove, variant = 'blue' }: FilterTagProps) => {
  const baseStyles = 'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium';
  const variantStyles = {
    blue: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    purple: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
  };
  const hoverStyles = {
    blue: 'hover:text-blue-600 dark:hover:text-blue-300',
    purple: 'hover:text-purple-600 dark:hover:text-purple-300'
  };

  return (
    <span className={`${baseStyles} ${variantStyles[variant]}`}>
      {label}
      <button
        onClick={onRemove}
        className={`ml-2 inline-flex items-center justify-center ${hoverStyles[variant]}`}
        aria-label={`Remove ${label} filter`}
      >
        <X className="w-4 h-4" />
      </button>
    </span>
  );
};

interface RangeFilterProps {
  label: string;
  icon: React.ReactNode;
  value: [number, number];
  min: number;
  max: number;
  step?: number;
  onChange: (values: [number, number]) => void;
  showMinMax?: boolean;
}

const RangeFilter = ({ 
  label, 
  icon, 
  value, 
  min, 
  max, 
  step = 1,
  onChange,
  showMinMax
}: RangeFilterProps) => (
  <div className="space-y-2">
    <label className="flex items-center space-x-2 text-sm font-medium text-gray-700 dark:text-gray-300">
      {icon}
      <span>{label}: {value[0]} - {value[1]}</span>
    </label>
    <div className="space-y-4">
      <input
        type="range"
        className="w-full accent-blue-600 dark:accent-blue-400"
        min={min}
        max={max}
        step={step}
        value={value[1]}
        onChange={(e) => onChange([value[0], parseFloat(e.target.value)])}
      />
      <input
        type="range"
        className="w-full accent-blue-600 dark:accent-blue-400"
        min={min}
        max={max}
        step={step}
        value={value[0]}
        onChange={(e) => onChange([parseFloat(e.target.value), value[1]])}
      />
    </div>
    {showMinMax && (
      <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
        <span>Min: {value[0]}</span>
        <span>Max: {value[1]}</span>
      </div>
    )}
  </div>
);

// Main Component
export const MovieFilter = ({ 
  genres, 
  selectedGenres, 
  yearRange,
  ratingRange,
  sortBy,
  onFilterChange,
  minYear,
  maxYear,
  searchQuery,
  searchType,
  onSearchChange,
  onCastCrewSelect,
  selectedCastCrew,
  onMovieSelect,
}: MovieFilterProps) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  const handleRemoveGenre = (genre: string) => {
    onFilterChange('genres', { genre, checked: false });
  };

  const handleRemoveCastCrew = (name: string) => {
    const newSet = new Set(Array.from(selectedCastCrew).filter(item => item !== name));
    onFilterChange('castCrew', newSet);
  };

  const totalActiveFilters = selectedGenres.size + selectedCastCrew.size;

  return (
    <div className="bg-white dark:bg-dark-secondary shadow-sm dark:shadow-gray-800 rounded-lg p-6 space-y-6 mb-8 transition-colors relative">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setIsSearchOpen(prev => !prev)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors"
            aria-label="Toggle search"
          >
            <Search className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
          <div 
            className="flex items-center space-x-2 cursor-pointer"
            onClick={() => setIsExpanded(!isExpanded)}
            role="button"
            tabIndex={0}
            aria-expanded={isExpanded}
          >
            <Filter 
              className={`w-5 h-5 transition-all duration-200 ${
                isExpanded ? 'text-blue-500 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400'
              }`} 
            />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Filters
            </h3>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          {totalActiveFilters > 0 && (
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {totalActiveFilters} active filter{totalActiveFilters !== 1 ? 's' : ''}
            </span>
          )}
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          )}
        </div>
      </div>

      {/* Search Component */}
      <MovieSearch
        searchQuery={searchQuery}
        searchType={searchType}
        onSearchChange={onSearchChange}
        onMovieSelect={onMovieSelect}
        onCastCrewSelect={onCastCrewSelect}
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
      />

      {isExpanded && (
        <>
          {/* Filter Controls Grid */}
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
                  checked: true 
                })}
                value=""
              >
                <option value="" disabled>Select genre</option>
                {genres
                  .filter(genre => !selectedGenres.has(genre))
                  .map((genre) => (
                    <option key={genre} value={genre}>
                      {genre}
                    </option>
                  ))
                }
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
            <RangeFilter
              label="Year Range"
              icon={<Calendar className="w-4 h-4" />}
              value={yearRange}
              min={minYear}
              max={maxYear}
              onChange={(values) => onFilterChange('yearRange', values)}
            />

            {/* Rating Filter */}
            <RangeFilter
              label="IMDB Rating Range"
              icon={<Star className="w-4 h-4" />}
              value={ratingRange}
              min={0}
              max={10}
              step={0.5}
              onChange={(values) => onFilterChange('ratingRange', values)}
              showMinMax
            />
          </div>

          {/* Active Filters Section */}
          {(selectedGenres.size > 0 || selectedCastCrew.size > 0) && (
            <div className="space-y-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              {/* Genre Tags */}
              {selectedGenres.size > 0 && (
                <div className="flex flex-wrap gap-2">
                  {Array.from(selectedGenres).map((genre) => (
                    <FilterTag
                      key={genre}
                      label={genre}
                      onRemove={() => handleRemoveGenre(genre)}
                      variant="blue"
                    />
                  ))}
                </div>
              )}

              {/* Cast/Crew Tags */}
              {selectedCastCrew.size > 0 && (
                <div className="flex flex-wrap gap-2">
                  {Array.from(selectedCastCrew).map((name) => (
                    <FilterTag
                      key={name}
                      label={name}
                      onRemove={() => handleRemoveCastCrew(name)}
                      variant="purple"
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};