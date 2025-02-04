import { useState } from 'react';
import { useTheme } from '../../features/theme/themeContext';
import { MovieFilterProps } from '../../features/movies/types';
import { MovieSearch } from './MovieSearch';
import GenreFilter from './GenreFilter';
import SortFilter from './SortFilter';
import RangeFilter from './RangeFilter';
import { 
  Calendar, 
  Star, 
  X,
  Filter,
  ChevronDown,
  Search,
  ChevronUp
} from 'lucide-react';

interface FilterTagProps {
  label: string;
  onRemove: () => void;
  variant?: 'blue' | 'purple';
}

const FilterTag = ({ label, onRemove, variant = 'blue' }: FilterTagProps) => {
  const baseStyles = 'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium transition-colors duration-200';
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

export const MovieFilter = ({ 
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
  const { theme } = useTheme();

  const handleRemoveGenre = (genre: string) => {
    onFilterChange('genres', { genre, checked: false });
  };

  const handleRemoveCastCrew = (name: string) => {
    const newSet = new Set(Array.from(selectedCastCrew).filter(item => item !== name));
    onFilterChange('castCrew', newSet);
  };

  const totalActiveFilters = selectedGenres.size + selectedCastCrew.size;

  return (
    <div className={`
      transition-colors duration-200 
      ${theme === 'light' 
        ? 'bg-white/90 shadow-lg' 
        : 'bg-gray-800/50 backdrop-blur-sm'
      } 
      rounded-lg p-6 space-y-6 mb-8
    `}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setIsSearchOpen(prev => !prev)}
            className={`
              p-2 rounded-full transition-colors duration-200
              ${theme === 'light'
                ? 'hover:bg-gray-100 text-gray-600'
                : 'hover:bg-gray-700/50 text-gray-400'
              }
            `}
            aria-label="Toggle search"
          >
            <Search className="w-5 h-5" />
          </button>
          <div 
            className="flex items-center space-x-2 cursor-pointer"
            onClick={() => setIsExpanded(!isExpanded)}
            role="button"
            tabIndex={0}
            aria-expanded={isExpanded}
          >
            <Filter 
              className={`
                w-5 h-5 transition-all duration-200
                ${isExpanded 
                  ? 'text-blue-500' 
                  : theme === 'light' ? 'text-gray-600' : 'text-gray-400'
                }
              `} 
            />
            <h3 className={`
              text-lg font-semibold transition-colors duration-200
              ${theme === 'light' ? 'text-gray-800' : 'text-gray-200'}
            `}>
              Filters
            </h3>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          {totalActiveFilters > 0 && (
            <span className={`
              text-sm transition-colors duration-200
              ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}
            `}>
              {totalActiveFilters} active filter{totalActiveFilters !== 1 ? 's' : ''}
            </span>
          )}
          {isExpanded ? (
            <ChevronUp className={`
              w-5 h-5 transition-colors duration-200
              ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}
            `} />
          ) : (
            <ChevronDown className={`
              w-5 h-5 transition-colors duration-200
              ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}
            `} />
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 relative">
            <div className="z-40">
              <GenreFilter
                selectedGenres={selectedGenres}
                onFilterChange={onFilterChange}
              />
            </div>

            <div className="z-40">
              <SortFilter
                sortBy={sortBy}
                onSortChange={(value) => onFilterChange('sort', value)}
              />
            </div>

            <RangeFilter
              label="Year Range"
              icon={<Calendar className="w-4 h-4" />}
              value={yearRange}
              min={minYear}
              max={maxYear}
              onChange={(values) => onFilterChange('yearRange', values)}
            />

            <RangeFilter
              label="IMDB Rating"
              icon={<Star className="w-4 h-4" />}
              value={ratingRange}
              min={0}
              max={10}
              step={0.1}
              onChange={(values) => onFilterChange('ratingRange', values)}
              showMinMax
            />
          </div>

          {/* Active Filters Section */}
          {(selectedGenres.size > 0 || selectedCastCrew.size > 0) && (
            <div className={`
              space-y-4 pt-4 border-t transition-colors duration-200
              ${theme === 'light' ? 'border-gray-200' : 'border-gray-700'}
            `}>
              <div className="flex flex-wrap gap-2">
                {Array.from(selectedGenres).map((genre) => (
                  <FilterTag
                    key={genre}
                    label={genre}
                    onRemove={() => handleRemoveGenre(genre)}
                    variant="blue"
                  />
                ))}
                {Array.from(selectedCastCrew).map((name) => (
                  <FilterTag
                    key={name}
                    label={name}
                    onRemove={() => handleRemoveCastCrew(name)}
                    variant="purple"
                  />
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};