import { useState } from 'react';
import { useTheme } from '../../features/theme/themeContext';
import { MovieFilterProps } from '../../features/movies/types';
import { MovieSearch } from './MovieSearch';
import GenreFilter from './GenreFilter';
import SortFilter from './SortFilter';
import RangeFilter from './RangeFilter';
import { ContentRatingFilter, MoodFilter, StreamingFilter } from './NewFilters';
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
  variant?: 'blue' | 'purple' | 'green' | 'orange' | 'red';
}

const FilterTag = ({ label, onRemove, variant = 'blue' }: FilterTagProps) => {
  const baseStyles = 'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium transition-colors duration-200';
  const variantStyles = {
    blue: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    purple: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
    green: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    orange: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
    red: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
  };
  const hoverStyles = {
    blue: 'hover:text-blue-600 dark:hover:text-blue-300',
    purple: 'hover:text-purple-600 dark:hover:text-purple-300',
    green: 'hover:text-green-600 dark:hover:text-green-300',
    orange: 'hover:text-orange-600 dark:hover:text-orange-300',
    red: 'hover:text-red-600 dark:hover:text-red-300'
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
  selectedContentRatings = new Set(),
  selectedMoods = new Set(),
  selectedPlatforms = new Set(),
}: MovieFilterProps) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const { theme } = useTheme();

  const handleRemoveGenre = (genre: string) => {
    onFilterChange('genre', { type: 'genre', genre, checked: false });
  };

  const handleRemoveCastCrew = (name: string) => {
    const newSet = new Set(Array.from(selectedCastCrew).filter(item => item !== name));
    onFilterChange('castCrew', { type: 'castCrew', value: newSet });
  };

  const handleRemoveContentRating = (rating: string) => {
    const newSet = new Set(Array.from(selectedContentRatings).filter(item => item !== rating));
    onFilterChange('contentRating', { type: 'contentRating', value: newSet });
  };

  const handleRemoveMood = (mood: string) => {
    const newSet = new Set(Array.from(selectedMoods).filter(item => item !== mood));
    onFilterChange('moodTags', { type: 'moodTags', value: newSet });
  };

  const handleRemovePlatform = (platform: string) => {
    const newSet = new Set(Array.from(selectedPlatforms).filter(item => item !== platform));
    onFilterChange('streamingPlatforms', { type: 'streamingPlatforms', value: newSet });
  };

  const totalActiveFilters = 
    selectedGenres.size + 
    selectedCastCrew.size + 
    selectedContentRatings.size + 
    selectedMoods.size + 
    selectedPlatforms.size;

  return (
    <div className={`
      transition-colors duration-200 
      ${theme === 'light' 
        ? 'bg-light-secondary border border-gray-200 shadow-lg' 
        : 'bg-dark-secondary border border-gray-950 shadow-lg'
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
                ? 'hover:bg-gray-100 text-light-text'
                : 'hover:bg-gray-950 text-dark-text'
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
                  : theme === 'light' ? 'text-light-text' : 'text-dark-text'
                }
              `} 
            />
            <h3 className={`
              text-lg font-semibold transition-colors duration-200
              ${theme === 'light' ? 'text-light-text' : 'text-dark-text'}
            `}>
              Filters
            </h3>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          {totalActiveFilters > 0 && (
            <span className={`
              text-sm transition-colors duration-200
              ${theme === 'light' ? 'text-light-text' : 'text-dark-text'}
            `}>
              {totalActiveFilters} active filter{totalActiveFilters !== 1 ? 's' : ''}
            </span>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className={`
              p-1 rounded-full transition-colors duration-200
              ${theme === 'light' 
                ? 'hover:bg-gray-100' 
                : 'hover:bg-gray-950'
              }
            `}
            aria-label={isExpanded ? "Collapse filters" : "Expand filters"}
          >
            {isExpanded ? (
              <ChevronUp className={`
                w-5 h-5 transition-colors duration-200
                ${theme === 'light' ? 'text-gray-600' : 'text-gray-300'}
              `} />
            ) : (
              <ChevronDown className={`
                w-5 h-5 transition-colors duration-200
                ${theme === 'light' ? 'text-gray-600' : 'text-gray-300'}
              `} />
            )}
          </button>
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
            <div className="z-50">
              <GenreFilter
                selectedGenres={selectedGenres}
                onFilterChange={onFilterChange}
              />
            </div>

            <div className="z-40">
              <SortFilter
                sortBy={sortBy}
                onSortChange={(type, value) => onFilterChange(type, value)}
              />
            </div>

            <div className="z-30">
              <ContentRatingFilter
                selectedRatings={selectedContentRatings}
                onChange={(value) => onFilterChange('contentRating', { type: 'contentRating', value })}
              />
            </div>

            <div className="z-20">
              <StreamingFilter
                selectedPlatforms={selectedPlatforms}
                onChange={(value) => onFilterChange('streamingPlatforms', { type: 'streamingPlatforms', value })}
              />
            </div>

            <div className="z-10">
              <MoodFilter
                selectedMoods={selectedMoods}
                onChange={(value) => onFilterChange('moodTags', { type: 'moodTags', value })}
              />
            </div>

            <RangeFilter
              label="Year Range"
              icon={<Calendar className="w-4 h-4" />}
              value={yearRange}
              min={minYear}
              max={maxYear}
              onChange={(values) => onFilterChange('yearRange', { type: 'yearRange', value: values })}
            />

            <RangeFilter
              label="IMDB Rating"
              icon={<Star className="w-4 h-4" />}
              value={ratingRange}
              min={0}
              max={10}
              step={0.1}
              onChange={(values) => onFilterChange('ratingRange', { type: 'ratingRange', value: values })}
              showMinMax
            />
          </div>

          {/* Active Filters Section */}
          {totalActiveFilters > 0 && (
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
                {Array.from(selectedContentRatings).map((rating) => (
                  <FilterTag
                    key={rating}
                    label={rating}
                    onRemove={() => handleRemoveContentRating(rating)}
                    variant="red"
                  />
                ))}
                {Array.from(selectedMoods).map((mood) => (
                  <FilterTag
                    key={mood}
                    label={mood}
                    onRemove={() => handleRemoveMood(mood)}
                    variant="orange"
                  />
                ))}
                {Array.from(selectedPlatforms).map((platform) => (
                  <FilterTag
                    key={platform}
                    label={platform}
                    onRemove={() => handleRemovePlatform(platform)}
                    variant="green"
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