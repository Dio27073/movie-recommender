import { useState, useRef, useEffect } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { SortOption, FilterValue, FilterParams } from '../../features/movies/types';
import { useTheme } from '../../features/theme/themeContext';

interface SortFilterProps {
  sortBy: SortOption;
  onSortChange: (type: keyof FilterParams, value: FilterValue) => void;
}

const sortOptions: { value: SortOption; label: string }[] = [
  { value: 'imdb_rating_desc', label: 'Rating (High to Low)' },
  { value: 'imdb_rating_asc', label: 'Rating (Low to High)' },
  { value: 'release_date_desc', label: 'Newest First' },
  { value: 'release_date_asc', label: 'Oldest First' },
  { value: 'title_asc', label: 'Title (A-Z)' },
  { value: 'title_desc', label: 'Title (Z-A)' },
];

const SortFilter = ({ sortBy, onSortChange }: SortFilterProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { theme } = useTheme();

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSort = (value: SortOption) => {
    onSortChange('sort', { type: 'sort', value });
    setIsOpen(false);
  };

  const getButtonText = () => {
    const currentSort = sortOptions.find(option => option.value === sortBy);
    return currentSort ? currentSort.label : 'Sort By';
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`
          w-full px-4 py-2 rounded-lg flex items-center justify-between
          ${theme === 'light' 
            ? 'bg-white hover:bg-gray-50 border border-gray-200' 
            : 'bg-gray-800 hover:bg-gray-700 border border-gray-700'
          }
        `}
      >
        <div className="flex items-center space-x-2">
          <span className={`${theme === 'light' ? 'text-gray-700' : 'text-gray-200'}`}>
            {getButtonText()}
          </span>
        </div>
        {isOpen ? (
          <ChevronUp className={`w-4 h-4 ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`} />
        ) : (
          <ChevronDown className={`w-4 h-4 ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`} />
        )}
      </button>

      {isOpen && (
        <div className={`
          absolute z-50 mt-2 w-64 rounded-lg shadow-lg
          ${theme === 'light' 
            ? 'bg-white border border-gray-200' 
            : 'bg-gray-800 border border-gray-700'
          }
        `}>
          <div className="p-2 space-y-1">
            {sortOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => handleSort(option.value)}
                className={`
                  w-full text-left px-3 py-2 rounded-md text-sm
                  transition-colors duration-200
                  ${sortBy === option.value
                    ? theme === 'light'
                      ? 'bg-blue-50 text-blue-700'
                      : 'bg-blue-900/30 text-blue-300'
                    : theme === 'light'
                      ? 'text-gray-700 hover:bg-gray-100'
                      : 'text-gray-200 hover:bg-gray-700'
                  }
                `}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SortFilter;